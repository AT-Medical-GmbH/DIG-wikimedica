#!/usr/bin/env bash
# =============================================================================
# backup.sh — Wikimedica backup: database + uploads + configuration
# =============================================================================
# Creates one verified backup SET   <name>_YYYYmmdd_HHMMSS_*   in BACKUP_LOCAL_DIR:
#
#   _db.sql.gz       full MariaDB dump (binary charset, single transaction)
#   _images.tar.gz   the uploads volume
#   _config.tar.gz   LocalSettings.php with secret-looking values redacted + deployed-version
#   .sha256          checksums of the files above (as stored, i.e. after encryption)
#   .manifest.json   written LAST: its presence marks the set as complete
#
# then (optionally) uploads it and rotates old sets (7 daily / 4 weekly / 3 monthly).
# State for monitoring: BACKUP_LOCAL_DIR/last-backup.json
#
# The .env file is NOT part of the backup (it holds every secret). Keep the secrets in
# the password manager / GitHub secrets; restoring needs them (docs/operations/backup-restore-runbook.md).
#
# Usage:
#   backup.sh [--no-upload] [--no-rotate]
#
# Environment (all optional; see infra/env/.env.example):
#   BACKUP_GPG_RECIPIENT              encrypt every file for this GPG key (recommended)
#   BACKUP_ALLOW_UNENCRYPTED_UPLOAD   =1 to allow offsite upload without encryption
#   BACKUP_S3_ENDPOINT / _BUCKET / _ACCESS_KEY / _SECRET_KEY    S3-compatible target
#   BACKUP_SFTP_HOST / _USER / _PATH                            SFTP (rsync over ssh) target
#   BACKUP_RETAIN_DAYS / _WEEKS / _MONTHS                       default 7 / 4 / 3
#
# Exit code: 0 ok · 1 backup failed · 3 local backup ok but the offsite upload failed
# =============================================================================
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=infra/deploy/lib.sh
source "${SCRIPT_DIR}/lib.sh"
LOG_PREFIX="BACKUP "

DO_UPLOAD=1
DO_ROTATE=1
while [ "$#" -gt 0 ]; do
  case "$1" in
    --no-upload) DO_UPLOAD=0; shift ;;
    --no-rotate) DO_ROTATE=0; shift ;;
    -h|--help)   sed -n '2,32p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

assert_env_keys MEDIAWIKI_DB_NAME MEDIAWIKI_DB_ROOT_PASSWORD

umask 077
mkdir -p "${BACKUP_LOCAL_DIR}"
chmod 700 "${BACKUP_LOCAL_DIR}"

STARTED_AT="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
STAMP="$(date -u '+%Y%m%d_%H%M%S')"
PREFIX="${BACKUP_NAME}_${STAMP}"
DB_NAME="$(env_get MEDIAWIKI_DB_NAME)"
GPG_RECIPIENT="$(env_opt BACKUP_GPG_RECIPIENT)"
SUFFIX=""
ENCRYPTED="false"
if [ -n "${GPG_RECIPIENT}" ]; then SUFFIX=".gpg"; ENCRYPTED="true"; fi

DB_FILE="${BACKUP_LOCAL_DIR}/${PREFIX}_db.sql.gz${SUFFIX}"
IMG_FILE="${BACKUP_LOCAL_DIR}/${PREFIX}_images.tar.gz${SUFFIX}"
CFG_FILE="${BACKUP_LOCAL_DIR}/${PREFIX}_config.tar.gz${SUFFIX}"
SUM_FILE="${BACKUP_LOCAL_DIR}/${PREFIX}.sha256"
MANIFEST="${BACKUP_LOCAL_DIR}/${PREFIX}.manifest.json"
STATUS_FILE="${BACKUP_LOCAL_DIR}/last-backup.json"
OFFSITE="skipped"

write_status() {  # write_status STATUS DETAIL
  local tmp="${STATUS_FILE}.tmp" detail
  # shellcheck disable=SC1003  # tr -d deletes the characters " and \ so that the detail stays valid JSON
  detail="$(printf '%s' "$2" | tr -d '"\\' | tr '\n' ' ')"
  printf '{"status":"%s","environment":"%s","prefix":"%s","started_at":"%s","finished_at":"%s","offsite":"%s","detail":"%s"}\n' \
    "$1" "${DEPLOY_ENV}" "${PREFIX}" "${STARTED_AT}" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "${OFFSITE}" "${detail}" > "${tmp}"
  mv "${tmp}" "${STATUS_FILE}"
}

cleanup_partial() {
  rm -f "${BACKUP_LOCAL_DIR}/${PREFIX}"_* "${BACKUP_LOCAL_DIR}/${PREFIX}".sha256 "${BACKUP_LOCAL_DIR}/${PREFIX}".manifest.json 2>/dev/null || true
}

FAIL_MSG=""
on_error() {
  local rc=$? line="${BASH_LINENO[0]}"
  trap - ERR
  log "FAILED (exit ${rc}) — removing the partial backup set"
  cleanup_partial
  write_status failed "${FAIL_MSG:-backup failed at line ${line}}"
  notify_failure "backup ${PREFIX} failed: ${FAIL_MSG:-see the server log}"
  exit 1
}
trap on_error ERR

