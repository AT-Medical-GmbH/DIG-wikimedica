# Disaster Recovery — Wikimedica

**Owner:** DevOps · **Last updated:** 2026-10-09 · **Status:** Active

**Targets (proposal, owner to confirm):** RPO 24 h (nightly backup; content is also in Git) ·
RTO 4 h for a rebuilt server.

## What exists where

| Asset | Source of truth | Recoverable from |
|---|---|---|
| Articles, templates, scripts, configuration | Git (GitHub) | clone |
| Wiki database (accounts, talk pages, history) | server | offsite backup |
| Uploads (images) | server volume | offsite backup |
| Secrets | password manager / GitHub secrets | there (never in Git or backups) |
| DNS, TLS | Cloudflare / ACME | Cloudflare dashboard, re-issued automatically |

## Scenario: server lost

1. Provision a server (same OS, Docker, Compose); open ports 80/443; secure SSH.
2. Clone the repository to `DEPLOY_PATH`; create `infra/env/.env` from `.env.example` with the secrets from the password manager.
3. Fetch the newest complete backup set and the GPG private key; put the set into `backups/`.
4. `DEPLOY_ENV=production infra/deploy/deploy.sh --tag <last deployed tag> --skip-backup` (first deployment without database).
5. `infra/deploy/restore.sh --prefix <set> --yes-overwrite --no-pre-backup` (the database is empty).
6. Point Cloudflare DNS to the new IP; check certificate issuance.
7. `infra/deploy/healthcheck.sh`; log in; open recent pages; re-run the importer for `published` articles newer than the backup (idempotent).
8. Write the incident report (what, when, data loss window).

## Scenario: database corrupted / bad edit run

Stop writes (`docker stop <app>`), restore the newest good set with `restore.sh`; the safety
dump preserves the broken state for analysis.

## Scenario: GitHub unavailable

The server keeps running. Deployments wait. A local clone on the server is enough for rollback.

## Scenario: Cloudflare/DNS problem

Switch the record to DNS-only (grey cloud) temporarily; the origin keeps its own certificate.

## Exercise

Run the server-lost scenario on staging once before go-live and then yearly; record the time taken.
