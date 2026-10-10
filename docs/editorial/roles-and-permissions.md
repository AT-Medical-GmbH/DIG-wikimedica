# Roles and Permissions — Wikimedica

**Document version:** 1.0
**Owner:** AT Medical Digital Solutions — Editorial Board
**Last updated:** 2026-10-09
**Status:** Active — authoritative role matrix (extends `editorial-governance.md` §2)

---

## 1. Design rule

GitHub is the **single source of truth**. Content is written, reviewed and approved in pull
requests; the MediaWiki page is a *generated view*. Therefore:

- Medical roles act on **GitHub** (pull requests, reviews, CODEOWNERS).
- MediaWiki rights are deliberately **minimal**: nobody edits article pages in the wiki by hand.
  Only the import bot (and administrators for emergencies) can write to content namespaces; a
  hand edit would be overwritten by the next import anyway.

---

## 2. Role catalogue

| # | Role | Who / qualification | GitHub (proposed team) | MediaWiki group |
|---|---|---|---|---|
| 1 | **Reader / public** | Anyone | — | `*` (read only) |
| 2 | **Registered Author** | Onboarded contributor, not yet a medical author | `medical-authors` (triage; works from branches/forks) | `user` (no edit) |
| 3 | **Medical Author** | Licensed/qualified healthcare professional, onboarded | `medical-authors` (write, PR-based) | `wm-editor` (talk pages) |
| 4 | **Reviewer** | Specialty-qualified (Facharzt or equivalent, see peer-review-policy §3); pharmacist for pharmaka | `medical-editors` | `wm-editor` |
| 5 | **Specialty Editor** | Reviewer with editorial responsibility for one specialty | `medical-editors` | `wm-editor` |
| 6 | **Gender-Medizin Editor** | Specialty Editor with Gender-Medizin qualification | `gender-medizin-editors` | `wm-editor` |
| 7 | **Editorial Board** | Leads editorial policy, templates, registries | `editorial-board` | `wm-editor` |
| 8 | **Medical Advisor** | Senior clinician; signs off high-risk content | `medical-advisors` | `wm-editor` |
| 9 | **Legal Reviewer** | Reviews consent modules, disclaimers, sourcing/copyright | `legal` | `wm-editor` |
| 10 | **DevOps** | Infrastructure, CI/CD, deployments | `devops` | `sysop` (CLI-assigned) |
| 11 | **Admin / Bureaucrat** | Owner-appointed; manages wiki accounts | `admins` | `bureaucrat`, `sysop` (CLI-assigned) |
| — | **Medical Director** *(existing role in the governance docs)* | Final clinical authority for escalations/retractions; sits in the Editorial Board | `editorial-board` | `wm-editor` |
| — | **Import bot** *(technical)* | Service account of the publishing pipeline | none (GitHub Actions secret) | `importbot` |

Team names marked "proposed" do not exist yet — see
[`docs/operations/github-teams-needed.md`](../operations/github-teams-needed.md). Nothing here
assumes they exist; CODEOWNERS is unchanged.

---

## 3. Who may do what in the lifecycle

✓ = may trigger/approve · (✓) = may trigger, approval by someone else required · — = not permitted

| Transition | Author | Reviewer | Specialty Editor | Gender Editor | Medical Advisor | Legal | Editorial Board | DevOps |
|---|---|---|---|---|---|---|---|---|
| new file → `draft` / `in-review` | ✓ | — | ✓ | ✓ | — | — | ✓ | — |
| `draft` → `in-review` | ✓ | — | ✓ | ✓ | — | — | ✓ | — |
| `in-review` → `draft` (revision) | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| `in-review` → `advisor-review` | — | — | ✓ | ✓ | — | — | ✓ | — |
| → `approved` | — | (✓) | ✓ | ✓ (gender scope) | ✓ if `risk_level: high` | ✓ for consent | ✓ | — |
| `approved` → `published` | — | — | ✓ | — | — | — | ✓ | ✓ (release/tag) |
| `published` → `in-review` | (✓) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| `published` → `archived` | — | — | ✓ | — | — | — | ✓ | — |
| `published` → `retracted` | — | — | — | — | (✓) | (✓) | ✓ (Medical Director) | — |
| set `safety_hold: true` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| clear `safety_hold` | — | — | — | — | ✓ | — | ✓ (Medical Director) | — |

**Enforcement.** The *allowed transitions* are machine-checked
(`check-status-transitions.py`). *Who* may approve is enforced by GitHub branch protection plus
CODEOWNERS (required reviews from the owning team). Both must be configured; this table is the
specification for that configuration.

---

## 4. Separation of duties

1. The author never reviews their own text; the **main author is never a reviewer**, and at least
   one reviewer is independent of all authors (validator rule).
2. The **Medical Advisor is never an author** of the article they sign off (validator rule).
3. DevOps changes infrastructure but does **not** approve medical content; the Editorial Board
   does not approve infrastructure changes. CODEOWNERS keeps the areas apart.
4. The person who clears a `safety_hold` is never the person who set it *alone* — clearing needs the
   Medical Advisor or the Medical Director.
5. Wiki administrators do not edit medical content; corrections go through GitHub.

---

## 5. MediaWiki permission model

Implemented in `infra/mediawiki/LocalSettings.example.php` (section "Roles and rights").

| Group | Rights (beyond `read`) | Assigned by |
|---|---|---|
| `*` (anonymous) | `read` only; no account creation, no editing | — |
| `user` (registered, unprivileged) | `read`; **no** edit, move, upload, create | — |
| `wm-editor` | edit **talk pages and user pages** (feedback/discussion); **not** content namespaces | bureaucrat (restricted list) |
| `wm-uploader` | `upload`, `reupload-own` | bureaucrat, case by case |
| `importbot` | `edit`, `createpage`, `wm-edit-content`, `bot`, `apihighlimits` | CLI only |
| `sysop` | standard administrator rights | CLI only (`createAndPromote.php`) |
| `bureaucrat` | may add/remove only `wm-editor` and `wm-uploader` | CLI only |

Content namespaces (Main, Template, Category, Help, Project) require the custom right
`wm-edit-content`, which only `importbot` and `sysop` hold (`$wgNamespaceProtection`).

**Staging acceptance test (required before production):** the permission model is syntax-checked in
CI but its behaviour is only provable on a running MediaWiki. On staging, verify with test
accounts — anonymous cannot edit; `user` cannot edit any namespace; `wm-editor` can edit a Talk
page but gets a permission error on a Main page; `importbot` can create/update a Main page via
the API; a bureaucrat cannot grant `sysop`; uploads work only for `wm-uploader`.

---

## 6. Joining and leaving a role

- **Joining:** application via `forms/author-application/`, onboarding per
  `docs/authors/author-onboarding-model.md`, then the Editorial Board assigns the GitHub team and
  (if needed) the wiki group. Qualifications are verified by the Editorial Board, not by the
  validator.
- **Leaving / inactivity:** team membership and wiki groups are removed on the same day; open pull
  requests are reassigned by the Specialty Editor.
- **Audit:** the Editorial Board reviews team membership and wiki groups at least once a year.
