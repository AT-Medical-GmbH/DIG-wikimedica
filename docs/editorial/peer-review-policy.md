# Review Policy — Wikimedica

**Document version:** 1.1
**Owner:** AT Medical Digital Solutions — Editorial Board
**Last updated:** 2026-10-09

---

## 1. Purpose

This document defines the mandatory peer review requirements, reviewer qualifications, turnaround standards, escalation procedures, and retraction processes for all Wikimedica content.

---

## 2. Mandatory Peer Review

All articles submitted to Wikimedica — regardless of type (professional, patient, consent module, discharge module) — **must** undergo at least one peer review before publication. There are no exceptions.

### Minimum Review Requirements by Article Type

| Article Type | Minimum Reviewers | Medical Advisor Required |
|---|---|---|
| Professional (standard, `risk_level` low/moderate) | 1 specialty reviewer | No |
| Professional (high-risk: emergency, intensive care, oncology) | 1 specialty reviewer + 1 Medical Advisor | **Yes** |
| Guideline summary | 1 specialty reviewer (+ Medical Advisor if `risk_level` high) | By risk level |
| Patient Article | 1 specialty reviewer + patient-comprehensibility review | No |
| Consent Module | 1 specialty reviewer + 1 Legal Reviewer + patient-comprehensibility review | By risk level |
| Discharge Module | 1 specialty reviewer + patient-comprehensibility review | By risk level |
| Pharmaka | 1 pharmacist reviewer + 1 specialty physician reviewer | **Yes** |
| Therapy Protocol | 1 specialty reviewer + 1 Medical Advisor | **Yes** |
| QR media reference | 1 specialty reviewer + accessibility check | No |

> **Change in v1.1:** Pharmaka moved from "recommended" to **mandatory** Medical Advisor sign-off.
> Drug dosing is a high-risk category (see Section 10), and the metadata validator now enforces
> `risk_level: high` for pharmaka. Consent and discharge modules follow their `risk_level`
> instead of a fixed rule.

### Self-Review Prohibition

A reviewer must **never be the main author** (first entry in `authors`). Co-authors may add comments, but at least one reviewer must be **independent of all authors**. The same applies to any person with a declared conflict of interest (see editorial governance document). The Medical Advisor must not be an author. These rules are enforced by `scripts/validation/validate-metadata.py` (see Section 9).

---

## 3. Specialty Reviewer Requirements

Reviewers must declare their specialty qualifications at onboarding (see `docs/authors/author-onboarding-model.md`). Review assignments are restricted to declared specialties.

A reviewer is considered **specialty-qualified** for a given article if:

1. They hold a board certification (Facharzt) or equivalent academic qualification in the relevant specialty, **or**
2. They hold a senior academic position (Oberarzt, Habilitation, or equivalent) in the specialty area, **or**
3. For cross-specialty articles (e.g., Gender-Medizin, Palliativmedizin): they hold qualification in at least one contributing specialty AND have documented experience in the cross-specialty area.

---

## 4. Turnaround Times

### Standard Targets

| Priority Level | Trigger | Target Turnaround |
|---|---|---|
| Standard | Normal new article or update | 14 calendar days |
| Elevated | New or updated guideline (AWMF/ESC/etc.) triggers content revision | 7 calendar days |
| Urgent | Patient safety concern identified | 48 hours |
| Emergency | Active safety recall / drug warning | 24 hours |

### Escalation on Timeout

If a review has not been completed within the target turnaround:

1. **Day +3 past deadline**: Automated GitHub comment on the PR notifying the assigned reviewer.
2. **Day +5 past deadline**: Editor notified via email; reviewer may be re-assigned.
3. **Day +7 past deadline**: Editor may assign a substitute reviewer and log the delay.

For **urgent and emergency** reviews: escalation to the Medical Director occurs at hour 24 (urgent) or hour 12 (emergency) if no reviewer has engaged.

---

## 5. Escalation Paths

### Clinical Uncertainty

If a reviewer identifies a clinical question that cannot be resolved with available evidence, they must:

1. Flag the specific question in the PR review comments.
2. Set article status to `in-review` (not approve).
3. Tag the relevant Medical Advisor in the PR.

The Medical Advisor has authority to:

- Resolve the question and approve.
- Request additional evidence.
- Recommend the article not be published in its current form.

### Disagreement Between Reviewers

If two reviewers disagree on a clinical point:

1. Both positions are documented in the PR comments.
2. The Editor escalates to the Medical Director.
3. The Medical Director's decision is final and documented in the PR.

### Urgent Patient Safety Concerns

If any reviewer or editor identifies a published article that may present a patient safety risk:

1. The article is immediately flagged in frontmatter with `safety_hold: true`. This is the **only** change permitted on frozen (approved/published) content without a status change, so the brake can be pulled at any time (`scripts/validation/check-status-transitions.py`).
2. The Editor notifies the Medical Director within 4 hours.
3. The Medical Director decides within 24 hours whether to retract, restrict access, or add a safety notice.
4. If retracted: see Section 8 (Retraction Process).

---

## 6. Appeal Process

### Author Appeal

An author who disagrees with a rejection decision may appeal by:

1. Submitting a written appeal to the Editorial Board (editorial@wikimedica.de) within **14 days** of the rejection notification.
2. Clearly stating the grounds for appeal and providing supporting evidence.

The Editorial Board will review the appeal within **21 days** and issue a final decision. The Medical Director may be consulted for clinical appeals.

### Reviewer Appeal

A reviewer who believes a decision was made improperly (e.g., their review was overridden without justification) may raise the matter with the Medical Director within **14 days**.

---

## 7. Stale Content Policy

Articles are considered **stale** when:

