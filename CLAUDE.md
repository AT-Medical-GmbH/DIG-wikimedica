# Claude Code – WikiMedica

**Mandatory starting context:** [docs/operations/session-handover-2026-10-11.md](docs/operations/session-handover-2026-10-11.md). Also read [AGENTS.md](AGENTS.md).

As of 11 October 2026, production is **live** at https://wikimedica.info; the article *Arterielle Hypertonie* was created and read-back verified from the production MediaWiki container. The active pipeline is `beta-local`, not the former BotPassword/API path. Production and staging run in distinct Docker containers. The incremental daily systemd timer fires 06:30 Europe/Berlin.

**Security task:** The operator's MediaWiki import BotPassword is stored on the wiki production server at `/etc/wikimedica/secrets/mediawiki-import-botpassword` *after* the separate secret-save command; legacy source `/etc/wikimedica/github-pull.env` (root-only). Coordinate secure migration **to the separate central password-manager server** only after identifying its genuine authenticated vault destination. Keep the value out of commits, issues, chat, terminal logs, argument lists and debug output. Remove old copies only after read-back confirms vault entry and dependencies are migrated. The local MediaWiki CLI importer does not require the token.

Do not make silent production changes or claim a test passed without seeing its output. Follow the full handover for timelines, exact paths, PR references, medical editorial boundaries, follow-up tests, and BETA-logo task.
