# Maintenance Plan — Wikimedica

**Owner:** DevOps · **Last updated:** 2026-10-09 · **Status:** Active

| Interval | Task | Who |
|---|---|---|
| continuous | health check (5 min), job queue (1 min) | cron |
| daily | backup 02:15; PubMed surveillance workflow; look at `last-backup.json` | cron / DevOps |
| weekly | read open `incident` / `security` issues; check Dependabot alerts; check disk and certificate warnings | DevOps |
| monthly | restore test on staging; guideline review reminder issue; review user list and admin accounts | DevOps / Editorial |
| quarterly | rotate bot password and deploy key; review GitHub team membership and branch protection | DevOps / Management |
| yearly | disaster-recovery exercise; review this plan, the version policy and the disclaimer text with Legal | DevOps / Legal |

## Maintenance window

Announce schema-changing releases and restores at least 24 h ahead (banner via `MediaWiki:Sitenotice`);
patch releases are done without a window.

## Housekeeping

- `docker image prune` only for images older than the current and previous release.
- Old `prerestore_*` safety dumps: delete after 14 days once the restore is confirmed good.
- Logs: `deploy.log` should be rotated by logrotate (weekly, 8 files) — to be configured on the server.