# fail MESSAGE — like die, but also cleans up, records the failure and alerts (die would skip all that).
fail() {
  log "ERROR: $*"
  FAIL_MSG="$*"
  on_error
}

# encrypt_in_place FILE — replaces FILE by FILE.gpg when encryption is configured.
# (Dump and archive are written plain first, then encrypted; the plain file never leaves this directory.)
maybe_encrypt() {
  local plain="$1"
  if [ -z "${GPG_RECIPIENT}" ]; then return 0; fi
  command -v gpg >/dev/null 2>&1 || fail "BACKUP_GPG_RECIPIENT is set but gpg is not installed"
  gpg --batch --yes --quiet --trust-model always --recipient "${GPG_RECIPIENT}" \
      --output "${plain}.gpg" --encrypt "${plain}"
  rm -f "${plain}"
}

# ---------------------------------------------------------------------------
# 1. Database
# ---------------------------------------------------------------------------
log "Dumping database '${DB_NAME}' from ${DB_CONTAINER}..."
PLAIN_DB="${DB_FILE%.gpg}"
# The password travels in the environment of the docker client (-e MYSQL_PWD), never on a command line.
MYSQL_PWD="$(env_get MEDIAWIKI_DB_ROOT_PASSWORD)" docker exec -e MYSQL_PWD "${DB_CONTAINER}" \
  mysqldump --user=root --single-transaction --routines --triggers --add-drop-table \
            --default-character-set=binary "${DB_NAME}" \
  | gzip -9 > "${PLAIN_DB}"

# A dump that stops half-way still looks like a file. Prove it is complete.
gzip -t "${PLAIN_DB}"
if ! gzip -dc "${PLAIN_DB}" | tail -n 5 | grep -q -- '-- Dump completed'; then
  fail "the database dump is incomplete (no 'Dump completed' trailer)"
fi
maybe_encrypt "${PLAIN_DB}"
log "Database dump verified: $(du -h "${DB_FILE}" | cut -f1)"

# ---------------------------------------------------------------------------
# 2. Uploads (images volume)
# ---------------------------------------------------------------------------
log "Archiving uploads from ${APP_CONTAINER}:/var/www/html/images ..."
PLAIN_IMG="${IMG_FILE%.gpg}"
docker exec "${APP_CONTAINER}" tar czf - -C /var/www/html/images . > "${PLAIN_IMG}"
tar tzf "${PLAIN_IMG}" >/dev/null
maybe_encrypt "${PLAIN_IMG}"
log "Uploads archive verified: $(du -h "${IMG_FILE}" | cut -f1)"

# ---------------------------------------------------------------------------
# 3. Configuration (without secrets)
# ---------------------------------------------------------------------------
log "Archiving configuration (secrets redacted)..."
PLAIN_CFG="${CFG_FILE%.gpg}"
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT
LS_SRC="${DEPLOY_DIR}/infra/mediawiki/LocalSettings.php"
if [ -f "${LS_SRC}" ]; then
  # Redact assignments of secret-looking settings and any quoted literal that follows a secret-looking key.
  # shellcheck disable=SC2016  # the $ in the sed pattern is literal (PHP variable names), not shell expansion
  sed -E \
    -e 's/(\$wg(SecretKey|UpgradeKey|DBpassword|ReCaptchaSecretKey|HCaptchaSecretKey)[[:space:]]*=[[:space:]]*).*/\1"<redacted>";/' \
    -e "s/((password|passwd|secret|token|api[_-]?key)[A-Za-z_'\"]*[[:space:]]*(=>|=)[[:space:]]*)['\"][^'\"]+['\"]/\\1'<redacted>'/Ig" \
    "${LS_SRC}" > "${WORK}/LocalSettings.redacted.php"
fi
if [ -f "${DEPLOY_DIR}/deployed-version" ]; then cp "${DEPLOY_DIR}/deployed-version" "${WORK}/"; fi
printf 'environment=%s\nbackup=%s\n' "${DEPLOY_ENV}" "${PREFIX}" > "${WORK}/backup-info.txt"
tar czf "${PLAIN_CFG}" -C "${WORK}" .
maybe_encrypt "${PLAIN_CFG}"

# ---------------------------------------------------------------------------
# 4. Checksums and manifest (the manifest is written last = "set is complete")
# ---------------------------------------------------------------------------
( cd "${BACKUP_LOCAL_DIR}" && sha256sum "$(basename "${DB_FILE}")" "$(basename "${IMG_FILE}")" "$(basename "${CFG_FILE}")" ) > "${SUM_FILE}"
( cd "${BACKUP_LOCAL_DIR}" && sha256sum -c --quiet "$(basename "${SUM_FILE}")" )

