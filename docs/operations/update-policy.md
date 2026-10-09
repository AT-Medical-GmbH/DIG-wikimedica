# Update Policy — Wikimedica

**Owner:** DevOps · **Last updated:** 2026-10-09 · **Status:** Active
Base: MediaWiki 1.43 LTS, MariaDB 10.11 LTS (see `docs/architecture/version-policy.md`).

| Class | Example | Deadline | Path |
|---|---|---|---|
| Security fix, actively exploited | MediaWiki security release | 24 h | staging smoke test (minimum) → emergency release tag |
| Security fix | MediaWiki / Traefik / MariaDB advisory | 7 days | staging → release tag |
| Patch / minor | 1.43.x, image digest update | monthly | staging → release tag |
| Major / LTS change | 1.43 → next LTS | planned project | full staging run with production data copy, restore test, maintenance window |

## Process

1. Change the pinned version (tarball URL and **SHA-256** in the Dockerfile/compose, image digest).
2. Pull request; CI must be green.
3. Deploy to staging (`DEPLOY_ENV=staging infra/deploy/deploy.sh --tag <branch>`); smoke test: read, login,
   edit, VisualEditor, search, upload, `api.php`, job queue, importer dry run.
4. Merge, tag `vX.Y.Z`, production deploy through the workflow (backup → update.php → health check → automatic rollback).
5. Record the new pins in the release notes.

## Rules

- No `latest` tags; no unpinned downloads; every download verified by checksum (MediaWiki's GPG signature is a
  recommended extra check at upgrade time).
- Extensions only from the bundled set or pinned to `REL1_43`.
- Dependabot PRs are reviewed within 7 days; a high-severity alert is handled like a security fix.
- Findings from real-MediaWiki tests that must be re-checked on every upgrade: TemplateStyles is not bundled
  (do not load it); the custom right `wm-edit-content` must be in the bot grant; bot-password format; confirmed
  e-mail address for the bot; sysop rights explicitly granted. They are covered by
  `tests/integration/test_real_mediawiki.py` (`WM_REAL_MW=1`).
