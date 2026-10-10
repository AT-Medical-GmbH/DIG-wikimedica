# Backup and Restore Runbook — Wikimedica

**Owner:** DevOps · **Last updated:** 2026-10-09 · **Status:** Active
**Principle: restore matters more than backup.** A backup counts only after a restore worked.

## What is backed up

One *set* per run in `BACKUP_LOCAL_DIR` (default `backups/`), name `wikimedica_YYYYmmdd_HHMMSS_*`:

| File | Content |
|---|---|
| `_db.sql.gz` | full database dump (binary charset, single transaction, verified with `gzip -t` and the dump trailer) |
| `_images.tar.gz` | uploads volume |
| `_config.tar.gz` | `LocalSettings.php` with secret-looking values redacted + `deployed-version` |
| `.sha256` | checksums of the files above |
| `.manifest.json` | written **last**; a set without it is incomplete and never counts |

**Not** in the backup: the `.env` file (all secrets). Keep the secrets in the password manager
and the GitHub environment secrets; a restore on a new server needs them. The article content
itself is in Git and can be re-imported.

## Retention (GFS)

7 daily + 4 weekly + 3 monthly sets, newest complete set never deleted, incomplete sets removed
after 48 h (`rotate-backups.py`; defaults overridable with `BACKUP_RETAIN_*`).

## Offsite copy and encryption

Local backups on the same server do not survive a server loss. Set a target (DEC-7: S3-compatible
or SFTP) and `BACKUP_GPG_RECIPIENT`. **Offsite upload without encryption is refused** (exit 3)
unless `BACKUP_ALLOW_UNENCRYPTED_UPLOAD=1` is set deliberately — the dump contains user e-mail
addresses and password hashes. Keep the private GPG key outside the server (password manager,
printed copy in the safe). Exit code 3 means: local backup fine, upload failed — fix before the
next run.

## Restore

```bash
infra/deploy/restore.sh --list                                   # sets and their state
infra/deploy/restore.sh --prefix wikimedica_20261009_021500 --yes-overwrite
        # options: --db-only | --images-only | --from DIR | --no-pre-backup
```

The script refuses without `--yes-overwrite`, verifies checksums, decrypts `.gpg`, writes a
safety dump of the current database (`prerestore_*_db.sql.gz`), stops the app, imports, restores
uploads, starts the app, runs `update.php` and the health check. If anything fails the app is
started again and the safety dump is the way back
(`gunzip -c prerestore_….sql.gz | docker exec -i <db> mysql …`).

### Rollback after a schema change

Patch releases are schema-compatible, so `rollback.sh vX.Y.Z` is enough. If a release changed the
schema and the old version no longer runs:
`infra/deploy/rollback.sh vX.Y.Z --restore-db <pre-deployment set>` — edits made since that backup are lost
(announce a maintenance window).

## Monthly restore test (staging)

1. Copy the newest production set (from the offsite target) to the staging host, e.g. `/srv/restore-source`.
2. `DEPLOY_ENV=staging infra/deploy/restore-test.sh --from /srv/restore-source`
3. Result in `backups/last-restore-test.json` (status, set, page count, time). Fail = open an issue the same day.
4. Document the date and result in the log below.

| Date | Set | Result | By |
|---|---|---|---|
| *(first test before go-live)* | | | |

## Verification

The tests `tests/test_backup_restore.py` run these scripts against a real MariaDB (umlauts,
binary data, damaged and incomplete sets, wrong GPG key, refused unencrypted upload).
