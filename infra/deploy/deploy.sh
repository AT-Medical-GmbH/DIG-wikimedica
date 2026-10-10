#!/usr/bin/env bash
# =============================================================================
# deploy.sh — deploy a Wikimedica RELEASE TAG on the server
# =============================================================================
# Production deploys exactly one thing: a release tag vX.Y.Z that lies on main.
# No branches, no "latest", no commits.
#
#   DEPLOY_ENV=production infra/deploy/deploy.sh --tag v1.2.3
#   DEPLOY_ENV=staging    infra/deploy/deploy.sh --tag my-feature-branch     (any ref on staging)
#
# Sequence (every step aborts the deploy; once the checkout happened, a failure triggers
# an automatic rollback to the previous version):
#   1  lock, .env complete (no REPLACE_WITH placeholders), working tree clean
#   2  fetch, tag exists, tag is on origin/main (production)
#   3  BACKUP of database + uploads (skipped on a first deployment without a database)
#   4  checkout the tag, validate the compose config, pull images, start the stack
#   5  wait for the database/app containers, run update.php
#   6  health check (real MediaWiki API answer, not just a proxy 200)
#   7  record the deployed version; notify
#
# Result for the caller (GitHub Actions): the LAST line printed is
#   DEPLOY_RESULT=success | failed | rolled-back | rollback-failed
# and ${DEPLOY_DIR}/deploy-summary.md holds a Markdown report for the job summary / issue.
#
# Options:
#   --tag REF        what to deploy (a positional REF works as well)
#   --skip-backup    first deployment only; there is nothing to back up yet
#   --no-rollback    leave a failed deployment in place for inspection
# =============================================================================
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=infra/deploy/lib.sh
source "${SCRIPT_DIR}/lib.sh"
LOG_PREFIX="DEPLOY "

REF=""
SKIP_BACKUP=0
NO_ROLLBACK=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --tag)         [ -n "${2:-}" ] || die "--tag needs a value"; REF="$2"; shift 2 ;;
    --skip-backup) SKIP_BACKUP=1; shift ;;
    --no-rollback) NO_ROLLBACK=1; shift ;;
    -h|--help)     sed -n '2,32p' "$0"; exit 0 ;;
    -*)            die "unknown option: $1" ;;
    *)             [ -z "${REF}" ] || die "deployment ref given twice"; REF="$1"; shift ;;
  esac
done
[ -n "${REF}" ] || die "usage: deploy.sh --tag vX.Y.Z"

if [ "${DEPLOY_ENV}" = "production" ] && ! [[ "${REF}" =~ ${TAG_RE} ]]; then
  die "production deploys release tags only (vX.Y.Z). Refusing '${REF}'."
fi

SUMMARY="${DEPLOY_DIR}/deploy-summary.md"
CHANGED=0
DB_MIGRATED=0
PREV_DESC=""
RESULT="failed"
STARTED="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
HEALTH_REPORT=""

write_summary() {  # write_summary DETAIL
  {
    echo "## Wikimedica deployment — \`${DEPLOY_ENV}\`"
    echo
    echo "| | |"
    echo "|---|---|"
    echo "| Requested | \`${REF}\` |"
    echo "| Previous | \`${PREV_DESC:-none}\` |"
    echo "| Result | **${RESULT}** |"
    echo "| Started | ${STARTED} |"
    echo "| Finished | $(date -u '+%Y-%m-%dT%H:%M:%SZ') |"
    echo
    echo "$1"
    if [ -n "${HEALTH_REPORT}" ]; then
      echo
      echo '```text'
      echo "${HEALTH_REPORT}"
      echo '```'
    fi
  } > "${SUMMARY}" 2>/dev/null || true
}

