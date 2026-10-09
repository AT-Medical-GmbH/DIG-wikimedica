#!/usr/bin/env bash
# shellcheck shell=bash
# =============================================================================
# lib.sh — shared helpers of the Wikimedica deploy scripts.  SOURCE it, do not run it.
# =============================================================================
# Configuration (environment, all optional):
#   DEPLOY_DIR      repository checkout on the server        (default /opt/wikimedica)
#   DEPLOY_ENV      production | staging                     (default production)
#   COMPOSE_FILES   colon-separated compose files, relative to DEPLOY_DIR or absolute
#                   (default: production -> docker-compose.yml,
#                             staging    -> docker-compose.yml + docker-compose.staging.yml;
#                    gateway topology: infra/docker/docker-compose.gateway-target.yml)
#   APP_CONTAINER / DB_CONTAINER / PROJECT_NAME   override the derived names
#   ENV_FILE        the .env file                            (default infra/env/.env)
#
# The .env file is NEVER executed. Values are read with env_get (plain KEY=VALUE),
# because passwords may contain $, backticks or quotes.
# =============================================================================

DEPLOY_DIR="${DEPLOY_DIR:-/opt/wikimedica}"
DEPLOY_ENV="${DEPLOY_ENV:-production}"
ENV_FILE="${ENV_FILE:-${DEPLOY_DIR}/infra/env/.env}"
LOG_FILE="${LOG_FILE:-${DEPLOY_DIR}/deploy.log}"
LOG_PREFIX="${LOG_PREFIX:-}"

case "${DEPLOY_ENV}" in
  production)
    _suffix=""
    PROJECT_NAME="${PROJECT_NAME:-wikimedica}"
    COMPOSE_FILES="${COMPOSE_FILES:-infra/docker/docker-compose.yml}"
    ;;
  staging)
    _suffix="_staging"
    PROJECT_NAME="${PROJECT_NAME:-wikimedica_staging}"
    COMPOSE_FILES="${COMPOSE_FILES:-infra/docker/docker-compose.yml:infra/docker/docker-compose.staging.yml}"
    ;;
  *)
    echo "DEPLOY_ENV must be 'production' or 'staging' (got '${DEPLOY_ENV}')" >&2
    exit 1
    ;;
esac

APP_CONTAINER="${APP_CONTAINER:-wikimedica_app${_suffix}}"
DB_CONTAINER="${DB_CONTAINER:-wikimedica_db${_suffix}}"
BACKUP_LOCAL_DIR="${BACKUP_LOCAL_DIR:-${DEPLOY_DIR}/backups}"
BACKUP_NAME="${BACKUP_NAME:-wikimedica${_suffix//_/-}}"
IMAGES_VOLUME="${IMAGES_VOLUME:-wikimedica${_suffix}_images}"
# shellcheck disable=SC2034  # used by deploy.sh / rollback.sh
TAG_RE='^v[0-9]+\.[0-9]+\.[0-9]+$'

log() {
  local line
  line="[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] ${LOG_PREFIX}$*"
  echo "${line}"
  if [ -n "${LOG_FILE}" ]; then
    echo "${line}" >> "${LOG_FILE}" 2>/dev/null || true
  fi
}

die() {
  log "ERROR: $*"
  exit 1
}

# env_get KEY [DEFAULT] — read one value from the .env file without executing it.
env_get() {
  local key="$1" default="${2:-}" line value
  if [ ! -f "${ENV_FILE}" ]; then
    printf '%s' "${default}"
    return 0
  fi
  line="$(grep -E "^${key}=" "${ENV_FILE}" | tail -n 1 || true)"
  if [ -z "${line}" ]; then
    printf '%s' "${default}"
    return 0
  fi
  value="${line#*=}"
  case "${value}" in
    \"*\") value="${value#\"}"; value="${value%\"}" ;;
    \'*\') value="${value#\'}"; value="${value%\'}" ;;
  esac
  printf '%s' "${value}"
}

# compose ARGS... — docker compose with the right project, env file and compose files.
compose() {
  local files=() args=() f
  IFS=':' read -r -a files <<< "${COMPOSE_FILES}"
  for f in "${files[@]}"; do
    case "${f}" in
      /*) args+=(-f "${f}") ;;
      *)  args+=(-f "${DEPLOY_DIR}/${f}") ;;
    esac
  done
  docker compose --project-name "${PROJECT_NAME}" --env-file "${ENV_FILE}" "${args[@]}" "$@"
}

# env_opt KEY — like env_get, but a value that is still a REPLACE_WITH_* placeholder counts as "not set".
env_opt() {
  local value
  value="$(env_get "$1")"
  case "${value}" in
    *REPLACE_WITH*) value="" ;;
  esac
  printf '%s' "${value}"
}

# assert_env_keys KEY... — every key must be present and must not be a placeholder.
# A forgotten placeholder would start the site with a publicly known password.
assert_env_keys() {
  [ -f "${ENV_FILE}" ] || die ".env file not found: ${ENV_FILE}"
  local key missing=""
  for key in "$@"; do
    if [ -z "$(env_opt "${key}")" ]; then
      missing="${missing} ${key}"
    fi
  done
  if [ -n "${missing}" ]; then
    die ".env is incomplete (missing or still a REPLACE_WITH placeholder):${missing}"
  fi
}

notify_failure() {
  local message="$1" url email
  url="$(env_get HEALTHCHECK_URL)"
  email="$(env_get ALERT_EMAIL)"
  if [ -n "${email}" ] && command -v mail >/dev/null 2>&1; then
    printf 'Wikimedica (%s): %s\n' "${DEPLOY_ENV}" "${message}" \
      | mail -s "[Wikimedica] ${DEPLOY_ENV} deployment FAILED" "${email}" 2>/dev/null || true
  fi
  case "${url}" in
    ''|*REPLACE_WITH*) ;;
    *) curl -fsS --max-time 10 --data-raw "${message}" "${url%/}/fail" >/dev/null 2>&1 || true ;;
  esac
}

notify_success() {
  local url
  url="$(env_get HEALTHCHECK_URL)"
  case "${url}" in
    ''|*REPLACE_WITH*) ;;
    *) curl -fsS --max-time 10 "${url}" >/dev/null 2>&1 || true ;;
  esac
}
