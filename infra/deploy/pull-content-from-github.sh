#!/usr/bin/env bash
# GitHub -> MediaWiki pull importer (runs on the WikiMedica server; NO GitHub Actions).
#
# Modes:
#   probe              fetch merged main and write/read-back ONE harmless system test page
#   staging-import     fetch merged main and import eligible approved/published articles to staging
#   production-release fetch latest release tag on main and import published articles to production
#
# Never modifies the running MediaWiki containers, GitHub main, or an existing
# application checkout. Uses a separate source checkout and an exclusive lock.
set -Eeuo pipefail
umask 077

usage() {
  cat >&2 <<'EOF'
Usage: pull-content-from-github.sh --env staging|production \
       --mode probe|staging-import|production-release [--tag vX.Y.Z] \
       [--only article-slug] [--dry-run]

Environment:
  WIKIMEDICA_SOURCE_DIR  Separate writable Git checkout (default /opt/wikimedica-source)
  WIKIMEDICA_GIT_URL     Repository Git URL (default public HTTPS)
  WIKIMEDICA_OUTPUT_DIR  Writable logs/results directory (default /var/lib/wikimedica-pull)
  WIKI_STAGING_API_URL, WIKI_STAGING_BOT_USER, WIKI_STAGING_BOT_PASSWORD
  WIKI_PRODUCTION_API_URL, WIKI_PRODUCTION_BOT_USER, WIKI_PRODUCTION_BOT_PASSWORD

This script does NOT interpret a plain PR merge as permission to import a
clinical draft. Production still imports only status: published at a release tag
and honours the legal disclaimer gate.
EOF
}

SOURCE_DIR="${WIKIMEDICA_SOURCE_DIR:-/opt/wikimedica-source}"
REPO_URL="${WIKIMEDICA_GIT_URL:-https://github.com/AT-Medical-GmbH/DIG-wikimedica.git}"
OUTPUT_DIR="${WIKIMEDICA_OUTPUT_DIR:-/var/lib/wikimedica-pull}"
ENVIRONMENT=""
MODE=""
TAG=""
ONLY=""
DRY_RUN=0

die() { echo "ERROR: $*" >&2; exit 2; }
log() { printf 'WikiMedica pull: %s\n' "$*" >&2; }

while [ "$#" -gt 0 ]; do
  case "$1" in
    --env) [ "$#" -ge 2 ] || die "--env needs a value"; ENVIRONMENT="$2"; shift 2 ;;
    --mode) [ "$#" -ge 2 ] || die "--mode needs a value"; MODE="$2"; shift 2 ;;
    --tag) [ "$#" -ge 2 ] || die "--tag needs a value"; TAG="$2"; shift 2 ;;
    --only) [ "$#" -ge 2 ] || die "--only needs a value"; ONLY="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) usage; die "Unknown option: $1" ;;
  esac
done

case "$ENVIRONMENT:$MODE" in
  staging:probe|production:probe|staging:staging-import|production:production-release) ;;
  *) usage; die "Unsupported env/mode combination: $ENVIRONMENT/$MODE" ;;
esac

if [ -n "$ONLY" ] && ! [[ "$ONLY" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
  die "Invalid --only slug"
fi
if [ -n "$TAG" ] && ! [[ "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  die "Invalid --tag format; expected vX.Y.Z"
fi

for cmd in git python3 flock; do
  command -v "$cmd" >/dev/null 2>&1 || die "Missing command: $cmd"
done

# Use an absolute lock path outside the checkout. Concurrent cron runs must
# never switch the same working tree while an API import is in progress.
mkdir -p -- "$OUTPUT_DIR"
exec 9>"$OUTPUT_DIR/pull.lock"
flock -n 9 || die "Another WikiMedica pull is already in progress"

if [ -d "$SOURCE_DIR/.git" ]; then
  ACTUAL_REMOTE="$(git -C "$SOURCE_DIR" remote get-url origin)"
  [ "$ACTUAL_REMOTE" = "$REPO_URL" ] || die "Git origin does not match WIKIMEDICA_GIT_URL"
  [ -z "$(git -C "$SOURCE_DIR" status --porcelain)" ] ||
    die "Source checkout has local changes; refusing to overwrite"
elif [ -e "$SOURCE_DIR" ]; then
  die "Source directory already exists but is not a Git checkout: $SOURCE_DIR"
else
  mkdir -p -- "$(dirname -- "$SOURCE_DIR")"
  log "Cloning source repository (read-only remote)"
  git clone --no-checkout -- "$REPO_URL" "$SOURCE_DIR"
fi

log "Fetching main and immutable release tags from GitHub"
git -C "$SOURCE_DIR" fetch --prune --tags origin main
MAIN_SHA="$(git -C "$SOURCE_DIR" rev-parse --verify refs/remotes/origin/main^{commit})"

if [ "$MODE" = production-release ]; then
  if [ -z "$TAG" ]; then
    # Automatic periodic import of the newest release reachable from main.
    TAG="$(git -C "$SOURCE_DIR" tag --merged origin/main --list 'v*' --sort=-version:refname |
      grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | head -n 1 || true)"
  fi
  [ -n "$TAG" ] || die "No release tag reachable from main. Create a vX.Y.Z release tag first."
  git -C "$SOURCE_DIR" rev-parse -q --verify "refs/tags/$TAG^{commit}" >/dev/null ||
    die "Release tag $TAG not found"
  git -C "$SOURCE_DIR" merge-base --is-ancestor "refs/tags/$TAG^{commit}" origin/main ||
    die "Release tag $TAG is not on main"
  REF="refs/tags/$TAG"
else
  REF="refs/remotes/origin/main"
fi

git -C "$SOURCE_DIR" checkout -q --detach "$REF"
CURRENT_SHA="$(git -C "$SOURCE_DIR" rev-parse HEAD)"
log "Checked out $CURRENT_SHA (main: $MAIN_SHA), mode=$MODE"

case "$MODE" in
  probe)
    ARGS=(--env "$ENVIRONMENT")
    if [ "$DRY_RUN" -eq 1 ]; then ARGS+=(--dry-run); fi
    python3 "$SOURCE_DIR/scripts/publishing/verify_github_transport.py" "${ARGS[@]}"
    ;;
  staging-import)
    ARGS=(--env staging --status both
          --content-dir "$SOURCE_DIR/content"
          --schema "$SOURCE_DIR/data/metadata/article-schema.yaml"
          --disclaimers "$SOURCE_DIR/data/legal/disclaimers.yaml"
          --output-dir "$OUTPUT_DIR/staging")
    if [ "$DRY_RUN" -eq 1 ]; then ARGS+=(--dry-run); fi
    if [ -n "$ONLY" ]; then ARGS+=(--only "$ONLY"); fi
    python3 "$SOURCE_DIR/scripts/publishing/import_to_mediawiki.py" "${ARGS[@]}"
    ;;
  production-release)
    ARGS=(--env production --status published --release-tag "$TAG"
          --content-dir "$SOURCE_DIR/content"
          --schema "$SOURCE_DIR/data/metadata/article-schema.yaml"
          --disclaimers "$SOURCE_DIR/data/legal/disclaimers.yaml"
          --output-dir "$OUTPUT_DIR/production")
    if [ "$DRY_RUN" -eq 1 ]; then ARGS+=(--dry-run); fi
    if [ -n "$ONLY" ]; then ARGS+=(--only "$ONLY"); fi
    python3 "$SOURCE_DIR/scripts/publishing/import_to_mediawiki.py" "${ARGS[@]}"
    ;;
esac

log "Completed successfully: $MODE at $CURRENT_SHA"
