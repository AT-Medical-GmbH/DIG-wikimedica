#!/usr/bin/env bash
# =============================================================================
# healthcheck.sh — one health check for deploys, cron and external monitoring
# =============================================================================
# Usage:
#   healthcheck.sh [--only core] [--wait SECONDS] [--json] [--strict]
#
#   --only core    check just the containers, database and the MediaWiki API
#                  (what a deploy needs to decide about rolling back)
#   --wait N       retry for up to N seconds until the checks pass
#   --json         machine-readable output (Uptime Kuma push monitor, Prometheus
#                  textfile collector, GitHub step summary)
#   --strict       treat warnings as failures
#
# Checks:  containers · database · app_api (real MediaWiki API answer, not just an HTTP
#          200 from the proxy) · edge (HTTPS through Traefik) · jobqueue · backup
#          freshness · certificate expiry · disk space
#
# Exit code: 0 healthy (warnings allowed unless --strict) · 1 at least one FAIL
# =============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=infra/deploy/lib.sh
source "${SCRIPT_DIR}/lib.sh"

ONLY=""
WAIT=0
JSON=0
STRICT=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --only)   ONLY="${2:-}"; shift 2 ;;
    --wait)   WAIT="${2:-0}"; shift 2 ;;
    --json)   JSON=1; shift ;;
    --strict) STRICT=1; shift ;;
    -h|--help) sed -n '2,22p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

JOBQUEUE_WARN="${JOBQUEUE_WARN:-5000}"
BACKUP_MAX_AGE_HOURS="${BACKUP_MAX_AGE_HOURS:-36}"
CERT_WARN_DAYS="${CERT_WARN_DAYS:-21}"
CERT_FAIL_DAYS="${CERT_FAIL_DAYS:-7}"
DISK_WARN_PCT="${DISK_WARN_PCT:-85}"
DISK_FAIL_PCT="${DISK_FAIL_PCT:-95}"

NAMES=()
STATES=()
DETAILS=()

record() {  # record NAME STATE DETAIL
  NAMES+=("$1")
  STATES+=("$2")
  DETAILS+=("$3")
}

container_state() {  # prints "<status> <health>" e.g. "running healthy"
  docker inspect -f '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$1" 2>/dev/null
}

check_containers() {
  local name state
  for name in "${APP_CONTAINER}" "${DB_CONTAINER}"; do
    state="$(container_state "${name}" || true)"
    case "${state}" in
      "running healthy"|"running none") record "container:${name}" OK "${state}" ;;
      "running starting")               record "container:${name}" FAIL "still starting" ;;
      "")                               record "container:${name}" FAIL "not found" ;;
      *)                                record "container:${name}" FAIL "${state}" ;;
    esac
  done
}

check_database() {
  if docker exec "${DB_CONTAINER}" healthcheck.sh --connect --innodb_initialized >/dev/null 2>&1; then
    record database OK "accepts connections"
  else
    record database FAIL "healthcheck.sh failed"
  fi
}

check_app_api() {
  # Ask MediaWiki itself, inside the container. A proxy that answers 200/301 proves nothing.
  local out
  out="$(docker exec "${APP_CONTAINER}" php -r \
    'echo @file_get_contents("http://127.0.0.1/api.php?action=query&meta=siteinfo&format=json");' 2>/dev/null || true)"
  if printf '%s' "${out}" | grep -q '"generator"[[:space:]]*:[[:space:]]*"MediaWiki'; then
    record app_api OK "$(printf '%s' "${out}" | grep -o '"generator"[[:space:]]*:[[:space:]]*"[^"]*"' | head -n1)"
  else
    record app_api FAIL "MediaWiki API did not return a valid answer"
  fi
}

check_edge() {
  local domain
  domain="$(env_get DOMAIN)"
  if [ -z "${domain}" ]; then
    record edge SKIP "DOMAIN not set"
    return
  fi
  if [ "${COMPOSE_FILES}" != "${COMPOSE_FILES%gateway-target.yml}" ]; then
    record edge SKIP "TLS is terminated by the central gateway"
    return
  fi
  local body
  body="$(curl -fsS --max-time 15 --resolve "${domain}:443:127.0.0.1" \
    "https://${domain}/api.php?action=query&meta=siteinfo&format=json" 2>/dev/null || true)"
  if printf '%s' "${body}" | grep -q '"generator"'; then
    record edge OK "https://${domain} answers through the proxy"
  else
    record edge FAIL "https://${domain} does not return the MediaWiki API through the proxy"
  fi
}

check_jobqueue() {
  local n
  n="$(docker exec "${APP_CONTAINER}" php maintenance/run.php showJobs 2>/dev/null | tr -dc '0-9' || true)"
  if [ -z "${n}" ]; then
    record jobqueue WARN "could not read the job queue"
  elif [ "${n}" -gt "${JOBQUEUE_WARN}" ]; then
    record jobqueue WARN "${n} jobs waiting (runJobs cron not running?)"
  else
    record jobqueue OK "${n} jobs waiting"
  fi
}

check_backup() {
  local status_file="${BACKUP_LOCAL_DIR}/last-backup.json" ts status epoch now age
  if [ ! -f "${status_file}" ]; then
    record backup WARN "no backup recorded yet"
    return
  fi
  status="$(grep -o '"status"[[:space:]]*:[[:space:]]*"[a-z]*"' "${status_file}" | head -n1 | sed 's/.*"\([a-z]*\)"$/\1/')"
  ts="$(grep -o '"finished_at"[[:space:]]*:[[:space:]]*"[^"]*"' "${status_file}" | head -n1 | sed 's/.*"\([^"]*\)"$/\1/')"
  epoch="$(date -u -d "${ts}" +%s 2>/dev/null || echo 0)"
  now="$(date -u +%s)"
  age=$(( (now - epoch) / 3600 ))
  if [ "${status}" != "ok" ]; then
    record backup FAIL "last backup status: ${status:-unknown}"
  elif [ "${age}" -gt "${BACKUP_MAX_AGE_HOURS}" ]; then
    record backup FAIL "last good backup is ${age}h old (limit ${BACKUP_MAX_AGE_HOURS}h)"
  else
    record backup OK "last good backup ${age}h ago"
  fi
}

