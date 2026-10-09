# MediaWiki Version Policy — Wikimedica

**Document version:** 1.0
**Owner:** AT Medical Digital Solutions — Engineering / DevOps
**Last updated:** 2026-10-09
**Status:** Active — decision record + upgrade policy

---

## 1. Decision

Wikimedica standardises on **MediaWiki 1.43 LTS** as its conservative
production base, pinned by image tag **and** digest (never `latest`). The
current repository pin `mediawiki:1.42` is retired.

```yaml
# infra/docker/docker-compose.yml (target)
mediawiki:
  image: mediawiki:1.43   # pin to a specific 1.43.x + @sha256 digest in production
```

---

## 2. Rationale

- **LTS, not a standard release.** 1.42 is a standard (non-LTS) release and is
  past end-of-life; standard releases receive only a short support window.
  1.43 is a **Long-Term-Support** line with multi-year security maintenance —
  the right base for a public medical platform where unplanned major upgrades
  are a patient-safety and availability risk.
- **Conservative, not bleeding-edge.** We do **not** track `latest`. A pinned
  LTS gives a predictable, auditable, reproducible deployment and a defined
  upgrade cadence.
- **Ecosystem maturity.** The bundled extensions and skins Wikimedica relies on
  (Vector 2022, MinervaNeue, VisualEditor, Cite, ParserFunctions,
  TemplateStyles, CategoryTree, SyntaxHighlight, Echo, ConfirmEdit,
  TitleBlacklist) are maintained against the LTS line.

---

## 3. Compatibility checklist (verify on staging before promotion)

| Area | Requirement for 1.43 | Action |
|---|---|---|
| **PHP** | Use the PHP version bundled in the official `mediawiki:1.43` image; do not override. | Confirm `php -v` in the built image; run `maintenance/checkComposerLockUpToDate.php`. |
| **MariaDB** | 10.6+ supported; project uses **10.11 LTS**. | Keep 10.11 pin; run `update.php` after upgrade. |
| **VisualEditor / Parsoid** | Parsoid ships **inside core** since 1.35 — **no standalone Parsoid/RESTBase service**. | Remove the legacy `$wgVirtualRestConfig['modules']['parsoid']` block; enable VE via `wfLoadExtension('VisualEditor')`. |
| **Skins** | Vector 2022 + MinervaNeue bundled. | Confirm `$wgDefaultSkin = 'vector-2022'`. |
| **Extensions** | All required extensions are bundled in the tarball image. | For any non-bundled extension, pin to the **REL1_43** branch. |
| **Deprecated config** | `$wgUseSquid`/`$wgSquidServers` → `$wgUseCdn`/`$wgCdnServers`. | Fix in `LocalSettings.example.php`. |
| **Invalid config** | `$wgRevisionStoreType` is not a real setting. | Remove. |
| **Object cache / jobs** | APCu + DB by default; Redis optional (eval). | Decide per concept DEC-3; run `runJobs.php` via cron if no queue service. |
| **Search** | MySQL/MariaDB full-text by default; CirrusSearch+OpenSearch optional. | Decide per concept DEC-3 at scale. |

---

## 4. Upgrade & rollback path

1. **Staging first.** Build and run the target image on staging with a copy of
   production data; never upgrade production in place blindly.
2. **Backup before upgrade** (DB + images + non-secret config).
3. Bring up the new image; run `php maintenance/update.php --quick`.
4. Smoke-test: read paths, login, edit, VisualEditor round-trip, search,
   upload, `api.php`, job queue.
5. Promote to production via the release-tag deploy workflow
   (`backup → up → health-check → rollback-on-failure`).
6. **Rollback:** re-pin the previous image digest, restore DB/images from the
   pre-upgrade backup, run `update.php` if needed. See
   the planned `docs/operations/backup-restore-runbook.md` (Phase 5)
   and `rollback.sh`.

---

## 5. Pinning policy

- Pin every image to a specific version **and** digest in production compose.
- Record the pinned digests in the deploy log / release notes.
- Review the pin on each LTS point release and on any security advisory; apply
  via the staging-first upgrade path above.
- No image is promoted to production from a `latest` or unpinned tag.

---

## 6. Review cadence

Reviewed on every MediaWiki LTS point release, on any relevant CVE, and at least
**annually**. Next scheduled review: see repository guideline/maintenance
reminders.

---

## 7. Findings from tests against a real MediaWiki 1.43.11

The importer and settings were exercised on a real MediaWiki 1.43.11 (`tests/integration/`, opt-in `WM_REAL_MW=1`).
Defects found there and fixed in this repository:

- **TemplateStyles is not bundled** with the 1.43 tarball; loading it is a fatal error → it stays commented out.
- **Custom edit right**: `wm-edit-content` must also be granted to bot passwords
  (`$wgGrantPermissions['editpage']`), otherwise the bot cannot edit protected namespaces.
- **Sysop** needs explicit edit/create/move/upload rights once `$wgNamespaceProtection` is used.
- **Bot password format**: 32+ characters from `[0-9a-w]`; the importer checks this.
- **E-mail confirmation** applies to the bot account too; confirm its address.
- `$wgAddGroups`/`$wgRemoveGroups` only apply when `userrights` is removed from bureaucrats.

Pins: the MediaWiki tarball is pinned by SHA-256; the GPG signature was not verified yet (open item, check at the next upgrade).