- They have not been reviewed within **12 months** of their `updated` date, **or**
- A guideline referenced in the article has been superseded, **or**
- A PubMed surveillance alert of **high relevance** has been logged against the article topic and not actioned within **30 days**.

### Stale Content Process

1. **Automated detection**: `scripts/review/generate-review-report.py` flags stale articles monthly.
2. **GitHub Issue created**: An issue is opened with label `stale-content` and assigned to the article's original author.
3. **Author response**: The author must either update the article or confirm it remains current within **30 days**.
4. **No response**: The Editor assigns a new reviewer; the issue is labelled `needs-update`. Published content is frozen, so staleness is tracked through the issue and the monthly review report, **not** by editing the frontmatter.
5. **Unresolvable staleness**: Article is archived with a notice explaining the circumstances.

---

## 8. Retraction Process

Retraction is a serious editorial action reserved for articles where:

- Clinically significant factual errors were published.
- A conflict of interest was concealed by the author.
- The content presents a patient safety risk that cannot be corrected in place.
- Plagiarism or copyright violation is confirmed.

### Steps

1. **Decision**: Medical Director issues written retraction order.
2. **Immediate action**: Article `status` is set to `retracted` and the public retraction notice is recorded in the frontmatter field `retraction_notice` (mandatory for this status; no patient or confidential data).
3. **MediaWiki**: The page is replaced with a retraction notice that explains the reason without identifying patients or confidential information.
4. **Archive**: The file stays in the repository with status `retracted`; the original text remains in the Git history. Deleting approved/published articles is blocked by the lifecycle guard.
5. **Notification**: Authors and reviewers of the retracted article are notified in writing.
6. **Public notice**: A retraction notice is published on the Wikimedica editorial blog (future).
7. **Registry**: The retraction is logged in the internal editorial registry (Nextcloud).

Retracted articles are **never** republished without a complete re-authoring and full review cycle.

---

## 9. Machine-Enforced Rules and Their Limits

The following rules are checked automatically on every pull request. A failing check blocks the merge.

| Rule | Enforced by |
|---|---|
| Reviewer is not the main author; at least one reviewer independent of all authors | `validate-metadata.py` |
| High risk ⇒ Medical Advisor name **and** sign-off date; advisor is not an author | `validate-metadata.py` |
| Pharmaka, therapy, emergency, intensive care, oncology ⇒ `risk_level: high` | `validate-metadata.py` (lists in `data/metadata/article-schema.yaml`) |
| AI assistance declared (`ai_assisted`) and described | `validate-metadata.py` |
| Sex/gender cross-check completed before approval | `validate-metadata.py` |
| `reviewers`, `next_review`, `license`, `change_summary`, `source_notes` and a source before approval | `validate-metadata.py` |
| Allowed status transitions; new articles start as draft/in-review; approved/published content is frozen | `check-status-transitions.py` |
| Required sections present as headings; no leftover comments/TODOs | `pre-publish-check.py` |

**What the machine cannot verify:** whether a reviewer is really specialty-qualified, whether a name
in the metadata is the person who actually reviewed, and whether the medical content is correct.
The validator compares names as text. Authority comes from GitHub: branch protection must require
approvals from the CODEOWNERS teams (see `docs/operations/github-teams-needed.md`), and the reviewer
confirms qualification and independence in the sign-off form.

---

## 10. High-Risk Content

**High risk** means an error can directly harm a patient. It covers pharmaka, therapy protocols,
emergency medicine, intensive care and oncology. The lists live in `data/metadata/article-schema.yaml`
(`risk:`); extending them is a reviewed change by the Editorial Board.

Additional requirements for `risk_level: high`:

1. Medical Advisor sign-off, recorded with `medical_advisor` and `medical_advisor_signoff_date`
   (form: `forms/editorial-review/medical-advisor-signoff.md`).
2. Every dose, threshold and contraindication is checked against a primary source (current
   Fachinformation or guideline) and recorded in `forms/reviewer-checklists/high-risk-checklist.md`.
3. Dosing information always carries its source and its date ("Stand").
4. Pharmaka: a pharmacist **and** a physician review the text.

---

## 11. Patient Content

Patient-facing text (patient articles, consent and discharge modules, QR media) gets a **separate**
comprehensibility review (`forms/reviewer-checklists/patient-comprehensibility-checklist.md`) in
addition to the medical review.

- Patient text is **general information**, never an individual medical instruction: no personal
  dosing, no "Nehmen Sie … ein / Setzen Sie … ab" phrasing for an individual case.
- The validator warns about such phrasing, dosages and low readability (Flesch-Amstad below 50).
  These warnings are aids for the reviewer, **not** a pass/fail comprehension test.
- Patient and professional content stay separate (`target_audience`, `article_type`, own categories);
  link them through `related_professional_article`.
- A section "Wann sofort zum Arzt?" and the automatic emergency notice are mandatory for patient-facing types.

---

## 12. Sex/Gender Cross-Check (Gender-Medizin)

Gender-Medizin is the flagship focus. **Every** article is assessed for sex- and gender-specific
aspects before approval and records the result in `sex_gender_relevance`
(`none` or `relevant`; `not_assessed` blocks approval). For `relevant`, `sex_gender_notes`
summarises the aspects. Articles in the specialty Gender-Medizin must be `relevant`.

The assessment follows `forms/reviewer-checklists/gender-medizin-checklist.md`. Articles marked
`relevant` outside the Gender-Medizin directory are reviewed by a Gender-Medizin Editor on request
of the Specialty Editor, because CODEOWNERS can only match paths, not metadata.

---

## 13. Change History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2025-01-01 | Initial policy |
| 1.1 | 2026-10-09 | Moved from `docs/governance/`; Pharmaka and therapy require a Medical Advisor; reviewer independence rules; machine-enforced rules; high-risk, patient-content and sex/gender sections; retraction field; stale marking via issue label |
