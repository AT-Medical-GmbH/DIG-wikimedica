# High-Risk Content Checklist (Source Verification) — Wikimedica

**Version:** 1.0
**Use for:** every article with `risk_level: high` — pharmaka, therapy protocols, emergency medicine,
intensive care, oncology (list: `data/metadata/article-schema.yaml`, section `risk`).
**Reviewers:** specialty reviewer, pharmacist (pharmaka) and the Medical Advisor.

> **Rule:** a dose, threshold, interval or contraindication is only "verified" if a person has read it
> in the **primary source** (current Fachinformation, guideline or protocol) and written down where.
> A statement checked only against another secondary text, or against an AI answer, is **not verified**.

---

## Article Information

**Article title and file:**
**PR number:**
**Version under review:**
**AI-assisted (frontmatter):** ☐ no ☐ yes → verify **every** factual statement below, not a sample.

---

## Section 1: Statement-by-statement verification

List every dose, threshold, interval, maximum, duration and contraindication in the article.

| # | Statement in the article (section) | Value | Primary source (title) | Edition / Stand | Location (chapter/page) | Checked by | ✅/❌ |
|---|---|---|---|---|---|---|---|
| 1 | | | | | | | |
| 2 | | | | | | | |
| 3 | | | | | | | |

Add rows as needed. Every row needs a source and a Stand.

---

## Section 2: Typical error sources

| # | Check | Status | Notes |
|---|---|---|---|
| 2.1 | Units are correct and consistent (mg vs. µg vs. mg/kg; per dose vs. per day) | ☐ ✅ ☐ ❌ | |
| 2.2 | Decimal separators and orders of magnitude cannot be misread | ☐ ✅ ☐ ❌ | |
| 2.3 | Maximum single and daily doses are stated | ☐ ✅ ☐ ❌ ☐ N/A | |
| 2.4 | Dose adjustment for kidney and liver impairment and for age is present and sourced | ☐ ✅ ☐ ❌ ☐ N/A | |
| 2.5 | Paediatric statements are weight- or age-based and sourced; none extrapolated from adult data | ☐ ✅ ☐ ❌ ☐ N/A | |
| 2.6 | Pregnancy and lactation are addressed | ☐ ✅ ☐ ❌ ☐ N/A | |
| 2.7 | Relevant interactions and contraindications are complete | ☐ ✅ ☐ ❌ ☐ N/A | |
| 2.8 | Off-label use is clearly labelled and the evidence level is stated | ☐ ✅ ☐ ❌ ☐ N/A | |
| 2.9 | Look-alike / sound-alike drug names cannot be confused in the text | ☐ ✅ ☐ ❌ ☐ N/A | |
| 2.10 | Sex-specific dosing or adverse-effect information from the source is included | ☐ ✅ ☐ ❌ ☐ N/A | |

## Section 3: Category-specific checks

| # | Check | Status | Notes |
|---|---|---|---|
| 3.1 | **Emergency:** time-critical algorithm matches the current guideline step by step; no step omitted | ☐ ✅ ☐ ❌ ☐ N/A | |
| 3.2 | **Intensive care:** thresholds, targets and monitoring parameters match the cited guideline | ☐ ✅ ☐ ❌ ☐ N/A | |
| 3.3 | **Oncology:** regimen names, cycle lengths and dose modifications match the cited protocol or guideline | ☐ ✅ ☐ ❌ ☐ N/A | |
| 3.4 | **Pharmaka:** approval status (DE/EU) and Stand of the Fachinformation are stated | ☐ ✅ ☐ ❌ ☐ N/A | |
| 3.5 | **Therapy:** scope and local-adaptation note present; no instruction that requires an individual decision is presented as universal | ☐ ✅ ☐ ❌ ☐ N/A | |

## Section 4: Decision

- [ ] ✅ All statements verified in primary sources — ready for Medical Advisor sign-off
- [ ] ⚠️ Corrections required (list above), re-check needed
- [ ] ❌ Not publishable in its current form

**Reviewer (typed name and role):**
**Date:**

Attach to the pull request. The Medical Advisor then completes
`forms/editorial-review/medical-advisor-signoff.md`.
