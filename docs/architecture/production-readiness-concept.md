# Production-Readiness Concept — Wikimedica

**Document version:** 1.0
**Owner:** AT Medical Digital Solutions — Engineering / DevOps / Editorial Board
**Last updated:** 2026-10-09
**Status:** Active — master concept for bringing `DIG-wikimedica` to production readiness
**Companion baseline:** [`docs/operations/current-state-audit.md`](../operations/current-state-audit.md)

---

## 0. How to read this document

This is the **master concept** for making Wikimedica (`wikimedica.de`)
technically, structurally, editorially and operationally production-ready. It
is grounded in the evidence-based audit (companion document) and translates the
handover into a target architecture plus an executable roadmap.

Every item in this concept is explicitly classified into one of three buckets,
because they must never be mixed:

- 🛠️ **ENG — Engineering task.** Directly solvable in-repo, staging-first, by
  Claude / the DevOps team. No external decision needed.
- 🧭 **DEC — Owner decision.** Deliberately left open for AT Medical GmbH
  (Andreas Tremml / Editorial Board / Legal). Engineering prepares options,
  does not decide.
- 🔑 **SEC — Real secret / credential.** A value that must **not** be invented.
  Documented as a named placeholder; the owner supplies the real value via
  GitHub Secrets or server-side `.env`.

> **Non-negotiable guard-rails** (from handover + ATMED governance):
> staging-first; no secrets in the repo; no invented production credentials; no
> blind live-server installs; AI may assist but never autonomously publishes
> medical content; human + qualified-reviewer sign-off before publication;
> high-risk content needs a Medical Advisor; Wikimedica *explains*, MediGuard
> *evaluates* — only prepare interfaces, do not build MediGuard features here.

---

## 1. Product vision (target)

Wikimedica is a modular, evidence-aware **public German-language medical
knowledge platform** on MediaWiki, with AT-Medical-specific content governance,
GitHub-based quality assurance, automated literature surveillance, and
controlled, auditable deployment.

**Audiences:** physicians · nurses · emergency/prehospital · pharmacists · other
medical professionals · patients · relatives · clinical teams needing
structured patient information, consent and discharge modules.

**Core content areas:** diseases · therapies · pharmaka · guideline summaries ·
professional articles · patient-friendly explanations · modular consent
(*Aufklärungsbögen*) · discharge & aftercare · wound-care instructions ·
QR-linked media · audio/video/FAQ modules · clinic-brandable output ·
(prospective) structured interfaces to MediGuard.

**Flagship:** Gender-Medizin as a cross-cutting editorial priority (own
category, expanded surveillance, mandatory gender-lens review of every
professional article, dedicated metadata).

---

## 2. Target architecture

### 2.1 Logical layers

```
 GitHub (single source of truth)
   content/ docs/ data/ scripts/ infra/  ──►  CI (GitHub Actions)
                                                │
                     ┌──────────────────────────┴───────────────────────┐
                     │ validate → lint → link → spell → metadata →       │
                     │ compose-config → security-scan → publish dry-run  │
                     └──────────────────────────┬───────────────────────┘
                                                │ (only on release tag vX.Y.Z)
                                                ▼
   Cloudflare (DNS · WAF · CDN · DDoS)  ──►  Edge/Reverse proxy  ──►  MediaWiki 1.43 LTS
                                                                      ├─ MariaDB 10.11+ (internal only)
                                                                      ├─ Redis (object cache + job queue) [eval]
                                                                      └─ OpenSearch + CirrusSearch [eval, scale]
                                                 Publishing: scripts/publishing/import_to_mediawiki.py
                                                 (Markdown+YAML → Wikitext via MediaWiki API)
```

### 2.2 Edge / reverse-proxy decision 🧭 **DEC-1**

Two supported topologies; pick one before production:

- **(A) Self-contained Traefik** (current `docker-compose.yml`): Wikimedica
  owns ports 80/443 on its own VPS. Keep as the default for an isolated host.
- **(B) ATINFRA central gateway** (`ATINFRA-gateway`): a central reverse proxy
  already terminates TLS and routes ingress. Running a second public Traefik
  next to it is wrong. For this case 🛠️ **ENG** provides
  `infra/docker/docker-compose.gateway-target.yml` that exposes only the app
  port internally and documents the gateway route — no second public Traefik.

