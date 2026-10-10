# GitHub Teams Needed — Wikimedica

**Document version:** 1.0
**Owner:** AT Medical Digital Solutions — DevOps / Editorial Board
**Last updated:** 2026-10-09
**Status:** Active — **action required by the GitHub organisation owner**

---

## 1. Finding

`.github/CODEOWNERS` assigns every path to teams of the form `@atmedical-wikimedica/<team>`.
The repository, however, lives in the organisation **`AT-Medical-GmbH`**.

Checked on 2026-10-09 through the GitHub API (teams visible to the session's credentials):

| Organisation | Teams found |
|---|---|
| `AT-Medical-GmbH` | `atmed-core-engineering`, `atmed-platform-team`, `atmed-infrastructure`, `atmed-devops`, `atmed-digital-systems`, `atmed-core-systems` |
| `AT-Digital-Systems-GmbH` | none visible |

**None of the teams referenced in CODEOWNERS was found.** The list only shows teams visible to the
credentials used, so a team in another organisation cannot be ruled out — the owner should confirm.

**Why this matters.** GitHub silently ignores invalid CODEOWNERS entries. If these teams do not
exist, "required review by code owners" protects **nothing**: medical content, infrastructure and
legal documents can be merged without the reviewers the governance documents promise.

**Not changed.** Per the handover rule, the team names in CODEOWNERS were **not** edited blindly.
This document specifies what has to exist; afterwards one reviewed change aligns CODEOWNERS.

---

## 2. Teams referenced today (CODEOWNERS)

| Referenced team | Purpose | Exists? |
|---|---|---|
| `@atmedical-wikimedica/editors` | default owner for everything | not found |
| `@atmedical-wikimedica/editorial-board` | docs, templates, registries, forms, PubMed scripts | not found |
| `@atmedical-wikimedica/medical-editors` | all medical content | not found |
| `@atmedical-wikimedica/gender-medizin-editors` | `content/specialties/gender-medizin/` | not found |
| `@atmedical-wikimedica/legal` | `docs/legal/` | not found |
| `@atmedical-wikimedica/devops` | infra, workflows, scripts | not found (closest existing: `AT-Medical-GmbH/atmed-devops`) |

## 3. Additional teams required by the role model

See `docs/editorial/roles-and-permissions.md`.

| Proposed team | Purpose | Needed for |
|---|---|---|
| `medical-advisors` | Sign-off of high-risk content | CODEOWNERS for `content/pharmaka/`, `content/therapies/`; required reviewer when `risk_level: high` |
| `medical-authors` | Onboarded authors | Triage/write access to open pull requests |
| `admins` | Repository and wiki administration | Repository admin, branch-protection exceptions |

## 4. Decision for the organisation owner 🧭

Choose **one**:

- **A — Create the missing teams** in `AT-Medical-GmbH` (recommended names: `wikimedica-editors`,
  `wikimedica-editorial-board`, `wikimedica-medical-editors`, `wikimedica-gender-medizin-editors`,
  `wikimedica-legal`, `wikimedica-medical-advisors`, `wikimedica-medical-authors`) and reuse
  `atmed-devops` for DevOps. Then update CODEOWNERS to `@AT-Medical-GmbH/<team>`.
- **B — Use an organisation `atmedical-wikimedica`** if it exists or is intended; then the existing
  names stay and the teams must be created there (and the repository would need to be reachable for them).

Teams from other organisations can only own paths if they have **write access** to the repository.

## 5. Required team rights

| Team | Repository permission | Notes |
|---|---|---|
| editorial-board, medical-editors, gender-medizin-editors, medical-advisors, legal | Write | Review/approve via pull requests |
| medical-authors | Triage or Write | Work on branches; no direct push to `main` |
| devops | Write; **Maintain** for Actions/environments | Owns workflows and the `production` environment |
| admins | Admin | Rare; protected by 2FA |

## 6. Branch protection for `main` (to be configured by an admin)

- Require a pull request before merging; **no direct pushes**, including administrators.
- Require approvals: **≥ 1**, and **≥ 2 for `content/**`** (see peer-review-policy; a ruleset can enforce this per path).
- **Require review from Code Owners.**
- Dismiss stale approvals when new commits are pushed (sign-off covers one exact text).
- Require status checks: metadata validation, markdown lint, link check, spelling, compose validation,
  security scan, tests (Phase 4 wires these into one required workflow).
- Require conversation resolution; require linear history; block force pushes and deletions.
- Restrict who can create release tags `v*.*.*` to `devops`/`editorial-board`; the `production`
  environment requires manual approval by a named reviewer.

## 7. After the teams exist

1. Add the members; enforce 2FA for the organisation.
2. Update CODEOWNERS in one pull request and verify GitHub shows **no "unknown owner" warnings**
   on the file.
3. Open a test pull request touching `content/` and check that the expected team is requested.
