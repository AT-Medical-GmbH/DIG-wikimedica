# Operations Runbook — Wikimedica

**Owner:** AT Medical Digital Solutions — DevOps · **Last updated:** 2026-10-09 · **Status:** Active

All commands run on the server in the repository checkout (`DEPLOY_PATH`). `DEPLOY_ENV`
defaults to `production`; use `DEPLOY_ENV=staging` for staging. Read-only checks first;
change nothing on production without a backup (the deploy script makes one itself).

## Daily checks

```bash
infra/deploy/healthcheck.sh            # containers, database, MediaWiki API, edge, job queue, backup age, certificate, disk
cat deployed-version                   # what is running (ref, commit, time, previous version)
cat backups/last-backup.json           # status of the last backup
```

Exit code 0 = healthy, 1 = at least one FAIL. Warnings are listed but do not fail.

## Standard tasks

| Task | Command |
|---|---|
| Deploy a release | GitHub → Actions → *Deploy* (tag push or manual with tag). On the server: `DEPLOY_ENV=production infra/deploy/deploy.sh --tag vX.Y.Z` |
| Roll back | `infra/deploy/rollback.sh vX.Y.(Z-1) --reason "text"` |
| Backup now | `infra/deploy/backup.sh` |
| List backups | `infra/deploy/restore.sh --list` |
| Create system pages | `infra/deploy/bootstrap-wiki.sh --env staging` |
| Run the job queue | `docker exec <app> php maintenance/run.php runJobs` (cron, see below) |

## Cron (server, user that owns the checkout)

```cron
# nightly backup 02:15, health check every 5 minutes, job queue every minute
15 2 * * *  cd /srv/wikimedica && infra/deploy/backup.sh >> deploy.log 2>&1
*/5 * * * * cd /srv/wikimedica && infra/deploy/healthcheck.sh --json > health.json 2>&1
* * * * *   docker exec wikimedica_app php maintenance/run.php runJobs --maxjobs 20 >/dev/null 2>&1
# monthly restore test on STAGING (1st, 04:00), see backup-restore-runbook.md
0 4 1 * *   cd /srv/wikimedica-staging && DEPLOY_ENV=staging infra/deploy/restore-test.sh --from /srv/restore-source
```

## Incidents

### Failed deployment

1. Read the `DEPLOY_RESULT=` line and `deploy-summary.md`.
2. `rolled-back`: the previous version runs again — open an issue, fix on staging, release a new tag.
3. `rollback-failed`: site may be down. `docker compose ps`, `docker logs --tail 100 <app>`, then
   `infra/deploy/rollback.sh <last good tag>`; if the database is the problem restore the
   pre-deployment backup (`backup-restore-runbook.md`, *Rollback after schema change*).
4. `failed` with "Nothing was changed on the server": fix the cause (tag not on main, incomplete `.env`, dirty checkout) and re-run.

### Site down / HTTP 5xx

`healthcheck.sh` shows which layer fails: container → `docker compose up -d`; database →
`docker logs <db>`, disk full?; app_api → `docker logs <app>`, last deployment?; edge →
Traefik/Cloudflare (certificate, DNS). If unresolved within 30 minutes and a deployment was the
trigger: roll back.

### Wrong or unsafe medical content

Not an IT incident but time-critical: set the article to `safety_hold`
(`docs/editorial/content-lifecycle.md`), re-run the importer for that slug — withdrawals are
never blocked by metadata errors. Inform the Medical Advisor.

### Suspected compromise

`security-response.md`.

## Contacts and escalation

DevOps on call → Management (Andreas Tremml) → Medical Advisor for content incidents. Names and
phone numbers are kept in the password manager, not in this repository.