Engineering prepares **both** compose variants; the owner chooses the topology
(and supplies the target host/alias 🔑 **SEC**).

### 2.3 Technology pins (target)

| Component | Target | Note |
|---|---|---|
| MediaWiki | **1.43 LTS**, pinned by digest | see `version-policy.md` |
| MariaDB | 10.11 LTS (pinned) | internal-only network |
| PHP | as bundled in `mediawiki:1.43` image | do not override blindly |
| Traefik | v3.x pinned | topology (A) only |
| Redis | 7.x pinned | 🧭 object cache / job queue, eval |
| OpenSearch | 2.x pinned | 🧭 CirrusSearch, scale-dependent |
| Docker Compose | v2 (no `version:` key) | staging + production files |

**Principle:** pin every image (prefer digest), never `latest`.

---

## 3. MediaWiki configuration (target)

Rationale and upgrade path live in
[`docs/architecture/version-policy.md`](version-policy.md). Summary of the
corrections the example config needs (see audit I2):

- **VisualEditor:** remove the legacy external-Parsoid `$wgVirtualRestConfig`
  block. On 1.43 Parsoid ships in core; `wfLoadExtension('VisualEditor')` +
  `$wgVisualEditorEnableWikitext` is sufficient. No standalone Parsoid service.
- **Remove invented setting** `$wgRevisionStoreType`.
- **CDN:** replace `$wgUseSquid`/`$wgSquidServers` with `$wgUseCdn = true;` and
  `$wgCdnServersNoPurge`/`$wgCdnServers` as appropriate for Cloudflare.
- **Fix ordering** so `$wgUploadDirectory` is defined before it is used.
- **Skins:** Vector 2022 (default) + MinervaNeue (mobile).
- **Extensions:** WikiEditor, VisualEditor, Cite, ParserFunctions,
  TemplateStyles, CategoryTree, SyntaxHighlight, Echo, TitleBlacklist,
  ConfirmEdit (+ a maintainable CAPTCHA — reCAPTCHA today; 🧭 evaluate hCaptcha
  as a privacy-friendlier alternative), and 🧭 AbuseFilter / SpamBlacklist /
  Lockdown as needed.
- **Uploads hardening:** keep `svg`/`pdf`/`webp` **only** with
  `$wgSVGConverter`, `$wgAllowTitlesInSVG=false`, strict
  `$wgMimeTypeExclusions`/`$wgVerifyMimeType`, `$wgTrustedMediaFormats`, and
  antivirus hook where available.
- **Object cache / job queue:** 🧭 add Redis (`$wgMainCacheType=CACHE_REDIS`,
  `$wgObjectCaches`, `$wgJobTypeConf`) once Redis is approved; otherwise keep
  APCu + DB and run jobs via `runJobs.php` cron.
- **Access posture (keep as-is, it is correct):** anonymous `createaccount`
  off, anonymous `edit` off, `read` on, email-confirm-to-edit on, production
  error suppression on.
- **Mail:** wire `$wgSMTP` from the new SMTP env block (🔑 **SEC**).

**Staging-vs-production config:** `LocalSettings.php` is generated from `.env`
on the server and is never committed with real values; the repo only carries
`LocalSettings.example.php`.

---

## 4. Infrastructure & deployment (target)

### 4.1 Compose 🛠️ **ENG**

- Drop obsolete `version:` key.
- Base `docker-compose.yml` (production) + `docker-compose.override.yml` (local
  dev) + a dedicated staging file + `docker-compose.gateway-target.yml` (DEC-1 B).
- Healthchecks that actually work: MediaWiki image lacks `curl` — use
  `php-fpm`/`wget`-free check (e.g. MediaWiki's own healthcheck endpoint via
  the proxy, or add a tiny healthcheck tool to the image build). Verify on
  staging.
- Persistent volumes for DB, images, certs, backups; DB strictly on the
  `internal: true` network (already correct).

### 4.2 GitHub-driven deployment 🛠️ **ENG**

- Deploy **only** on release tags `vX.Y.Z` on `main` (never per-commit, never
  from PRs) — already the trigger; keep it.
