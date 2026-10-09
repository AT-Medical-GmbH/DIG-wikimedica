# Medical Advisor Sign-Off — Wikimedica

**Version:** 1.0
**Required for:** every article with `risk_level: high` before it can be set to `approved`.
**Attach as a comment to the pull request.**

> The Medical Advisor confirms clinical safety of the content. This does not replace peer review and
> is not a legal review.

---

## Article Information

**Article title and file:**
**Article type:** ☐ Pharmaka ☐ Therapy ☐ Professional (emergency / intensive care / oncology) ☐ Other high-risk
**Version signed off:**
**PR number:**
**Reason for `risk_level: high`:**

---

## Independence Declaration

| # | Statement | Confirmed |
|---|---|---|
| 1 | I am **not** an author of this article | ☐ |
| 2 | I have no undeclared conflict of interest regarding the substances, products or companies named | ☐ |
| 3 | I read the **final** text of the version named above | ☐ |

Declared interests (if any):

---

## Scope of Review

| # | Item | Status |
|---|---|---|
| 1 | The high-risk checklist (`high-risk-checklist.md`) is complete and every row is verified in a primary source | ☐ ✅ ☐ ❌ |
| 2 | Peer review(s) are complete and comments are resolved | ☐ ✅ ☐ ❌ |
| 3 | Dosing, thresholds and algorithms are clinically plausible and safe to publish as general information | ☐ ✅ ☐ ❌ |
| 4 | Warnings, contraindications and red flags are complete and prominent | ☐ ✅ ☐ ❌ |
| 5 | The text cannot reasonably be read as an individual treatment instruction | ☐ ✅ ☐ ❌ |
| 6 | **AI assistance:** `ai_assisted` is `____` ; if `true`, I confirm every factual statement was verified against sources by a human | ☐ ✅ ☐ ❌ ☐ N/A |
| 7 | Sex/gender cross-check is completed (`sex_gender_relevance` ≠ `not_assessed`) | ☐ ✅ ☐ ❌ |

---

## Findings and Residual Risk

**Findings:**

**Residual risks that remain (and how the text mitigates them):**

---

## Decision

- [ ] ✅ **Sign off** — clinically safe to publish as general information
- [ ] ⚠️ **Sign off after listed changes** — a new review of the changes is required
- [ ] ❌ **Do not sign off**

---

## Sign-Off

**Medical Advisor (typed name):**
**Qualification / position:**
**Date:**

After signing off, the author or editor records in the article frontmatter:

```yaml
medical_advisor: "<name above>"
medical_advisor_signoff_date: <YYYY-MM-DD>   # the date above
```

The validator rejects `approved` / `published` high-risk articles without both fields, or where the
advisor is also an author. Changing the text afterwards invalidates the sign-off: the article returns to
`in-review` and a new sign-off is needed for the new version.
