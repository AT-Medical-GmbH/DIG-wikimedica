# Go-Live Checklist — wikimedica.de

**Owner:** Management (decisions) · DevOps (technical) · **Last updated:** 2026-10-09 · **Status:** Active
Engineering cannot tick the first block; the scripts refuse production while the gated items are open.

## A. Owner decisions (blocking)

- [ ] **DEC-2 License** (entschieden: Artikel CC BY-SA 4.0, Code proprietär — siehe `docs/architecture/decision-log.md`; Umsetzung offen): decide repository licence vs. article licence (`docs/legal/license-decision-needed.md`); then set `licence` in articles/schema and align README.
- [ ] **Legal review** of `data/legal/disclaimers.yaml` → `review_status: approved` (production render of system pages and import are blocked until then).
- [ ] **Impressum / Datenschutz**: fill all placeholders in `docs/legal/page-drafts/` (production bootstrap refuses while any `REPLACE_WITH` remains); data-protection officer named.
- [ ] **DEC-1 Edge topology**, **DEC-3 Redis/search**, **DEC-4 CAPTCHA**, **DEC-5 tracking** (proposal: none), **DEC-7 backup target** decided.
- [ ] **Medical Advisor** and qualified reviewers named per specialty (`docs/editorial/roles-and-permissions.md`).

> Entscheidungen vom 2026-10-09 stehen im [Entscheidungsprotokoll](../architecture/decision-log.md); die Punkte unten sind weiterhin Gates.

## B. GitHub

- [ ] Teams from `.github/CODEOWNERS` exist (`docs/operations/github-teams-needed.md`).
- [ ] Branch protection on `main`: required review, required check `ci-ok`, no force push, tags `v*` protected.
- [ ] Environments `staging` and `production` (production: required reviewers).
- [ ] Secrets: `SSH_PRIVATE_KEY`, `SSH_HOST`, `SSH_USER`, `SSH_KNOWN_HOSTS`, `DEPLOY_PATH`, optional `SSH_PORT`;
      `WIKI_STAGING_*` and `WIKI_PRODUCTION_*` (API_URL, BOT_USER, BOT_PASSWORD); repository variable `NCBI_EMAIL`.
- [ ] PubMed workflow: commits to `main` conflict with branch protection → grant a bot exemption or switch it to pull requests.
- [ ] Dependabot alerts (1 high, 1 moderate reported on the default branch) reviewed and resolved.

## C. Server and edge

- [ ] Server provisioned, SSH hardened, firewall 80/443 only, unattended security updates.
- [ ] DNS and Cloudflare for wikimedica.de (proxy, TLS full-strict, API token for DNS-01 limited to the zone).
- [ ] `.env` complete (no `REPLACE_WITH`), permissions 600, copy in the password manager.
- [ ] Backup target configured, `BACKUP_GPG_RECIPIENT` set, private key stored offline.
- [ ] Cron entries from `docs/operations/runbook.md`; external uptime monitor and heartbeat.

## D. Proof on staging (record results)

- [ ] Acceptance test of `staging-first-deployment.md` passed.
- [ ] Restore test passed (`restore-test.sh`), date: ____
- [ ] Disaster-recovery exercise done, time taken: ____
- [ ] Importer: dry run + real import of at least one `approved` article reviewed by a human.

## E. Content

- [ ] At least the launch set of articles has passed review (`status: published`, reviewer names, Advisor for high-risk).
- [ ] No article contains dosage recommendations without Advisor review; AI assistance declared.
- [ ] Sources verified by a human; `sex_gender_relevance` assessed.

## F. Release

- [ ] Tag `v1.0.0` on `main`; production approval; deploy; health check; `bootstrap-wiki.sh --env production`;
      import `published` articles; announce.