- Harmonise secret names to the handover set (`SSH_PRIVATE_KEY`, `SSH_HOST`,
  `SSH_USER`, `SSH_PORT`, `DEPLOY_PATH`); stop hard-coding `/opt/wikimedica`.
- Deployment sequence the workflow must enforce:
  `backup → pull/up → health-check → (on fail) rollback + open failure issue`.
  The `deploy.sh` script already health-checks; the **workflow** must gate on
  its exit status and trigger `rollback.sh` + a GitHub issue / job summary.
- Add shebang to `deploy.sh`; run `shellcheck` in CI on all deploy scripts.

### 4.3 Backup / restore 🛠️ **ENG** (restore first)

- Extend `backup.sh` rotation to **7 daily / 4 weekly / 3 monthly**.
- Add a **restore script** (DB + images + non-secret config) — this is the
  priority; "restore matters more than backup".
- Targets: local + S3-compatible and/or SFTP (🔑 **SEC** credentials).
- Runbooks: `backup-restore-runbook.md`, `disaster-recovery.md`; a **monthly
  restore test in staging** as a documented, scheduled procedure.

### 4.4 Monitoring hooks 🛠️ **ENG (document) / 🧭 (tooling choice)**

Document health endpoints, Docker healthchecks, Traefik access logs, MediaWiki
error logs, MariaDB health, backup status, cert status, job-queue/`runJobs`
status. 🧭 choose Uptime Kuma / Prometheus / `ntfy` as the external monitor;
the `.env` already exposes `HEALTHCHECK_URL` + `ALERT_EMAIL` hooks.

---

## 5. Security concept

- HTTPS-only, HSTS, security headers (Traefik `middlewares.yml` already exists —
  extend with a CSP tuned not to break MediaWiki/VisualEditor), rate limiting,
  Cloudflare WAF-compatible.
- No anonymous editing; public read only; registration disabled/moderated;
  editing only for approved, email-confirmed users; restrictive
  admin/bureaucrat and upload rights; MIME + SVG checks.
- Store **no patient data**; no sensitive logs.
- Legal surfaces: medical disclaimer, emergency notice, privacy/Impressum,
  cookie/tracking decision (🧭 **DEC** — documented, default: no non-essential
  tracking).
- CI: add a secret-scanning / dependency / compose-config security job that
  **fails clearly** rather than silently.
- `SECURITY.md` with a coordinated-disclosure contact.

---

## 6. Content model & editorial governance

### 6.1 Schema extensions 🛠️ **ENG**

Add the missing mandatory fields to `article-schema.yaml` and the validator:
`slug`, `ai_assistance_description`, `references`, `source_notes`,
**`risk_level`** (enum: `low|moderate|high` — high ⇒ Medical-Advisor sign-off),
`target_audience`, `change_summary`, and **`sex_gender_relevance`** (gender-lens
field). Reconcile `licence`→`license` spelling and the status enum against the
documented lifecycle. Keep the strong existing validator; extend its cross-field
rules (e.g. high `risk_level` ⇒ `medical_advisor` required; patient articles ⇒
comprehensibility checklist reference).

### 6.2 Lifecycle & roles (target, already largely documented)

`draft → in-review → approved → published → archived`
(+ `advisor-review`, `retracted` as needed; `published → in-review` on update).
Rules: AI assistance must be declared; reviewer ≠ lead author; high-risk
(pharmaka/dosing/emergency/oncology/intensive) needs Medical-Advisor sign-off;
patient content gets a separate comprehensibility review and must not read like
individual medical instruction.

Roles: Reader · Registered Author · Medical Author · Reviewer · Specialty
Editor · Gender-Medizin Editor · Editorial Board · Medical Advisor · Legal
Reviewer · DevOps · Admin/Bureaucrat.

### 6.3 Templates 🛠️ **ENG**

Add the four missing templates (**Pharmaka**, **Therapy protocol**, **Guideline
summary**, **QR media reference**) to match the four existing ones. Every
template carries: YAML frontmatter · heading structure · references section ·
review history · change log · disclaimer fields · audience marker · risk
classification · review-due date.

### 6.4 AI-assistance policy 🛠️ **ENG**

