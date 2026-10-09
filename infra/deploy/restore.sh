#!/usr/bin/env bash
# =============================================================================
# restore.sh — restore a Wikimedica backup set (database and/or uploads)
# =============================================================================
# "Restore matters more than backup": this script is written so that a restore under
# stress cannot make things worse.
#
#   * refuses to run without --yes-overwrite (it REPLACES the live database/uploads)
#   * verifies the SHA-256 checksums of the set before touching anything
#   * first takes a safety dump of the CURRENT database (prerestore_*), so the restore
#     itself can be undone
#   * stops the application during the restore, so no edit lands in a half-restored database
#   * afterwards runs update.php (schema of an older dump vs. newer code) and the health check
#
# Usage:
#   restore.sh --prefix wikimedica_20261009_020000 --yes-overwrite [--db-only|--images-only]
#              [--from DIR] [--no-pre-backup]
#   restore.sh --list [--from DIR]
#
# Staging vs. production:  DEPLOY_ENV=staging restore.sh ...   (monthly restore test)
# Encrypted sets (.gpg) need the private GPG key on this machine.
# =============================================================================
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=infra/deploy/lib.sh
source "${SCRIPT_DIR}/lib.sh"
LOG_PREFIX="RESTORE "

PREFIX=""
FROM="${BACKUP_LOCAL_DIR}"
DO_DB=1
DO_IMG=1
CONFIRMED=0
PRE_BACKUP=1
LIST=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --prefix)         PREFIX="${2:-}"; shift 2 ;;
    --from)           FROM="${2:-}"; shift 2 ;;
    --db-only)        DO_IMG=0; shift ;;
    --images-only)    DO_DB=0; shift ;;
    --yes-overwrite)  CONFIRMED=1; shift ;;
    --no-pre-backup)  PRE_BACKUP=0; shift ;;
    --list)           LIST=1; shift ;;
    -h|--help)        sed -n '2,26p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

if [ "${LIST}" = "1" ]; then
  echo "Complete backup sets in ${FROM} (newest first):"
  find "${FROM}" -maxdepth 1 -type f -printf '%f\n' 2>/dev/null | sed -n "s/^\(${BACKUP_NAME}_[0-9]\{8\}_[0-9]\{6\}\)\.manifest\.json$/  \1/p" | sort -r
  exit 0
fi

[[ "${PREFIX}" =~ ^[a-z0-9-]+_[0-9]{8}_[0-9]{6}$ ]] || die "--prefix is required, e.g. ${BACKUP_NAME}_20261009_020000 (see --list)"
[ "${CONFIRMED}" = "1" ] || die "this REPLACES the live data of '${DEPLOY_ENV}'. Re-run with --yes-overwrite if that is what you want."
[ -f "${FROM}/${PREFIX}.manifest.json" ] || die "set ${PREFIX} is not complete (no manifest) in ${FROM}"
assert_env_keys MEDIAWIKI_DB_NAME MEDIAWIKI_DB_ROOT_PASSWORD

DB_NAME="$(env_get MEDIAWIKI_DB_NAME)"
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT
umask 077

log "=== Restore of ${PREFIX} into '${DEPLOY_ENV}' ==="

# ---------------------------------------------------------------------------
# 1. Verify before touching anything
# ---------------------------------------------------------------------------
log "Verifying checksums..."
( cd "${FROM}" && sha256sum -c --quiet "${PREFIX}.sha256" ) || die "checksum verification FAILED — the backup is damaged; nothing was changed"

find_file() {  # find_file SUFFIX -> prints the path (plain or .gpg) or nothing
  local base="${FROM}/${PREFIX}$1"
  if [ -f "${base}" ]; then echo "${base}"; elif [ -f "${base}.gpg" ]; then echo "${base}.gpg"; fi
}

plain_copy() {  # plain_copy FILE -> prints path of a readable (decrypted if needed) file
  local f="$1"
  case "${f}" in
    *.gpg)
      command -v gpg >/dev/null 2>&1 || die "$(basename "${f}") is encrypted but gpg is not installed"
      local out
      out="${WORK}/$(basename "${f%.gpg}")"
      gpg --batch --yes --quiet --output "${out}" --decrypt "${f}" || die "decryption failed (is the private key available?)"
      echo "${out}" ;;
    *) echo "${f}" ;;
  esac
}

DB_SRC=""
IMG_SRC=""
if [ "${DO_DB}" = "1" ]; then
  DB_SRC="$(plain_copy "$(find_file _db.sql.gz)")"
  [ -f "${DB_SRC}" ] || die "no database dump in set ${PREFIX}"
  gzip -t "${DB_SRC}" || die "database dump is not a valid gzip file"
