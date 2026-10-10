# PubMed Surveillance Architecture — Wikimedica

**Document version:** 1.0
**Owner:** AT Medical Digital Solutions — Engineering & Editorial
**Last updated:** 2025-01-01

---

## 1. Overview

Wikimedica operates a fully automated daily PubMed surveillance pipeline to identify newly published research relevant to the platform's content areas. The pipeline queries the NCBI Entrez API, normalises results, classifies relevance, and triggers editorial actions — all without human intervention in the data-gathering phase.

---

## 2. Daily Workflow Architecture

```text
06:00 UTC — GitHub Actions: pubmed-daily.yml
     │
     ▼
scripts/pubmed/pubmed-daily-search.py
     │
     ├── 1. Load search terms from scripts/pubmed/search-terms.yaml
     │
     ├── 2. Query NCBI Entrez API (Bio.Entrez)
     │        ├── esearch: retrieve PMIDs for each specialty query
     │        └── efetch: fetch full metadata for new PMIDs
     │
     ├── 3. Normalise metadata
     │        └── map to internal schema (see Section 6)
     │
     ├── 4. Filter: exclude already-processed PMIDs
     │        └── compare against data/pubmed/processed_pmids.txt
     │
     ├── 5. Relevance classification (stub → ML future)
     │        ├── HIGH: landmark RCTs, meta-analyses, S3 guideline updates
     │        ├── MEDIUM: observational studies, case series, narrative reviews
     │        └── LOW: editorials, letters, conference abstracts
     │
     ├── 6. Specialty mapping
     │        └── tag each record with Wikimedica specialty label(s)
     │
     ├── 7. Write output to data/pubmed/YYYY-MM-DD.jsonl
     │
     ├── 8. Append new PMIDs to data/pubmed/processed_pmids.txt
     │
     ├── 9. Commit data files to repository (GitHub Actions bot commit)
     │
     └── 10. Action dispatch
              ├── HIGH relevance → open GitHub Issue (label: pubmed-alert, priority-high)
              ├── MEDIUM relevance → log to data/pubmed/pending-review.jsonl
              └── LOW relevance → store only, no action
```

---

## 3. Search Strategy per Specialty

Search terms are maintained in `scripts/pubmed/search-terms.yaml`. Each specialty has:

- **Core terms**: high-precision MeSH terms and keywords specific to the specialty.
- **Filter terms**: study design filters (e.g., `("Randomized Controlled Trial"[pt] OR "Meta-Analysis"[pt])`).
- **Recency filter**: by default, articles published in the last 2 days are retrieved per run (adjusted for weekend gaps to cover 3 days on Monday).
- **Language filter**: no language restriction — German and English articles are included. Other languages are tagged for potential translation.

### Search Term Maintenance

- Search terms are reviewed quarterly by the Editorial Board.
- Editors may propose changes via PR to `scripts/pubmed/search-terms.yaml`.
- Changes require review by the relevant specialty editor.

---

## 4. Relevance Classification Model

### Current Implementation (Stub)

The current relevance classifier is a rule-based heuristic:

| Signal | Score Contribution |
|---|---|
| Publication type: RCT | +30 |
| Publication type: Meta-Analysis | +30 |
| Publication type: Systematic Review | +25 |
| Publication type: Clinical Trial | +20 |
| Publication type: Practice Guideline | +35 |
| Publication type: Editorial / Comment | −20 |
| Journal Impact Factor > 10 (cached list) | +15 |
| Title contains specialty keyword (exact) | +10 |
| Abstract contains patient safety term | +20 |
| Article is German-language (relevant to DE context) | +5 |

**Classification thresholds:**

- Score ≥ 60 → **HIGH**
- Score 30–59 → **MEDIUM**
- Score < 30 → **LOW**

### Future Implementation (ML)

The stub classifier is designed to be replaced with a fine-tuned classification model:

- Training data: manually labelled PubMed records from the first 6–12 months of operation.
- Model: lightweight text classifier (e.g., scikit-learn TF-IDF + LR, or a fine-tuned PubMedBERT variant).
- Deployment: Python inference within the existing script, no external API dependency.
- Feedback loop: editorial actions (issue opened, ignored, article updated) feed back into training labels.

---

## 5. Output Actions

| Relevance | Action | GitHub Label | Assigned To |
|---|---|---|---|
| HIGH | Open GitHub Issue | `pubmed-alert`, `priority-high`, specialty label | Specialty editor |
| MEDIUM | Append to pending-review.jsonl | — | Reviewed monthly by editorial team |
| LOW | Store in JSONL, no action | — | Available for retrospective queries |

### GitHub Issue Format for PubMed Alerts

Issues are created using the template `.github/ISSUE_TEMPLATE/pubmed-alert.yml`. Key fields:

- PMID and direct PubMed URL
- Article title and authors
- Abstract excerpt (first 300 characters)
- Specialty tag
- Relevance score and classification
- Suggested editorial action (e.g., "Review for update to article X")

---

## 6. Gender-Medizin as Flagship Focus

Gender-Medizin receives **expanded search coverage** relative to other specialties, reflecting its status as a flagship editorial priority:

- Additional search terms covering sex-disaggregated outcomes, gender bias in clinical trials, and sex-specific pharmacology.
- A dedicated Gender-Medizin PubMed alert queue with its own daily processing.
- Gender-relevant findings from other specialty searches are **cross-tagged** with `gender-medizin` in the specialty mapping.
- A weekly (rather than monthly) review of `MEDIUM` relevance Gender-Medizin results is performed by the Gender-Medizin editor.

See `scripts/pubmed/search-terms.yaml` for the full Gender-Medizin search term set.

---

## 7. API Integration Notes

### NCBI Entrez API

- **Base URL**: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`
- **Authentication**: API key via environment variable `NCBI_API_KEY` (stored in GitHub Actions Secrets).
- **Rate limits**: 10 requests/second with API key (vs. 3/second without).
- **Required fields on efetch**: PMID, title, abstract, authors, journal, publication date, publication types, MeSH terms.
- **Bio.Entrez module**: used via Biopython (`from Bio import Entrez`).
- **Email field**: set to `surveillance@wikimedica.de` as required by NCBI usage guidelines.

### Error Handling

- Network failures: retry up to 3 times with exponential backoff.
- API rate limit errors (429): back off 10 seconds and retry.
- Malformed responses: log warning, skip record, continue processing.
- All errors are logged to the GitHub Actions run log and to `data/pubmed/error.log`.

---

## 8. Data Normalisation Schema

Each processed PubMed record is stored as a JSON object with the following schema:

```json
{
  "pmid": "string",
  "title": "string",
  "abstract": "string",
  "authors": ["string"],
  "journal": "string",
  "year": "integer",
  "publication_types": ["string"],
  "mesh_terms": ["string"],
  "specialty_tags": ["string"],
  "relevance_score": "integer",
  "relevance_class": "HIGH | MEDIUM | LOW",
  "action_taken": "issue_opened | logged | stored",
  "github_issue_url": "string | null",
  "processed_at": "ISO 8601 timestamp",
  "source": "pubmed"
}
```

See `data/pubmed/README.md` for detailed field descriptions and retention policy.
