#!/usr/bin/env bash
# =============================================================================
# restore-test.sh — monthly restore test (runs on STAGING only)
# =============================================================================
# A backup that was never restored is only a hope. Once a month, restore the newest
# production backup into the staging stack and prove that the wiki comes up with content.
#
#   DEPLOY_ENV=staging infra/deploy/restore-test.sh --from /path/to/production/backups [--prefix SET]
#
# Production backups must be copied to the staging host first (scp/rsync from the offsite
# target). The script REFUSES to run against production.
# Result: BACKUP_LOCAL_DIR/last-restore-test.json  (status, set, pages, timestamp)
# =============================================================================
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export DEPLOY_ENV="${DEPLOY_ENV:-staging}"
# shellcheck source=infra/deploy/lib.sh
source "${SCRIPT_DIR}/lib.sh"
LOG_PREFIX="RESTORE-TEST "

[ "${DEPLOY_ENV}" = "staging" ] || die "the restore test only runs on staging (DEPLOY_ENV=${DEPLOY_ENV})"

FROM=""
PREFIX=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --from)   FROM="${2:-}"; shift 2 ;;
    --prefix) PREFIX="${2:-}"; shift 2 ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done
[ -n "${FROM}" ] && [ -d "${FROM}" ] || die "--from DIR (directory with production backup sets) is required"

if [ -z "${PREFIX}" ]; then
  PREFIX="$(find "${FROM}" -maxdepth 1 -type f -printf '%f\n' | sed -n 's/^\(wikimedica_[0-9]\{8\}_[0-9]\{6\}\)\.manifest\.json$/\1/p' | sort | tail -n 1)"
  [ -n "${PREFIX}" ] || die "no complete production backup set found in ${FROM}"
fi
log "Restoring ${PREFIX} into the staging stack..."

RESULT="${BACKUP_LOCAL_DIR}/last-restore-test.json"
mkdir -p "${BACKUP_LOCAL_DIR}"
write_result() {  # write_result STATUS PAGES
  printf '{"status":"%s","set":"%s","pages":"%s","tested_at":"%s"}\n' \
    "$1" "${PREFIX}" "$2" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" > "${RESULT}"
}

if ! "${SCRIPT_DIR}/restore.sh" --prefix "${PREFIX}" --from "${FROM}" --yes-overwrite --no-pre-backup; then
  write_result failed 0
  notify_failure "restore test FAILED for ${PREFIX}"
  die "restore failed"
fi

pages="$(MYSQL_PWD="$(env_get MEDIAWIKI_DB_ROOT_PASSWORD)" docker exec -e MYSQL_PWD "${DB_CONTAINER}" \
  mysql --user=root --batch --skip-column-names "$(env_get MEDIAWIKI_DB_NAME)" -e 'SELECT COUNT(*) FROM page' 2>/dev/null || echo 0)"
if [ "${pages:-0}" -lt 1 ]; then
  write_result failed "${pages:-0}"
  notify_failure "restore test: ${PREFIX} restored but contains no pages"
  die "restored database has no pages"
fi

write_result ok "${pages}"
notify_success
log "=== Restore test passed: ${PREFIX} (${pages} pages) ==="