on_failure() {
  local msg="$1" detail
  trap - ERR
  log "ERROR: ${msg}"
  detail="**What happened:** ${msg}"
  if [ "${CHANGED}" = "1" ] && [ "${NO_ROLLBACK}" != "1" ] && [ -n "${PREV_DESC}" ]; then
    log "Rolling back to ${PREV_DESC}..."
    if WM_DEPLOY_LOCK_HELD=1 "${SCRIPT_DIR}/rollback.sh" "${PREV_DESC}" --reason "deployment of ${REF} failed"; then
      RESULT="rolled-back"
      detail="${detail}"$'\n\n'"The previous version \`${PREV_DESC}\` is running again."
    else
      RESULT="rollback-failed"
      detail="${detail}"$'\n\n'"**The automatic rollback FAILED. The site may be down — follow docs/operations/runbook.md (incident: failed deployment).**"
    fi
    if [ "${DB_MIGRATED}" = "1" ]; then
      detail="${detail}"$'\n\n'"update.php had already migrated the database. Patch releases are schema-compatible; for a schema change restore the pre-deployment backup (docs/operations/backup-restore-runbook.md)."
    fi
  elif [ "${CHANGED}" = "0" ]; then
    detail="${detail}"$'\n\n'"Nothing was changed on the server."
  fi
  write_summary "${detail}"
  notify_failure "deploy ${REF} (${DEPLOY_ENV}): ${RESULT} — ${msg}"
  echo "DEPLOY_RESULT=${RESULT}"
  exit 1
}

fail() { on_failure "$*"; }
trap 'on_failure "command failed at line ${LINENO}"' ERR

# ---------------------------------------------------------------------------
# 1. Pre-flight
# ---------------------------------------------------------------------------
log "=== Deploy ${REF} to ${DEPLOY_ENV} ==="
[ -d "${DEPLOY_DIR}/.git" ] || fail "${DEPLOY_DIR} is not a git checkout"
command -v docker >/dev/null 2>&1 || fail "docker not found"
command -v git >/dev/null 2>&1 || fail "git not found"

if [ "${WM_DEPLOY_LOCK_HELD:-0}" != "1" ]; then
  exec 9>"${DEPLOY_DIR}/.deploy.lock"
  flock -n 9 || fail "another deployment or rollback is running"
fi

REQUIRED=(DOMAIN MEDIAWIKI_DB_NAME MEDIAWIKI_DB_USER MEDIAWIKI_DB_PASSWORD MEDIAWIKI_DB_ROOT_PASSWORD
          MEDIAWIKI_SECRET_KEY MEDIAWIKI_UPGRADE_KEY)
if [ "${COMPOSE_FILES}" = "${COMPOSE_FILES%gateway-target.yml}" ]; then
  REQUIRED+=(TRAEFIK_ACME_EMAIL CLOUDFLARE_API_TOKEN)
fi
( assert_env_keys "${REQUIRED[@]}" ) || fail ".env is incomplete or still contains REPLACE_WITH placeholders"

cd "${DEPLOY_DIR}"
[ -z "$(git status --porcelain --untracked-files=no)" ] || fail "the working tree has local modifications; refusing to deploy over them"

# ---------------------------------------------------------------------------
# 2. Resolve the ref
# ---------------------------------------------------------------------------
PREV_COMMIT="$(git rev-parse HEAD)"
PREV_DESC="$(git describe --tags --exact-match HEAD 2>/dev/null || echo "${PREV_COMMIT}")"
log "Currently deployed: ${PREV_DESC}"

# A tag must never move: if the remote tag differs from the local one, fetch refuses and we stop.
git fetch --quiet origin --tags --prune || fail "git fetch failed (a moved tag also causes this — tags must be immutable)"
# Production: a tag (checked below). Staging may name a branch; use the remote tip, not a stale local branch.
TARGET_COMMIT="$(git rev-parse -q --verify "origin/${REF}^{commit}" 2>/dev/null || git rev-parse -q --verify "${REF}^{commit}" || true)"
if [ "${DEPLOY_ENV}" = "production" ]; then
  TARGET_COMMIT="$(git rev-parse -q --verify "refs/tags/${REF}^{commit}" || true)"