fi
if [ "${DO_IMG}" = "1" ]; then
  IMG_SRC="$(plain_copy "$(find_file _images.tar.gz)")"
  [ -f "${IMG_SRC}" ] || die "no uploads archive in set ${PREFIX}"
  tar tzf "${IMG_SRC}" >/dev/null || die "uploads archive is not a valid tar.gz file"
fi

# ---------------------------------------------------------------------------
# 2. Safety dump of the current state
# ---------------------------------------------------------------------------
SAFETY=""
if [ "${DO_DB}" = "1" ] && [ "${PRE_BACKUP}" = "1" ]; then
  mkdir -p "${BACKUP_LOCAL_DIR}"
  SAFETY="${BACKUP_LOCAL_DIR}/prerestore_$(date -u '+%Y%m%d_%H%M%S')_${DEPLOY_ENV}_db.sql.gz"
  log "Safety dump of the current database -> ${SAFETY}"
  if MYSQL_PWD="$(env_get MEDIAWIKI_DB_ROOT_PASSWORD)" docker exec -e MYSQL_PWD "${DB_CONTAINER}" \
       mysqldump --user=root --single-transaction --default-character-set=binary "${DB_NAME}" \
       | gzip -9 > "${SAFETY}" && gzip -t "${SAFETY}"; then
    log "Safety dump written."
  else
    rm -f "${SAFETY}"
    die "could not create the safety dump; refusing to overwrite the database (use --no-pre-backup to skip, if the database is empty/broken)"
  fi
fi

# ---------------------------------------------------------------------------
# 3. Restore
# ---------------------------------------------------------------------------
APP_WAS_RUNNING=0
if [ "$(docker inspect -f '{{.State.Running}}' "${APP_CONTAINER}" 2>/dev/null || echo false)" = "true" ]; then
  APP_WAS_RUNNING=1
  log "Stopping ${APP_CONTAINER} (no writes during the restore)..."
  docker stop "${APP_CONTAINER}" >/dev/null
fi

restart_app() {
  if [ "${APP_WAS_RUNNING}" = "1" ]; then docker start "${APP_CONTAINER}" >/dev/null || true; fi
}
trap 'restart_app; rm -rf "${WORK}"' ERR

if [ "${DO_DB}" = "1" ]; then
  log "Importing the database dump..."
  gzip -dc "${DB_SRC}" \
    | MYSQL_PWD="$(env_get MEDIAWIKI_DB_ROOT_PASSWORD)" docker exec -i -e MYSQL_PWD "${DB_CONTAINER}" \
        mysql --user=root --default-character-set=binary "${DB_NAME}"
  log "Database restored."
fi

if [ "${DO_IMG}" = "1" ]; then
  log "Restoring the uploads volume ${IMAGES_VOLUME}..."
  APP_IMAGE="$(docker inspect -f '{{.Config.Image}}' "${APP_CONTAINER}")"
  docker run --rm -i -v "${IMAGES_VOLUME}:/volume" --entrypoint sh "${APP_IMAGE}" \
    -c 'find /volume -mindepth 1 -delete && tar xzpf - -C /volume' < "${IMG_SRC}"
  log "Uploads restored."
fi

# ---------------------------------------------------------------------------
# 4. Bring the application back and verify
# ---------------------------------------------------------------------------
trap 'rm -rf "${WORK}"' EXIT
if [ "${APP_WAS_RUNNING}" = "1" ]; then
  log "Starting ${APP_CONTAINER}..."
  docker start "${APP_CONTAINER}" >/dev/null
  if [ "${DO_DB}" = "1" ]; then
    log "Running update.php (an older dump may need the schema of the current version)..."
    docker exec "${APP_CONTAINER}" php maintenance/run.php update --quick >/dev/null
  fi
  log "Health check..."
  "${SCRIPT_DIR}/healthcheck.sh" --only core --wait 120
fi

if [ "${DO_DB}" = "1" ]; then
  pages="$(MYSQL_PWD="$(env_get MEDIAWIKI_DB_ROOT_PASSWORD)" docker exec -e MYSQL_PWD "${DB_CONTAINER}" \
    mysql --user=root --batch --skip-column-names "${DB_NAME}" -e 'SELECT COUNT(*) FROM page' 2>/dev/null || echo '?')"
  log "Pages in the restored database: ${pages}"
fi
log "=== Restore of ${PREFIX} complete ==="
if [ -n "${SAFETY}" ]; then
  log "To undo this restore: restore from ${SAFETY} (gunzip -c it into the database)."
fi
