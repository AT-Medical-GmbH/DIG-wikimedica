# Content Lifecycle — Wikimedica

**Document version:** 1.0
**Owner:** AT Medical Digital Solutions — Editorial Operations
**Last updated:** 2026-10-09
**Document version (revised):** 1.1

---

## 1. Overview

This document describes the complete lifecycle of a Wikimedica article — from initial proposal through drafting, review, publication, ongoing maintenance, and eventual archival. It also defines the versioning model, update triggers, content scoring approach, and quality metrics.

---

## 2. Lifecycle Stages

```text
PROPOSAL
    │  GitHub Issue: new-article template
    ▼
TRIAGE
    │  Editor assigns specialty, priority, author
    ▼
DRAFTING
    │  Author creates PR using content template
    │  Status: draft
    ▼
PEER REVIEW
    │  Assigned reviewer(s) evaluate content
    │  Status: in-review
    │
    ├──[needs revision]──► DRAFTING (revision cycle)
    │
    └──[approved by reviewer]──►
EDITORIAL REVIEW
    │  Editor checks compliance, metadata, sourcing
    │  Status: in-review (editor stage)
    │
    ├──[needs revision]──► DRAFTING
    │
    └──[editor approved]──►
MEDICAL ADVISOR REVIEW (high-risk only)
    │  Advisor sign-off for clinical safety
    │  Status: advisor-review
    │
    └──[advisor approved]──►
APPROVED
    │  PR merged to main
    │  Status: approved
    ▼
PUBLICATION
    │  Import script pushes to MediaWiki (scripts/publishing/import_to_mediawiki.py, Phase 4)
    │  Status: published
    ▼
MAINTENANCE
    │  Ongoing monitoring for staleness / update triggers
    │
    ├──[update trigger]──► DRAFTING (update PR)
    │
    └──[archival trigger]──►
ARCHIVED
    │  Status: archived
    │  Content preserved in Git history
```

---

## 2a. Formal Status Transitions

The `status` field is the single source of truth for the lifecycle position. Only the transitions
below are allowed; `scripts/validation/check-status-transitions.py` compares every pull request with
`main` and rejects anything else. The table is defined in `data/metadata/article-schema.yaml`
(`lifecycle.transitions`).

| From | To | Condition |
|---|---|---|
| *(new file)* | `draft` / `in-review` | A new article can never enter the repository as `approved` or `published` |
| `draft` | `in-review` | Author requests review; `change_summary` filled |
| `in-review` | `draft` | Revision requested |
| `in-review` | `advisor-review` | High-risk content after peer review |
| `in-review` / `advisor-review` | `approved` | All required reviews passed; `reviewers`, `next_review`, `license`, `source_notes` set; high risk ⇒ advisor sign-off |
| `advisor-review` | `in-review` / `draft` | Advisor requests changes |
| `approved` | `published` | Release/import step (never directly from `draft` or `in-review`) |
| `approved` | `in-review` | Re-opened before publication |
| `published` | `in-review` | **Update needed** (guideline change, PubMed alert, correction); bump the version |
| `published` | `archived` | Superseded or obsolete content |
| `published` | `retracted` | Retraction process; `retraction_notice` mandatory |
| `archived`, `retracted` | — | Terminal |

**Frozen content.** Once an article is `approved` or `published`, its text and metadata cannot change
while the status stays the same — the sign-off covered exactly that text. Any edit starts with
`published → in-review` (or `approved → in-review`). **Exception:** `safety_hold` can be set or
cleared at any time (patient-safety brake, see the peer-review policy).

**Never deleted, never renamed.** Approved/published articles are archived or retracted, not
deleted. The file name is the slug and is immutable; moving a file to another directory with the
same file name is permitted.

---

## 3. Versioning Model

Articles use **semantic versioning** (`MAJOR.MINOR.PATCH`):