Create `docs/editorial/ai-assistance-policy.md`: AI may draft/support;
disclosure mandatory (`ai_assisted` + `ai_assistance_description`); no
autonomous publication; full human + qualified-reviewer review remains
mandatory; no unlawful ingestion of protected full texts.

### 6.5 CODEOWNERS / teams 🧭 **DEC / 🛠️ ENG**

Content ⇒ medical reviewers; Gender-Medizin ⇒ gender editor group; infra ⇒
DevOps; legal ⇒ Legal/Editorial Board; PubMed scripts ⇒ DevOps + Editorial;
templates ⇒ Editorial Board; Actions ⇒ DevOps. If the GitHub teams do not exist
or names are wrong, **do not guess** — list the required team names + rights in
`docs/operations/github-teams-needed.md` (🧭 owner creates teams; then 🛠️ ENG
wires CODEOWNERS + branch protection).

---

## 7. Publishing pipeline GitHub → MediaWiki (critical path)

The core missing capability. 🛠️ **ENG** build `scripts/publishing/import_to_mediawiki.py`:

- Parse Markdown + YAML frontmatter; validate against schema; enforce status
  gate (**only `approved`/`published`** may be published).
- Convert Markdown → MediaWiki Wikitext.
- Auto-generate: categories from specialty; metadata/infobox; literature/PMID
  section; version box; disclaimers; audience marker.
- Idempotent import via MediaWiki API with a **bot account / API auth**
  (🔑 **SEC** bot credentials), `--dry-run`, `--env staging|production`,
  `--status`, `--release-tag`. Import log + failure report as GitHub issue /
  job summary.
- Production import **only** via release tag; staging import for approved
  content.

CLI contract (as per handover):

```
python scripts/publishing/import_to_mediawiki.py --env staging --dry-run
python scripts/publishing/import_to_mediawiki.py --env staging --status approved
python scripts/publishing/import_to_mediawiki.py --env production --status published --release-tag vX.Y.Z
```

**Acceptance for criterion #12:** a working **dry-run** that parses, validates,
converts and reports without writing to MediaWiki.

---

## 8. Literature & guideline surveillance

- **PubMed** (`pubmed-daily-search.py` + `search-terms.yaml`): harden NCBI key
  handling (controlled skip / reduced mode when 🔑 `NCBI_API_KEY` is absent),
  rate-limit + retry/backoff, tool/email params, dedup, relevance
  classification, specialty mapping, expanded Gender-Medizin terms. Legal
  boundary: store **metadata/PMIDs/links only**, never redistribute abstracts
  unlawfully. Routing: high ⇒ issue, medium ⇒ monthly, low ⇒ stored.
- **Guidelines** (`guideline-registry.yaml` + `monthly-guideline-report.py`):
  AWMF/ESC/society tracking, per-article `next_review`, monthly review issue,
  auto-flag stale articles.

Both exist and run — scope is **verify + harden**, documented in
`docs/pubmed/pubmed-surveillance-architecture.md` and
`docs/guidelines/guideline-priority-program.md`.

---

## 9. Tests / validation 🛠️ **ENG**

Python tests for scripts; metadata schema validation (exists) + sample-article
fixtures; publishing dry-run test; link checker; markdown + YAML lint; compose
`config` validation; `LocalSettings` PHP `-l` syntax check; `shellcheck` for
deploy scripts; backup-script dry-run; restore-doc test. All CI jobs must
**skip cleanly with a clear message** when a secret is absent — never fail
opaquely; PubMed runs in reduced mode without a key; deploy runs only on tags.

---

## 10. Legal 🧭 **DEC** (prepared, not decided)

`LICENSE` exists (AT Medical Proprietary Source-Available v1.0) and is **not
changed** by engineering. The README contradiction (audit L1) is recorded in
[`docs/legal/license-decision-needed.md`](../legal/license-decision-needed.md)
with three options:

1. **AT Medical Proprietary Source-Available License v1.0** for everything.
2. **Apache-2.0 for code + CC BY-SA 4.0 for content.**
3. **Split model:** code proprietary/source-available, content CC BY-SA /
   CC BY-NC-SA.

