#!/usr/bin/env bash
# =============================================================================
# bootstrap-wiki.sh — create the wiki's system pages (categories, CSS, footer
# links, legal pages, main page) through MediaWiki's maintenance script.
# =============================================================================
# Runs ON THE SERVER, needs no API credentials, and is idempotent: running it
# again writes the same text (MediaWiki records a null edit).
#
# Usage:
#   infra/deploy/bootstrap-wiki.sh --env staging
#   infra/deploy/bootstrap-wiki.sh --env production            # refuses while legal
#                                                              # placeholders remain or
#                                                              # the disclaimers are unapproved
#   infra/deploy/bootstrap-wiki.sh --env staging --pages-dir DIR   # use pre-rendered pages
#
# Environment:
#   APP_CONTAINER   name of the MediaWiki container
#                   (default: wikimedica_app, or wikimedica_app_staging for staging)
#   EDIT_CMD        full command that runs MediaWiki's edit.php and reads the page
#                   text from stdin (default: docker exec -i <container> php maintenance/run.php edit)
# =============================================================================
set -euo pipefail

ENVIRONMENT=""
PAGES_DIR=""

usage() { echo "Usage: $0 --env staging|production [--pages-dir DIR]" >&2; }

while [ "$#" -gt 0 ]; do
  case "$1" in
    --env)       ENVIRONMENT="${2:-}"; shift 2 ;;
    --pages-dir) PAGES_DIR="${2:-}"; shift 2 ;;
    -h|--help)   usage; exit 0 ;;
    *)           echo "unknown argument: $1" >&2; usage; exit 1 ;;
  esac
done

case "${ENVIRONMENT}" in
  staging|production) ;;
  *) usage; exit 1 ;;
esac

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [ "${ENVIRONMENT}" = "staging" ]; then
  APP_CONTAINER="${APP_CONTAINER:-wikimedica_app_staging}"
else
  APP_CONTAINER="${APP_CONTAINER:-wikimedica_app}"
fi
EDIT_CMD="${EDIT_CMD:-docker exec -i ${APP_CONTAINER} php maintenance/run.php edit}"

CLEANUP_DIR=""
if [ -z "${PAGES_DIR}" ]; then
  CLEANUP_DIR="$(mktemp -d)"
  PAGES_DIR="${CLEANUP_DIR}"
  trap 'rm -rf "${CLEANUP_DIR}"' EXIT
  python3 "${REPO_ROOT}/scripts/publishing/render_system_pages.py" --env "${ENVIRONMENT}" --out "${PAGES_DIR}"
fi

[ -f "${PAGES_DIR}/pages.tsv" ] || { echo "ERROR: ${PAGES_DIR}/pages.tsv not found" >&2; exit 1; }

count=0
while IFS=$'\t' read -r title file; do
  [ -n "${title}" ] || continue
  # shellcheck disable=SC2086  # EDIT_CMD is intentionally word-split into a command
  ${EDIT_CMD} --bot --no-rc --summary "Wikimedica system page bootstrap" "${title}" < "${PAGES_DIR}/${file}" >/dev/null
  count=$((count + 1))
done < "${PAGES_DIR}/pages.tsv"

echo "bootstrap complete: ${count} system pages written for ${ENVIRONMENT}"