| Change Type | Version Bump | Review Required |
|---|---|---|
| Typographical / formatting fix | PATCH (x.x.1) | No (Editor only) |
| New references, minor factual additions | MINOR (x.1.0) | Peer review |
| New sections, significant clinical updates | MINOR (x.1.0) | Peer review |
| Complete rewrite, major guideline-driven revision | MAJOR (1.0.0 → 2.0.0) | Full review cycle |
| Retraction of incorrect clinical information | MAJOR | Medical Advisor sign-off |

Version history is tracked in Git commit history. The current version is always present in the `version` field of the article frontmatter.

---

## 4. Update Triggers

An article may enter a new revision cycle for the following reasons:

### 4.1 Guideline Update

- A guideline referenced in the article has been updated or superseded.
- Detected via: monthly guideline registry review (`scripts/reporting/monthly-guideline-report.py`).
- Response: the published article moves `published → in-review` in an update PR (version bump).
- Response time: 30 days (high priority) or next quarterly cycle (standard priority), per AMPIS score.

### 4.2 PubMed Alert

- A PubMed surveillance alert of `HIGH` or `MEDIUM` relevance has been generated for the article's topic.
- Detected via: daily PubMed surveillance (`scripts/pubmed/pubmed-daily-search.py`).
- Response time: 7 days (HIGH), 30 days (MEDIUM).

### 4.3 Editorial Flag

- An editor or reviewer identifies an inaccuracy, safety concern, or significant gap in published content.
- Any Wikimedica contributor or reader (via the MediaWiki "report issue" function, future) can flag content for review.
- An immediate review is triggered when a safety concern is raised.

### 4.4 Stale Detection

- Article has not been reviewed in 12 months.
- Detected via: `scripts/review/generate-review-report.py` (monthly run).
- Response: GitHub Issue opened; author notified with 30-day response window.

### 4.5 External Report

- Reader, patient, or third-party organisation reports an error.
- All external reports are triaged by the Editorial Board within 5 business days.

---

## 5. Archival Policy

An article is archived when:

- It has been **superseded** by a more comprehensive or updated version.
- The clinical topic is **no longer relevant** (withdrawn procedure, obsolete diagnosis).
- The content was **retracted** due to clinical error or copyright violation.
- The article has been **inactive for 24 months** with no update activity despite automated prompts.

### Archival Process

1. Editor changes `status` to `archived` in frontmatter.
2. The file **stays at its path** (the slug is immutable; moving it would break links and history).
3. MediaWiki page is updated with an archival notice pointing to any replacement article.
4. Git history is preserved; content is never deleted from the repository.

---

## 6. Content Scoring

Every published article is assigned a **Content Quality Score (CQS)** — a composite indicator used to prioritise editorial review and identify articles needing improvement.

### CQS Dimensions

| Dimension | Weight | Description |
|---|---|---|
| Completeness | 25% | All required frontmatter fields and sections present |
| Reference Quality | 25% | Proportion of claims backed by S3/S2 guidelines or RCTs |
| Currency | 20% | Days since last review (normalised; penalises staleness) |
| Review Depth | 15% | Number of distinct qualified reviewers |
| Readability | 15% | Flesch-Kincaid or equivalent score (appropriate to article type) |

CQS is calculated by `scripts/review/generate-review-report.py` and reported in the monthly review dashboard.

---

## 7. Quality Metrics

The Editorial Board tracks the following platform-level quality metrics:

| Metric | Target | Measurement Frequency |
|---|---|---|
| % articles with `published` status that are current (not stale) | ≥ 90% | Monthly |
| Average review turnaround time (standard) | ≤ 14 days | Monthly |
| % articles with ≥ 2 reviewers | ≥ 60% | Quarterly |
| % high-risk articles with Medical Advisor sign-off | 100% | Monthly |
| PubMed HIGH alerts actioned within 7 days | ≥ 80% | Monthly |
| Guideline updates reflected within 30 days (high priority) | ≥ 90% | Monthly |
| Author CoI declarations up to date | 100% | Annually |

These metrics are reported in the annual editorial report and used to inform resource allocation and process improvements.
