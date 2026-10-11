# Agent onboarding (Codex / CLI / AI agents)

**Read first:** [WikiMedica operational handover, 11 October 2026](docs/operations/session-handover-2026-10-11.md).

This is a production MediaWiki 1.43 project. The live website is **https://wikimedica.info**. The first article `Arterielle Hypertonie` was imported successfully and verified by reading it back from the production container.

**Effective BETA import pipeline:** GitHub `main` -> dedicated checkout on wiki host -> `infra/deploy/pull-content-from-github.sh --env production --mode beta-local` -> `scripts/publishing/import_merged_beta_local.py` -> `docker exec wikimedica_app php maintenance/run.php edit/getText`; timer daily 06:30 Europe/Berlin.

**Do not** rely on GitHub Actions or the public MediaWiki Action API (last test 403). Do not confuse staging and production. Do not disable the conventional release-tag/clinical/legal gates to enable BETA publication. The operator's merge authorizes a **visibly labelled BETA** article only; it is not independent clinical peer review.

**Secret migration:** The MediaWiki API bot token is not needed for the active local importer. The root-only local secret location on the WikiMedica production host is `/etc/wikimedica/secrets/mediawiki-import-botpassword` (operator-confirmed as created on 11 October 2026; root:root 0600 in root-only directory 0700). Historic source `/etc/wikimedica/github-pull.env`, variable `WIKI_PRODUCTION_BOT_PASSWORD`. Codex must **move the token from the production host to the central password vault running on a different server**, with an authenticated encrypted transport and verified vault read-back; remove local copies only after confirming dependencies and successful transfer. Never print, commit, or echo the value. The vault host/address is **not yet confirmed** and must be discovered from trusted private infrastructure configuration, never guessed.

Current priorities: retain the verified initial incremental sync SHA (confirmed at 45dba487...), run a follow-up article update test, fix the old superscript BETA logo duplication while retaining the article disclaimer, migrate the secret into the central server's password manager, modernize obsolete docs, and implement the actual AI evidence review agent (issue #266). See detailed handover.

**Latest confirmed operator outputs (11.10.2026):** `/var/lib/wikimedica-pull/beta-last-successful-sha` = `45dba4873b64038583a658116e0f9b7ecddc6daa`; `systemctl start wikimedica-beta-sync.service` succeeded, reported 0 changes. The secret exists with root-only permissions, but **has NOT yet been transferred to the password vault on the separate server**. Never claim that migration is done.
