# AT Medical Publication Impact Score (AMPIS) — Wikimedica

This directory contains the specification, calibration data, and scoring outputs for the **AT Medical Publication Impact Score (AMPIS)** — a composite metric used to prioritise editorial updates in response to new publications and guideline changes.

---

## Concept

The AMPIS quantifies the editorial relevance and urgency of a new publication or guideline update relative to Wikimedica's existing content. A high AMPIS score triggers immediate editorial action; a low score results in the publication being logged for periodic review.

The AMPIS is calculated by the PubMed surveillance pipeline and the monthly guideline review script.

---

## Scoring Dimensions

AMPIS is composed of four weighted dimensions, each scored 0–100, combined into a weighted average to produce a final AMPIS score of 0–100.

### Dimension 1: Clinical Relevance (Weight: 30%)

Assesses how directly the publication affects clinical management decisions.

| Criterion | Score |
|---|---|
| Changes first-line treatment recommendation | 90–100 |
| Changes diagnostic criteria or algorithm | 80–90 |
| Provides major safety information (new contraindication, serious ADR) | 85–95 |
| Provides new efficacy data that modifies existing guidance | 60–80 |
| Adds supporting evidence for existing guidance | 30–60 |
| Background / epidemiological data only | 10–30 |
| Not directly clinically actionable | 0–10 |

### Dimension 2: Evidence Quality (Weight: 25%)

Based on study design and guideline level:

| Evidence Type | Score |
|---|---|
| S3 guideline update (AWMF) / Class I ESC recommendation | 90–100 |
| Large RCT (n > 1000), pre-registered, relevant endpoint | 80–90 |
| Meta-analysis with low heterogeneity (I² < 50%) | 75–85 |
| S2k/S2e guideline | 65–75 |
| Smaller RCT or high-quality cohort study | 50–65 |
| S1 guideline / expert consensus | 40–55 |
| Observational study, registry data | 25–40 |
| Case series, expert opinion, narrative review | 5–25 |

### Dimension 3: Update Urgency (Weight: 25%)

Measures how much the new publication changes currently published Wikimedica content.

| Scenario | Score |
|---|---|
| Current article contradicts the new evidence | 90–100 |
| Current article is silent on a newly-established recommendation | 70–90 |
| Current article requires significant additions | 50–70 |
| Minor additions or cross-references needed | 20–50 |
| No change to article content required | 0–20 |

### Dimension 4: Specialty Coverage (Weight: 20%)

Measures how broadly relevant the publication is across Wikimedica specialties.

| Scope | Score |
|---|---|
| Directly relevant to ≥ 4 Wikimedica specialties | 80–100 |
| Directly relevant to 2–3 specialties | 50–80 |
| Directly relevant to 1 specialty | 20–50 |
| Cross-specialty relevance only marginal | 0–20 |

---

## Scoring Formula

```text
AMPIS = (Clinical_Relevance × 0.30) +
        (Evidence_Quality   × 0.25) +
        (Update_Urgency     × 0.25) +
        (Specialty_Coverage × 0.20)
```

AMPIS values range from **0** (no editorial relevance) to **100** (maximum urgency).

---

## Priority Action Thresholds

| AMPIS Score | Priority | Editorial Action |
|---|---|---|
| 80–100 | Critical | Immediate alert; article update within 7 days |
| 60–79 | High | GitHub Issue opened; update within 30 days |
| 40–59 | Medium | Added to quarterly review queue |
| 20–39 | Low | Logged in pending-review.jsonl; reviewed monthly |
| 0–19 | Minimal | Stored in data/pubmed; no action |

---

## Current Implementation Status

The current AMPIS implementation in `scripts/pubmed/pubmed-daily-search.py` is a **stub** that approximates the score using proxy signals available from PubMed metadata (publication type, journal, title keywords). The full scoring rubric above requires editorial input that is not always available from API data alone.

**Planned improvements:**

1. **Semi-automated scoring**: Editorial team provides dimension scores for HIGH-relevance records via a GitHub issue comment command (e.g., `/score clinical=85 evidence=90 urgency=70 coverage=40`).
2. **ML-assisted scoring**: Train a model on manually scored records to predict AMPIS scores automatically.
3. **Guideline integration**: Automatically pull guideline level from AWMF registry API when available.

---

## Use in Prioritisation

AMPIS scores are used in:

- `scripts/pubmed/pubmed-daily-search.py`: classifies each PubMed record and dispatches actions.
- `scripts/reporting/monthly-guideline-report.py`: orders guidelines for review by urgency.
- Monthly editorial dashboard (future): visualises content update queue sorted by AMPIS.