check_cert() {
  local domain end epoch now days
  domain="$(env_get DOMAIN)"
  if [ -z "${domain}" ] || ! command -v openssl >/dev/null 2>&1 || [ "${COMPOSE_FILES}" != "${COMPOSE_FILES%gateway-target.yml}" ]; then
    record certificate SKIP "not applicable here"
    return
  fi
  end="$(echo | openssl s_client -connect 127.0.0.1:443 -servername "${domain}" 2>/dev/null \
    | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2 || true)"
  if [ -z "${end}" ]; then
    record certificate WARN "could not read the certificate"
    return
  fi
  epoch="$(date -u -d "${end}" +%s 2>/dev/null || echo 0)"
  now="$(date -u +%s)"
  days=$(( (epoch - now) / 86400 ))
  if [ "${days}" -lt "${CERT_FAIL_DAYS}" ]; then
    record certificate FAIL "expires in ${days} days"
  elif [ "${days}" -lt "${CERT_WARN_DAYS}" ]; then
    record certificate WARN "expires in ${days} days"
  else
    record certificate OK "valid for ${days} more days"
  fi
}

check_disk() {
  local pct
  pct="$(df -P "${DEPLOY_DIR}" 2>/dev/null | awk 'NR==2 {gsub("%","",$5); print $5}')"
  if [ -z "${pct}" ]; then
    record disk WARN "unknown"
  elif [ "${pct}" -ge "${DISK_FAIL_PCT}" ]; then
    record disk FAIL "${pct}% used"
  elif [ "${pct}" -ge "${DISK_WARN_PCT}" ]; then
    record disk WARN "${pct}% used"
  else
    record disk OK "${pct}% used"
  fi
}

run_checks() {
  NAMES=(); STATES=(); DETAILS=()
  check_containers
  check_database
  check_app_api
  if [ "${ONLY}" != "core" ]; then
    check_edge
    check_jobqueue
    check_backup
    check_cert
    check_disk
  fi
}

failures() {
  local i n=0
  for i in "${!STATES[@]}"; do
    if [ "${STATES[$i]}" = "FAIL" ]; then n=$((n + 1)); fi
    if [ "${STRICT}" = "1" ] && [ "${STATES[$i]}" = "WARN" ]; then n=$((n + 1)); fi
  done
  echo "${n}"
}

json_escape() { printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'; }

report() {
  local i overall="ok" bad
  bad="$(failures)"
  if [ "${bad}" -gt 0 ]; then overall="fail"; fi
  if [ "${JSON}" = "1" ]; then
    printf '{"status":"%s","environment":"%s","checks":[' "${overall}" "${DEPLOY_ENV}"
    for i in "${!NAMES[@]}"; do
      if [ "${i}" -gt 0 ]; then printf ','; fi
      printf '{"name":"%s","state":"%s","detail":"%s"}' \
        "$(json_escape "${NAMES[$i]}")" "${STATES[$i]}" "$(json_escape "${DETAILS[$i]}")"
    done
    printf ']}\n'
  else
    for i in "${!NAMES[@]}"; do
      printf '%-5s %-28s %s\n' "${STATES[$i]}" "${NAMES[$i]}" "${DETAILS[$i]}"
    done
  fi
}

deadline=$(( $(date +%s) + WAIT ))
while :; do
  run_checks
  if [ "$(failures)" -eq 0 ] || [ "$(date +%s)" -ge "${deadline}" ]; then
    break
  fi
  sleep "${HEALTH_SLEEP_SECONDS:-10}"
done

report
[ "$(failures)" -eq 0 ]
