# Staging-First Deployment — Wikimedica

**Owner:** DevOps · **Last updated:** 2026-10-09 · **Status:** Active

Nothing reaches production that has not run on staging. Staging has its own compose project
(`DEPLOY_ENV=staging`: containers `wikimedica_app_staging`, `wikimedica_db_staging`, its own volumes and `.env`).
Edge topology (own Traefik vs. central gateway) is open decision DEC-1; both variants exist in `infra/docker/`.

## One-time setup of staging

1. Server with Docker/Compose; DNS name (e.g. `staging.wikimedica.de`, access-restricted: Cloudflare Access or basic auth).
2. `git clone` to `DEPLOY_PATH`; `cp infra/env/.env.example infra/env/.env`; fill every `REPLACE_WITH_…` (generate secrets with `openssl rand -hex 32`).
3. `DEPLOY_ENV=staging infra/deploy/deploy.sh --tag main --skip-backup` (staging may deploy a branch; first run has no database yet).
4. Install MediaWiki once (`php maintenance/run.php install …` with the DB values), copy `infra/mediawiki/LocalSettings.example.php`
   to `LocalSettings.php`, set the secrets from the environment, run `update.php`.
5. Create the bot: `Special:BotPasswords` for a dedicated account with a confirmed e-mail address; grants "Edit existing pages" and
   "Create, edit, and move pages"; store as GitHub environment secrets `WIKI_STAGING_API_URL`, `WIKI_STAGING_BOT_USER`, `WIKI_STAGING_BOT_PASSWORD`.
6. `infra/deploy/bootstrap-wiki.sh --env staging` (categories, CSS, footer, legal pages, main page).

## Per release

1. Merge to `main`; deploy the same revision to staging.
2. Acceptance test (record the result in the release issue):
   - [ ] `infra/deploy/healthcheck.sh` green
   - [ ] anonymous read, login, edit (VisualEditor and source), search, upload
   - [ ] protected namespaces cannot be edited by normal users
   - [ ] importer dry run, then real import to staging: `import_to_mediawiki.py --env staging --status approved`
   - [ ] pages carry notices, version box, categories; no unexpanded `{{ }}`
   - [ ] backup + `restore-test.sh` succeeded in the last 30 days
3. Tag `vX.Y.Z` on `main`; the *Deploy* workflow waits for approval of the `production` environment, then runs.
4. After production deploy: health check, one article smoke test, import of newly `published` articles
   (`--env production --status published --release-tag vX.Y.Z`).

## Rollback

Automatic when the health check fails after the switch; manual: `infra/deploy/rollback.sh <tag>`.
See `docs/operations/runbook.md`.