Default stance for production prep: **grant no rights away; no open-source
switch without an owner decision.** Engineering de-duplicates the README so it
stops asserting a license that contradicts `LICENSE` until DEC is made, and
adds `medical-disclaimer.md` + `privacy-notes.md`.

---

## 11. Roadmap (phased, staging-first)

| Phase | Theme | Key deliverables | Blockers cleared |
|---|---|---|---|
| **1 Audit** | Baseline | current-state-audit.md ✅, this concept ✅, license-decision-needed.md, version-policy.md | — |
| **2 Version & infra** | Stabilise core | MW 1.43 pin, corrected LocalSettings.example, Parsoid fix, Redis/search eval, compose split + gateway variant, `.env.example` completion (SSH/SMTP/rotation) | #2 #4 |
| **3 Governance & content** | Quality system | schema field extensions, 4 missing templates, ai-assistance-policy, reviewer checklists (patient + gender), disclaimers, teams-needed doc | #8 #9 |
| **4 Automation** | Make it move | `import_to_mediawiki.py` dry-run, PubMed/guideline hardening, compose-config + security + pre-publish CI jobs, clean-skip behaviour | #12 #10 #11 #7 |
| **5 Deploy readiness** | Operate safely | staging-first doc, deploy workflow gating (backup→health→rollback→issue), restore script + runbooks, monitoring + security docs, final PR | #13 #14 #15 #16 #17 |

Each phase is committed in coherent, reviewable commits on
`claude/wikimedica-production-readiness-bks0x1`, verified on staging where
possible, with nothing experimental left on production systems.

---

## 12. Open owner decisions (consolidated) 🧭

| ID | Decision | Default if unanswered |
|---|---|---|
| DEC-1 | Edge topology: own Traefik vs. ATINFRA gateway | Prepare both; owner picks |
| DEC-2 | License model (3 options) | Keep proprietary; no rights granted |
| DEC-3 | Redis + CirrusSearch/OpenSearch now or later | APCu+DB + MySQL search until scale needs it |
| DEC-4 | CAPTCHA: reCAPTCHA vs. hCaptcha/alternative | Keep configurable; recommend hCaptcha |
| DEC-5 | Cookie/tracking posture | No non-essential tracking |
| DEC-6 | GitHub team names & membership | Document needs; owner creates teams |
| DEC-7 | Backup target (S3 vs. SFTP vs. both) | Support both; owner supplies creds |

## 13. Required real secrets (consolidated) 🔑

Never invented; supplied via GitHub Secrets / server `.env`:
`SSH_PRIVATE_KEY`, `SSH_HOST`, `SSH_USER`, `SSH_PORT`, `DEPLOY_PATH`,
`CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ZONE_ID`, `TRAEFIK_ACME_EMAIL`,
`MEDIAWIKI_DB_PASSWORD`, `MEDIAWIKI_DB_ROOT_PASSWORD`, `MEDIAWIKI_SECRET_KEY`,
`MEDIAWIKI_UPGRADE_KEY`, `MEDIAWIKI_ADMIN_PASS`, MediaWiki **bot** API
credentials, `NCBI_API_KEY`, SMTP host/port/user/pass/from, and the backup
target credentials (S3 and/or SFTP). Real target server, IP, SSH alias,
Cloudflare zone and domain parameters are owner-supplied; until then the repo
uses documented placeholders only.

---

## 14. Known risks

- MediaWiki major-version upgrade can break extensions/skins — mitigated by
  staging-first + a documented upgrade/rollback path (`version-policy.md`).
- VisualEditor/Parsoid misconfiguration is the most common 1.43 pitfall —
  addressed by removing the legacy external-Parsoid block.
- Publishing pipeline must never leak unapproved content — enforced by the
  status gate + release-tag-only production import.
- Legal exposure from the live license contradiction — contained by the README
  de-duplication + the recorded decision.
- Medical-safety: no autonomous AI publication; high-risk content gated on a
  Medical Advisor.

---

## 15. Next steps

Proceed with **Phase 2** (version & infra stabilisation) staging-first, in
reviewable commits, followed by Phases 3–5, keeping the three-bucket separation
(ENG / DEC / SEC) intact and surfacing every owner decision rather than guessing.
