#!/usr/bin/env bash
# =============================================================================
# rollback.sh — return to a previously deployed version
# =============================================================================
#   infra/deploy/rollback.sh v1.1.0 [--reason "text"] [--restore-db wikimedica_20261009_020000]
#
# * the target must be a release tag (production) or a commit that lies on origin/main
# * the stack is updated in place (`up -d`) — no `down` first, so the downtime is only
#   the container swap
# * the exit code tells the truth: 0 only if the health check passes afterwards
# * update.php is NOT run: older code cannot downgrade a database schema
# * the database is not touched unless you pass --restore-db (which restores that backup
#   set, see restore.sh; use it when a schema change made the old version unusable)
# =============================================================================
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=infra/deploy/lib.sh
source "${SCRIPT_DIR}/lib.sh"
LOG_PREFIX="ROLLBACK "

TARGET=""
REASON="manual rollback"
RESTORE_DB=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --reason)     REASON="${2:-}"; shift 2 ;;
    --restore-db) RESTORE_DB="${2:-}"; shift 2 ;;
    -h|--help)    sed -n '2,15p' "$0"; exit 0 ;;
    -*)           die "unknown option: $1" ;;
    *)            [ -z "${TARGET}" ] || die "target given twice"; TARGET="$1"; shift ;;
  esac
done
[ -n "${TARGET}" ] || die "usage: rollback.sh <tag-or-commit> [--reason TEXT] [--restore-db PREFIX]"

[ -d "${DEPLOY_DIR}/.git" ] || die "${DEPLOY_DIR} is not a git checkout"
if [ "${WM_DEPLOY_LOCK_HELD:-0}" != "1" ]; then
  exec 9>"${DEPLOY_DIR}/.deploy.lock"
  flock -n 9 || die "another deployment or rollback is running"
fi

cd "${DEPLOY_DIR}"
log "=== Rollback to ${TARGET} (${REASON}) ==="
git fetch --quiet origin --tags --prune || log "WARNING: git fetch failed; using local objects only"

COMMIT="$(git rev-parse -q --verify "${TARGET}^{commit}" || true)"
[ -n "${COMMIT}" ] || die "'${TARGET}' not found in the repository"
if [ "${DEPLOY_ENV}" = "production" ]; then
  if ! [[ "${TARGET}" =~ ${TAG_RE} ]] && ! [[ "${TARGET}" =~ ^[0-9a-f]{40}$ ]]; then
    die "production rolls back to a release tag (vX.Y.Z) or a full commit hash, not '${TARGET}'"
  fi
  git merge-base --is-ancestor "${COMMIT}" origin/main || die "${TARGET} is not on main"
fi

git checkout --quiet --detach "${COMMIT}"
log "Repository at ${COMMIT:0:12}."
compose config -q || die "docker compose configuration of ${TARGET} is invalid"
compose up -d --remove-orphans || die "docker compose up failed during the rollback"

if [ -n "${RESTORE_DB}" ]; then
  log "Restoring the database from ${RESTORE_DB}..."
  "${SCRIPT_DIR}/restore.sh" --prefix "${RESTORE_DB}" --db-only --yes-overwrite || die "database restore failed"
fi

log "Health check..."
if "${SCRIPT_DIR}/healthcheck.sh" --only core --wait "${HEALTH_WAIT_SECONDS:-180}"; then
  printf 'ref=%s\ncommit=%s\ndeployed_at=%s\nenvironment=%s\nrollback_reason=%s\n' \
    "${TARGET}" "${COMMIT}" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "${DEPLOY_ENV}" "${REASON}" > "${DEPLOY_DIR}/deployed-version"
  log "=== Rollback to ${TARGET} complete and healthy ==="
else
  docker logs --tail 40 "${APP_CONTAINER}" 2>&1 | sed 's/^/  app: /' || true
  die "the stack is NOT healthy after the rollback. If a schema change is the cause, restore the database: rollback.sh ${TARGET} --restore-db <backup prefix>"
fi