{
  printf '{"prefix":"%s","environment":"%s","created_at":"%s","encrypted":%s,"files":[' \
    "${PREFIX}" "${DEPLOY_ENV}" "${STARTED_AT}" "${ENCRYPTED}"
  first=1
  for f in "${DB_FILE}" "${IMG_FILE}" "${CFG_FILE}"; do
    if [ "${first}" = "0" ]; then printf ','; fi
    first=0
    printf '{"name":"%s","bytes":%s}' "$(basename "${f}")" "$(stat -c %s "${f}")"
  done
  printf ']}\n'
} > "${MANIFEST}"
log "Backup set complete: ${PREFIX}"

# ---------------------------------------------------------------------------
# 5. Offsite upload
# ---------------------------------------------------------------------------
UPLOAD_FILES=("${DB_FILE}" "${IMG_FILE}" "${CFG_FILE}" "${SUM_FILE}" "${MANIFEST}")
upload_failed=0

upload_s3() {
  local endpoint bucket key secret f
  endpoint="$(env_opt BACKUP_S3_ENDPOINT)"; bucket="$(env_opt BACKUP_S3_BUCKET)"
  key="$(env_opt BACKUP_S3_ACCESS_KEY)";    secret="$(env_opt BACKUP_S3_SECRET_KEY)"
  if [ -z "${endpoint}" ] || [ -z "${bucket}" ]; then return 2; fi
  if ! command -v aws >/dev/null 2>&1; then log "WARNING: aws CLI not installed; S3 upload skipped"; return 2; fi
  for f in "${UPLOAD_FILES[@]}"; do
    AWS_ACCESS_KEY_ID="${key}" AWS_SECRET_ACCESS_KEY="${secret}" \
      aws s3 cp --only-show-errors --endpoint-url "${endpoint}" "${f}" "s3://${bucket}/${BACKUP_NAME}/$(basename "${f}")" || return 1
  done
}

upload_sftp() {
  local host user path f
  host="$(env_opt BACKUP_SFTP_HOST)"; user="$(env_opt BACKUP_SFTP_USER)"
  path="$(env_opt BACKUP_SFTP_PATH)"; path="${path:-/backups/wikimedica}"
  if [ -z "${host}" ] || [ -z "${user}" ]; then return 2; fi
  if ! command -v rsync >/dev/null 2>&1; then log "WARNING: rsync not installed; SFTP upload skipped"; return 2; fi
  for f in "${UPLOAD_FILES[@]}"; do
    rsync -a --no-perms -e "ssh -o BatchMode=yes" "${f}" "${user}@${host}:${path}/${BACKUP_NAME}/" || return 1
  done
}

if [ "${DO_UPLOAD}" = "1" ]; then
  configured=0
  if [ -n "$(env_opt BACKUP_S3_BUCKET)" ] || [ -n "$(env_opt BACKUP_SFTP_HOST)" ]; then configured=1; fi
  if [ "${configured}" = "1" ] && [ -z "${GPG_RECIPIENT}" ] && [ "$(env_opt BACKUP_ALLOW_UNENCRYPTED_UPLOAD)" != "1" ]; then
    log "ERROR: offsite upload is configured but backups are not encrypted. Set BACKUP_GPG_RECIPIENT"
    log "       (or BACKUP_ALLOW_UNENCRYPTED_UPLOAD=1 if you accept that DB dumps leave the server in clear text)."
    OFFSITE="refused-unencrypted"
    upload_failed=1
  elif [ "${configured}" = "1" ]; then
    OFFSITE="ok"
    for target in s3 sftp; do
      rc=0
      "upload_${target}" || rc=$?
      if [ "${rc}" = "1" ]; then
        log "ERROR: upload to ${target} failed"
        OFFSITE="failed"
        upload_failed=1
      elif [ "${rc}" = "0" ]; then
        log "Uploaded to ${target}"
      fi
    done
  else
    log "No offsite target configured (BACKUP_S3_* / BACKUP_SFTP_*): backup stays on this server only"
  fi
fi

# ---------------------------------------------------------------------------
# 6. Rotation (only local sets; remote retention belongs to the target, e.g. an S3 lifecycle rule)
# ---------------------------------------------------------------------------
if [ "${DO_ROTATE}" = "1" ]; then
  keep_days="$(env_opt BACKUP_RETAIN_DAYS)"; keep_weeks="$(env_opt BACKUP_RETAIN_WEEKS)"; keep_months="$(env_opt BACKUP_RETAIN_MONTHS)"
  python3 "${SCRIPT_DIR}/rotate-backups.py" --dir "${BACKUP_LOCAL_DIR}" --name "${BACKUP_NAME}" \
    --daily "${keep_days:-7}" --weekly "${keep_weeks:-4}" --monthly "${keep_months:-3}" 2>&1 | sed 's/^/  /' \
    || log "WARNING: rotation failed"
fi

trap - ERR
if [ "${upload_failed}" = "1" ]; then
  write_status ok "local backup ok, offsite upload ${OFFSITE}"
  notify_failure "backup ${PREFIX}: local backup ok but offsite upload ${OFFSITE}"
  exit 3
fi
write_status ok "backup complete"
log "=== Backup complete: ${PREFIX} ==="
