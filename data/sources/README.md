# Source Tracking — Wikimedica

This directory maintains records of external sources registered for use in Wikimedica content. Source tracking ensures transparency, copyright compliance, and systematic quality monitoring.

---

## Purpose

Every external source referenced in a Wikimedica article must be registered here if it is used beyond a simple PMID citation. This includes: guidelines, textbooks, databases, and any source subject to specific licence or copyright restrictions.

---

## Source Registration

### How to Register a Source

1. Add an entry to the appropriate YAML file in this directory (see file structure below).
2. Include all required fields (see schema below).
3. Submit via Pull Request to `main`.
4. An editor will review the source registration for copyright compliance.

### File Structure

```text
data/sources/
├── README.md             ← this file
├── guidelines.yaml       ← Clinical guidelines (AWMF, ESC, NICE, etc.)
├── databases.yaml        ← Databases (PubMed, Cochrane, etc.)
├── textbooks.yaml        ← Textbooks and reference works
├── proprietary.yaml      ← Proprietary sources (DocCheck, UpToDate) — rights-cleared only
└── rights-cleared/       ← Documented permissions for third-party content use
```

---

## Reference Types

| Type | Examples | Usage Policy |
|---|---|---|
| Peer-reviewed journal article | PubMed records | Cite PMID; no text reproduction without rights check |
| Clinical guideline (AWMF) | AWMF S3/S2k/S1 guidelines | Short quotation with attribution; no full-text reproduction |
| Clinical guideline (international) | ESC, NICE, SIGN | As above |
| Systematic review / Cochrane | Cochrane Reviews | Cite DOI/PMID; no reproduction beyond short quotation |
| Textbook | Harrison's, Herold, Pschyrembel | Reference only; no reproduction |
| Proprietary database | DocCheck Flexikon, UpToDate, Amboss | Background research only; no reproduction unless rights-cleared |
| Drug prescribing information | Fachinformation | Dosing data may be paraphrased with attribution |
| Government / public health | RKI, STIKO, WHO | Link and attribute; check licence for reproduction |

---

## DocCheck / UpToDate Policy

These proprietary sources are subject to strict restrictions. See `docs/legal/copyright-and-sourcing-policy.md` for the full policy.

In summary:

- **DocCheck Flexikon**: Reference (link) only; no reproduction.
- **UpToDate**: Background research only; no reproduction of any content.
- **Amboss**: Background research only; no reproduction.

Any author who believes that specific content from these sources has been rights-cleared for reproduction in Wikimedica must provide documentation in `data/sources/rights-cleared/`.

---

## AWMF Guideline References

AWMF guidelines are cited using the following format:

```yaml
- id: "awmf-019-013"
  title: "Nationale VersorgungsLeitlinie Herzinsuffizienz"
  issuer: "AWMF / DEGAM / DGK"
  awmf_register: "019-013"
  guideline_level: "S3"
  year: 2023
  version: "4.0"
  url: "https://www.awmf.org/leitlinien/detail/ll/019-013.html"
  usage: "citation_and_short_quotation"
  copyright_cleared: false
```

---

## Source Quality Scoring

Sources are assessed for quality using the following dimensions:

| Dimension | Description | Score (1–5) |
|---|---|---|
| Evidence quality | Level of evidence (RCT, meta-analysis, observational, expert opinion) | 1–5 |
| Currency | How recently was this source published or updated? | 1–5 |
| Issuer authority | Issuer's standing (major learned society, peer-reviewed journal, etc.) | 1–5 |
| German-context relevance | Applicability to German healthcare system and population | 1–5 |
| Accessibility | Is the full source freely accessible? | 1–5 |

Source quality scores inform the evidence grading in articles and are used by the PubMed surveillance pipeline's relevance classifier.
