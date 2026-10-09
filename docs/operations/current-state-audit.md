# Current-State Audit — Wikimedica

**Document version:** 1.0
**Owner:** AT Medical Digital Solutions — Engineering / DevOps
**Last updated:** 2026-10-09
**Status:** Active — baseline for the production-readiness programme

---

## 1. Purpose and scope

This document is the evidence-based baseline ("Bestandsaufnahme") of the
`AT-Medical-GmbH/DIG-wikimedica` repository at the start of the
production-readiness programme. It records **what exists today**, **in which
state**, and **which gaps block production readiness** — without changing any
code. It is the factual foundation for
[`docs/architecture/production-readiness-concept.md`](../architecture/production-readiness-concept.md),
which defines the target state and the remediation roadmap.

Everything below was verified directly against the working tree on branch
`claude/wikimedica-production-readiness-bks0x1` (default branch `main`,
PR #1 already merged). No assumptions were made about files that were not read.

> **Scope boundary.** Wikimedica is the **public / public-facing medical
> knowledge backbone** of the Digital-Solutions line. It is explicitly **not**
> the internal `ATMED-wiki`, not BookStack, and not internal company
> documentation. MediGuard is a separate system (Wikimedica *explains*;
> MediGuard *evaluates in context*). This audit only prepares interfaces to
> MediGuard, it does not pull MediGuard functionality into Wikimedica.

---

## 2. Method

- Full file inventory of the working tree (excluding `.git/` and the
  `data/pubmed/` result harvest).
- Direct read of all infrastructure, configuration, schema, governance and
  automation entry-point files.
- Cross-check of the repository against the handover requirements and the
  20 acceptance criteria.
- Severity rating per finding: **S1 blocker** (prevents a safe production
  deployment), **S2 major** (significant risk or missing capability),
  **S3 minor** (correctness/quality), **S4 decision** (owner decision required,
  not a technical defect).

---

## 3. Repository inventory

### 3.1 Top-level layout (verified present)

```text
content/         articles, consent-modules, discharge-modules, drafts,
                 patient-info, pharmaka, published, review-queue,
                 specialties/ (+ gender-medizin/), templates/, therapies/
data/            metadata/ (article-schema.yaml), registries/
                 (guideline-registry.yaml), pubmed/ (41 JSONL harvests),
                 media/, queries/, scoring/, sources/
docs/            architecture, authors, consent, deployment, editorial,
                 governance, guidelines, legal, operations, pubmed
forms/           author-application, editorial-review, reviewer-checklists
infra/           deploy/ (deploy.sh, rollback.sh, backup.sh), docker/
                 (compose + override), env/ (.env.example),
                 mediawiki/ (LocalSettings.example.php),
                 traefik/ (traefik.yml, dynamic/middlewares.yml)
scripts/         publishing/ (pre-publish-check.py), pubmed/
                 (pubmed-daily-search.py, search-terms.yaml),
                 reporting/ (monthly-guideline-report.py),
                 review/ (generate-review-report.py),
                 validation/ (validate-metadata.py)
.github/         CODEOWNERS, ISSUE_TEMPLATE/ (4), PULL_REQUEST_TEMPLATE,
                 workflows/ (9)
root             README.md, LICENSE, CONTRIBUTING.md, CODE_OF_CONDUCT.md,
                 .gitignore, .cspell.json, .markdownlint.json
```

The scaffold is **substantially complete and coherent** — this is a real
backbone, not an empty skeleton. The automation scripts total ~1,860 lines of
Python and ~530 lines of shell; the governance/architecture docs are written
and consistent in house style.

### 3.2 GitHub Actions workflows (9, all present)

| Workflow | Purpose | First-read assessment |
|---|---|---|
| `markdown-lint.yml` | Markdown lint | Present |
| `metadata-validation.yml` | Frontmatter schema validation | Present, wired to `validate-metadata.py` |
| `link-check.yml` | Link checking | Present |
| `spelling-check.yml` | cspell | Present (`.cspell.json` exists) |
| `pr-label-enforcement.yml` | PR label gate | Present (130 lines) |
| `pubmed-daily.yml` | Daily PubMed surveillance | Present; actively committing results |
| `pubmed-editorial-routing.yml` | Route PubMed hits to issues | Present |
| `guideline-review-reminder.yml` | Monthly guideline review | Present |
| `deploy.yml` | Deploy on version tag | Present; **gaps — see §5.4** |

Observed runtime evidence: `data/pubmed/` holds 41 daily JSONL harvests and the
commit log shows `chore(pubmed): daily surveillance results …` up to
2026-05-21, i.e. the daily surveillance has demonstrably run.

**Missing vs. handover workflow list:** no Docker Compose validation workflow,
no security-scan workflow, and no pre-publish (publishing dry-run) workflow.

---

## 4. Legal / licensing status

### 4.1 Finding L1 — README license contradiction **[S1 / S4]**

`LICENSE` is present and unambiguous:

> *AT Medical Proprietary Source-Available License v1.0 — Copyright (c) 2026
> AT Medical GmbH. All rights reserved.*

`README.md`, however, is internally contradictory. It was assembled from **two
different drafts** and contains:

- **Two** `# Wikimedica` titles, two "License", two "Contributing" sections.
- One block (README §License) stating content is **CC BY-SA 4.0** and code is
  "© AT Medical Digital Solutions, all rights reserved".
- Another block stating the **whole repository** is under the **AT Medical
  Proprietary Source-Available License v1.0** and explicitly that adaptation /
  redistribution is not allowed.
- `article-schema.yaml` additionally defaults the per-article `licence` field
  to `CC BY-SA 4.0`.

This is a genuine, externally visible defect on a public repository: the stated
license depends on which paragraph a reader stops at. Per handover rule, the
existing `LICENSE` is **not** changed by engineering; the conflict is escalated
as an owner decision (see
[`docs/legal/license-decision-needed.md`](../legal/license-decision-needed.md))
and the README is de-duplicated to stop asserting a license that contradicts
`LICENSE` until the decision is made.

### 4.2 Finding L2 — `CONTRIBUTING.md` / `CODE_OF_CONDUCT.md` are stubs **[S3]**

- `CONTRIBUTING.md` — 4 lines, no contributor process.
- `CODE_OF_CONDUCT.md` — 1 line: *"See DIG-mediguard CODE_OF_CONDUCT standard."*
  A cross-repo pointer is not a usable CoC for a public repository.

### 4.3 Finding L3 — legal docs incomplete **[S2]**

`docs/legal/copyright-and-sourcing-policy.md` exists. **Missing:**
`docs/legal/medical-disclaimer.md`, `docs/legal/privacy-notes.md`, and a
license-decision record. A public medical platform must not launch without a
clearly visible medical disclaimer, emergency notice, and privacy/Impressum
statement.

---

## 5. Infrastructure status

### 5.1 Finding I1 — MediaWiki pinned to an unsupported version **[S1]**

`infra/docker/docker-compose.yml:49` → `image: mediawiki:1.42`.
MediaWiki 1.42 is a standard (non-LTS) release and is **end-of-life**. Target
is **MediaWiki 1.43 LTS** (rationale in
[`docs/architecture/version-policy.md`](../architecture/version-policy.md)).

### 5.2 Finding I2 — `LocalSettings.example.php` does not match a 1.43 target **[S1]**

Concrete technical defects in the example config:

1. **Obsolete external Parsoid block.**
   `$wgVirtualRestConfig['modules']['parsoid'] = [... 'url' => 'http://localhost:8142' ...]`
   describes the legacy standalone-Parsoid/RESTBase setup. Since MW 1.35 Parsoid
   ships **inside core** and VisualEditor uses it directly; this block is wrong
   for 1.43 and would misconfigure VisualEditor.
2. **Invented variable.** `$wgRevisionStoreType = 'FileStore';` is **not a real
   MediaWiki setting** and has no effect (dead/misleading config).
3. **Deprecated CDN variables.** `$wgUseSquid` / `$wgSquidServers` were replaced
   by `$wgUseCdn` / `$wgCdnServers` (deprecated since 1.34).
4. **Variable-ordering bug.** `$wgFileCacheDirectory = "{$wgUploadDirectory}/cache";`
   references `$wgUploadDirectory` ~8 lines **before** it is defined → resolves
   to `/cache`.
5. **No object cache / job queue backend** (handover asks to evaluate Redis),
   no `CirrusSearch`, no `AbuseFilter` / `SpamBlacklist`, and upload hardening
   for `svg`/`pdf`/`webp` is enabled without the MIME/SVG safety settings that
   must accompany it.

The file is otherwise sound on the important security posture: anonymous
`createaccount=false`, anonymous `edit=false`, `read=true`, email-confirm-to-edit,
production error suppression.

### 5.3 Finding I3 — Compose files **[S2/S3]**

- `version: "3.9"` is obsolete under Compose v2 (ignored, emits a warning) — S3.
- Only `docker-compose.yml` + `docker-compose.override.yml` exist. There is
  **no explicit staging vs. production split** and **no
  `docker-compose.gateway-target.yml`** for the ATINFRA central-gateway model
  named in the handover — S2.
- `internal_net` is correctly `internal: true`; MariaDB uses `expose` (not
  `ports`) — DB is **not** publicly reachable (good).
- The MediaWiki healthcheck uses `curl` inside the official `mediawiki` image,
  which does **not** ship `curl` by default — the healthcheck likely never
  passes as written (S2, verify on build).

### 5.4 Finding I4 — `deploy.yml` workflow gaps **[S2]**

The workflow triggers correctly (tags `v*.*.*` + manual dispatch, `production`
environment) and handles the SSH key safely (writes, `chmod 600`, cleans up with
`if: always()`). Gaps:

- Secret **naming mismatch**: workflow uses `VPS_HOST` / `VPS_USER`; handover
  specifies `SSH_HOST` / `SSH_USER` / `SSH_PORT` / `DEPLOY_PATH`. `SSH_PORT`
  and `DEPLOY_PATH` are unused (path `/opt/wikimedica` is hard-coded).
- **No backup-before-deploy** step, **no post-deploy healthcheck gate**, and
  **no rollback-on-failure / failure-issue** step in the workflow itself
  (the *script* does health-check — see I5 — but the workflow does not react).

### 5.5 Finding I5 — deploy scripts are good but have defects **[S2/S3]**

- `deploy.sh` (212 lines) is genuinely capable: arg parsing, `git fetch --tags`,
  tag checkout, `docker compose pull/up`, a 12×10s health-check loop, and
  Healthchecks.io ping hooks. **But it has no `#!/usr/bin/env bash` shebang**
  (starts with a comment) — a portability/shellcheck defect (S3) — and its
  health-check/rollback outcome is not surfaced back to CI (S2).
- `backup.sh` (182 lines) dumps DB + images, rotates by `BACKUP_RETAIN_DAYS`,
  supports S3/SFTP. **Rotation is daily-only**; handover requires
  7 daily / 4 weekly / 3 monthly (S2).
- `rollback.sh` (137 lines) present with pre-flight checks.
- A **restore script is missing** entirely (S2) — "restore is more important
  than backup".

### 5.6 Finding I6 — `.env.example` nearly complete, some secrets missing **[S2]**

Present and well-documented: domain, DB creds, MW secret/upgrade/admin,
Traefik ACME + Cloudflare token + zone, NCBI key/email, GitHub token/repo,
S3 + SFTP backup, healthcheck + alert email. **Missing vs. deploy needs:**
`SSH_PRIVATE_KEY`, `SSH_HOST`, `SSH_USER`, `SSH_PORT`, `DEPLOY_PATH`, and a
full **SMTP** block (host/port/user/pass/from) for MediaWiki mail. Backup
retention only exposes `BACKUP_RETAIN_DAYS` (no weekly/monthly knobs).

---

## 6. Content model & governance status

### 6.1 Finding C1 — schema is strong but missing mandatory fields **[S2]**

`data/metadata/article-schema.yaml` is rich and the validator
(`validate-metadata.py`, 346 lines) is a real, working, cross-field validator
(semver, date sanity, published-needs-reviewer, consent-needs-procedure,
`wikimedica_credit` must be true). The **26 specialties are present and exact**,
Gender-Medizin included.

**Missing vs. the handover's mandatory metadata list:** `slug`,
`ai_assistance_description`, `references`, `source_notes`,
`risk_level` (only a `safety_hold` bool exists — there is **no risk
classification**), `target_audience` (schema has `language_level` instead),
`change_summary`, and a dedicated **sex/gender-relevance** field for the
flagship cross-cutting review.

Minor: schema key is `licence` (British) while handover uses `license`; the
status enum is a superset (`advisor-review`, `retracted` added) that should be
reconciled with the documented lifecycle.

### 6.2 Finding C2 — content templates incomplete **[S2]**

Present: `article-professional.md`, `article-patient.md`, `consent-module.md`,
`discharge-module.md`. **Missing templates** named in the handover:
**Pharmaka**, **Therapy protocol**, **Guideline summary**, **QR media
reference**.

### 6.3 Finding C3 — governance docs present, some missing **[S2]**

Present: editorial-governance, review-policy (governance/), content-lifecycle
(operations/), author-onboarding-model, modular-consent-system,
guideline-priority-program, pubmed-surveillance-architecture; forms for author
application, editorial sign-off, medical review checklist.
**Missing:** `docs/editorial/ai-assistance-policy.md`,
`docs/editorial/peer-review-policy.md` (a `governance/review-policy.md` exists —
reconcile naming), and the reviewer-checklist set is a single file (no
patient-comprehensibility or gender-lens checklists).

### 6.4 Finding C4 — publishing pipeline GitHub → MediaWiki is absent **[S1]**

This is the most important functional gap. `scripts/publishing/` contains only
`pre-publish-check.py` (357 lines, a gate). There is **no**
`scripts/publishing/import_to_mediawiki.py` — i.e. no Markdown→Wikitext
conversion, no MediaWiki API import, no dry-run/staging/production modes, no
auto-generated category/infobox/reference/version/disclaimer blocks, no import
log. The core "GitHub content → MediaWiki publication" capability (acceptance
criterion #12) does not yet exist.

---

## 7. Automation status (PubMed / guidelines)

- `pubmed-daily-search.py` (578 lines) + `search-terms.yaml` exist and the
  pipeline **demonstrably runs** (41 harvests committed). Needs verification of:
  NCBI key handling + rate-limit/backoff, controlled skip when the key is
  absent, dedup, relevance classification (README says "stub"), and legal
  storage boundary (metadata/PMIDs only, no unlawful abstract redistribution).
- `monthly-guideline-report.py` (304 lines) + `guideline-registry.yaml` exist;
  registry is real (AWMF/NVL entries). Needs a verification run.
- `generate-review-report.py` (278 lines) exists for review-due reporting.

These are **S2 "verify and harden"**, not "build from scratch".

---

## 8. Missing documents (handover-required, not yet present)

`SECURITY.md`, `docs/architecture/version-policy.md`,
`docs/deployment/staging-first-deployment.md`,
`docs/operations/runbook.md`, `docs/operations/maintenance.md`,
`docs/operations/update-policy.md`, `docs/operations/security-response.md`,
`docs/operations/backup-restore-runbook.md`,
`docs/operations/disaster-recovery.md`,
`docs/operations/github-teams-needed.md`,
`docs/editorial/ai-assistance-policy.md`,
`docs/legal/medical-disclaimer.md`, `docs/legal/privacy-notes.md`,
`docs/legal/license-decision-needed.md`, and this `current-state-audit.md`
(now created).

---

## 9. Readiness scorecard against the 20 acceptance criteria

| # | Criterion | State | Severity |
|---|---|---|---|
| 1 | Repo inventory documented | **Done** (this doc) | — |
| 2 | MediaWiki on supported version | Not met (1.42) | S1 |
| 3 | Compose staging+production ready | Partial | S2 |
| 4 | LocalSettings matches MW version | Not met | S1 |
| 5 | No secrets in repo | **Met** (placeholders only; `.gitignore` excludes `.env`) | — |
| 6 | `.env.example` complete | Partial (SSH/SMTP missing) | S2 |
| 7 | Actions run or skip cleanly | Partial (verify skip-without-secrets) | S2 |
| 8 | Content schema validated | **Met** (works) / extend fields | S2 |
| 9 | Templates complete | Partial (4 of 8) | S2 |
| 10 | PubMed surveillance robust | Partial (runs; harden) | S2 |
| 11 | Guideline review prepared | **Mostly met** (verify) | S2 |
| 12 | Publishing pipeline ≥ dry-run | **Not met** (no importer) | S1 |
| 13 | Deployment via release tag | Partial (workflow gaps) | S2 |
| 14 | Backup/restore prepared | Partial (no restore, no w/m rotation) | S2 |
| 15 | Rollback prepared | **Mostly met** (verify) | S2 |
| 16 | Monitoring hooks documented | Partial (hooks exist; undocumented) | S2 |
| 17 | Security concept + partial impl | Partial | S2 |
| 18 | Editorial governance traceable | **Mostly met** | S3 |
| 19 | License conflict resolved/recorded | Not met (contradiction live) | S1/S4 |
| 20 | Clean PR | Pending | — |

**S1 blockers:** MediaWiki version (#2/#4), publishing pipeline (#12), license
contradiction (#19). These define the critical path.

---

## 10. Conclusion

The repository is a **credible, well-structured backbone** with working
validation, a running PubMed pipeline, capable deploy/rollback scripts, and
coherent governance. It is **not yet production-ready** because of three
blockers (unsupported MediaWiki version + mismatched config, the missing
GitHub→MediaWiki publishing pipeline, and the live license contradiction) plus
a set of S2 hardening and documentation gaps.

The remediation plan, target architecture, and the explicit separation of
**engineering tasks vs. owner decisions vs. real secrets** are defined in
[`docs/architecture/production-readiness-concept.md`](../architecture/production-readiness-concept.md).