fi
[ -n "${TARGET_COMMIT}" ] || fail "ref '${REF}' not found in the repository"
if [ "${DEPLOY_ENV}" = "production" ]; then
  git rev-parse -q --verify "refs/tags/${REF}" >/dev/null || fail "'${REF}' is not a tag"
  git merge-base --is-ancestor "${TARGET_COMMIT}" origin/main || fail "tag ${REF} is not on main; production deploys only what was merged to main"
fi
log "Target: ${REF} = ${TARGET_COMMIT:0:12}"

# ---------------------------------------------------------------------------
# 3. Backup first
# ---------------------------------------------------------------------------
if [ "${SKIP_BACKUP}" = "1" ]; then
  log "Backup skipped (--skip-backup)."
elif ! docker inspect "${DB_CONTAINER}" >/dev/null 2>&1; then
  log "No database container yet: this is a first deployment, nothing to back up."
else
  log "Creating the pre-deployment backup..."
  rc=0
  "${SCRIPT_DIR}/backup.sh" --no-rotate || rc=$?
  case "${rc}" in
    0) ;;
    3) log "WARNING: local backup is fine, the offsite upload failed. Continuing; fix the upload." ;;
    *) fail "the pre-deployment backup failed (exit ${rc}); nothing was changed" ;;
  esac
fi

# ---------------------------------------------------------------------------
# 4. Switch version
# ---------------------------------------------------------------------------
CHANGED=1
git checkout --quiet --detach "${TARGET_COMMIT}"
log "Checked out ${REF}."

compose config -q || fail "docker compose configuration of ${REF} is invalid"
log "Pulling images..."
compose pull --quiet || fail "docker compose pull failed"
log "Starting the stack..."
compose up -d --remove-orphans || fail "docker compose up failed"

# ---------------------------------------------------------------------------
# 5. Database schema
# ---------------------------------------------------------------------------
log "Waiting for the containers..."
for _ in $(seq 1 30); do
  if docker exec "${DB_CONTAINER}" healthcheck.sh --connect --innodb_initialized >/dev/null 2>&1 \
     && [ "$(docker inspect -f '{{.State.Running}}' "${APP_CONTAINER}" 2>/dev/null || echo false)" = "true" ]; then
    break
  fi
  sleep "${HEALTH_SLEEP_SECONDS:-5}"
done
if [ -f "${DEPLOY_DIR}/infra/mediawiki/LocalSettings.php" ]; then
  log "Running update.php (schema migrations)..."
  docker exec "${APP_CONTAINER}" php maintenance/run.php update --quick || fail "update.php failed"
  DB_MIGRATED=1
else
  log "No LocalSettings.php yet: skipping update.php (initial installation, see docs/deployment/staging-first-deployment.md)."
fi

# ---------------------------------------------------------------------------
# 6. Health
# ---------------------------------------------------------------------------
log "Health check..."
if ! HEALTH_REPORT="$("${SCRIPT_DIR}/healthcheck.sh" --only core --wait "${HEALTH_WAIT_SECONDS:-180}" 2>&1)"; then
  echo "${HEALTH_REPORT}"
  docker logs --tail 40 "${APP_CONTAINER}" 2>&1 | sed 's/^/  app: /' || true
  fail "the health check failed after the deployment"
fi
echo "${HEALTH_REPORT}"

# ---------------------------------------------------------------------------
# 7. Record and report
# ---------------------------------------------------------------------------
printf 'ref=%s\ncommit=%s\ndeployed_at=%s\nenvironment=%s\nprevious=%s\n' \
  "${REF}" "${TARGET_COMMIT}" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "${DEPLOY_ENV}" "${PREV_DESC}" > "${DEPLOY_DIR}/deployed-version"
RESULT="success"
write_summary "Deployed \`${REF}\` (\`${TARGET_COMMIT:0:12}\`). Health check passed."
notify_success
trap - ERR
log "=== Deploy of ${REF} complete ==="
echo "DEPLOY_RESULT=success"
