# Monitoring — Wikimedica

**Owner:** DevOps · **Last updated:** 2026-10-09 · **Status:** Active

## Internal: `infra/deploy/healthcheck.sh`

| Check | FAIL when | WARN when |
|---|---|---|
| containers | app or database not running / still starting | — |
| database | `healthcheck.sh --connect --innodb_initialized` fails | — |
| app_api | MediaWiki API inside the container does not answer with its siteinfo | — |
| edge | HTTPS through Traefik does not answer | — |
| jobqueue | — | more than `JOBQUEUE_WARN` (5000) jobs |
| backup | no backup / last backup failed | older than `BACKUP_MAX_AGE_HOURS` (36) |
| certificate | expires in < 7 days | < 21 days |
| disk | > 95 % | > 85 % |

`--json` produces machine-readable output; `--strict` turns warnings into failures.

## External (to set up before go-live)

- Uptime monitor (e.g. Uptime Kuma or an external service) on `https://wikimedica.de/api.php?action=query&meta=siteinfo&format=json` — content check for `"generator":"MediaWiki`.
- Heartbeat: `HEALTHCHECK_URL` (push monitor) pinged by the 5-minute cron when the check passes; a missing ping alerts.
- Alerts to `ALERT_EMAIL`; `notify_failure` in `lib.sh` sends deploy failures there (needs the `mail` command on the host and `HEALTHCHECK_URL` for the fail ping).
- GitHub: Dependabot alerts, the daily PubMed workflow (opens issues), the monthly guideline reminder.

## Privacy

No analytics or tracking by default (DEC-5 proposal). Access logs on the server should be kept for
7 days and not shipped to third parties; see `docs/legal/privacy-notes.md`.
