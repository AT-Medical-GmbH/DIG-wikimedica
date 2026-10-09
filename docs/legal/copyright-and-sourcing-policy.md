# Copyright and Sourcing Policy — Wikimedica

**Document version:** 1.0
**Owner:** AT Medical Digital Solutions — Legal & Editorial
**Last updated:** 2025-01-01

---

## 1. Purpose

This policy governs the use of third-party content, the sourcing and attribution of references, and the licensing of Wikimedica's own published content. All contributors, reviewers, and editors must read and comply with this policy.

---

## 2. Fundamental Principle: Independent Authorship

**Wikimedica articles must be independently authored.** This means:

- Articles are written from scratch by qualified medical authors.
- The structure, language, and formulation are original, even when drawing on the same underlying evidence.
- No article may be a paraphrase, reformatting, or systematic restatement of any copyrighted text from a third-party source.

This principle applies regardless of whether the source is a proprietary database (DocCheck, UpToDate, Amboss), a textbook, a journal article, or another wiki.

---

## 3. Use of Third-Party Sources

### 3.1 What Is Permitted

- **Citing** published peer-reviewed articles (PMIDs) as references.
- **Citing** named clinical guidelines (AWMF, ESC, DGK, DGN, DGHO, RKI, etc.) by title, issuer, and URL.
- **Paraphrasing factual content** (e.g., diagnostic criteria from ICD-10/DSM-5) using independent language, with full attribution.
- **Quoting short passages** (1–3 sentences) from copyrighted sources where legally permissible under German copyright law (§ 51 UrhG — Zitatrecht), provided the quote is identified, attributed, and serves a specific commentary or explanatory purpose.

### 3.2 What Is Not Permitted

- **Copying substantial text** from DocCheck Flexikon, UpToDate, Amboss, MSD Manual, Pschyrembel, or any other proprietary medical reference without documented rights clearance.
- **Screen-scraping or automated extraction** of copyrighted content from any source.
- **Republishing Wikipedia or Wikidata content** without complying with the CC BY-SA licence terms (attribution + ShareAlike).
- **Republishing journal abstracts or full text** beyond what PubMed's terms of service and the publisher's licence permit.
- **Republishing guideline full text** beyond short quotation unless the guideline issuer has granted explicit permission or released the text under a free licence.

### 3.3 DocCheck and UpToDate

These are proprietary databases with specific licence restrictions:

- **DocCheck Flexikon**: Content is licenced under a proprietary DocCheck licence, not Creative Commons. Content may be **referenced** (linked) but not reproduced.
- **UpToDate**: All content is fully proprietary. UpToDate may only be used as a **background research source** for factual orientation. No text, tables, figures, or structured data from UpToDate may appear in Wikimedica articles.

If an institution holds an UpToDate or DocCheck licence, individual authors may use these tools as research aids, but the resulting article text must be original.

### 3.4 AWMF Guidelines

AWMF (Arbeitsgemeinschaft der Wissenschaftlichen Medizinischen Fachgesellschaften) guidelines are published under varying licence conditions:

- Many AWMF guidelines are freely accessible but **not** under a free licence. Full-text reproduction is not permitted without written authorisation.
- Short quotes (diagnostic criteria, recommendation grades, key recommendations) may be reproduced under § 51 UrhG with full attribution (guideline title, AWMF register number, version, URL).
- Always link directly to the AWMF guideline registry entry.

---

## 4. Rights Clearance Process

If an author wishes to include content from a third-party source that would not normally be permissible under the policies above, they must:

1. Submit a written rights clearance request to editorial@wikimedica.de before including the content in a draft.
2. Provide: the source, the specific content to be reproduced, and the intended use.
3. The Editorial team contacts the rights holder and obtains written permission.
4. Permission documentation is stored in the internal rights register (Nextcloud).
5. Only upon documented permission may the content be included.

---

## 5. Attribution Model

### In-Text Citations

All factual claims requiring attribution should use numbered in-text citations (e.g., `[1]`), with full references listed in the article's **References** section. Use the following reference format:

**Journal article:**
> Mustermann M, Schmidt A. Titel des Artikels. *Zeitschrift für Medizin*. 2024;42(3):100–110. PMID: 12345678.

**Guideline:**
> Deutsche Gesellschaft für Kardiologie (DGK). ESC Leitlinie: Akutes Koronarsyndrom. AWMF-Register Nr. 019-013. Version 2023. URL: https://www.awmf.org/...

**Book:**
> Autor A. *Buchtitel*, 5. Auflage. Verlag, 2023. S. 200–210.

### YAML Frontmatter Attribution

PubMed IDs and guideline references are also recorded in the article YAML frontmatter (fields `pubmed_ids` and `guidelines`) to enable automated cross-referencing and update tracking.

---

## 6. Licensing of Wikimedica Content

### Original Content

Articles, patient information, consent modules, and discharge modules **authored for Wikimedica** are published under the **Creative Commons Attribution–ShareAlike 4.0 International Licence** ([CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)).

This means:

- **Attribution (BY)**: Anyone reproducing Wikimedica content must credit "Wikimedica / AT Medical Digital Solutions" with a link to the original.
- **ShareAlike (SA)**: Any adapted or derived works must be distributed under the same CC BY-SA 4.0 licence.
- Commercial use is permitted under these terms.

### Clinic-Branded Consent and Discharge Modules

Consent and discharge modules include a `wikimedica_credit` metadata field. When clinics use the Wikimedica template and the content has not been substantially modified, the Wikimedica credit must remain visible in the footer or metadata of the printed/displayed document (consistent with CC BY-SA 4.0 attribution requirements).

### Platform Code and Scripts

The platform infrastructure code (`infra/`), GitHub Actions workflows (`.github/`), and automation scripts (`scripts/`) are © AT Medical Digital Solutions, all rights reserved, unless a separate open-source licence is specified in the file header. These are **not** released under Creative Commons.

---

## 7. AI-Generated Content and Copyright

### Copyright of AI Output

AI-generated text currently has uncertain copyright status in Germany and the EU. To eliminate risk:

- AI-generated text that forms the basis of a Wikimedica article must be substantially revised, restructured, and independently validated by a human author before submission.
- The submitted content is treated as the author's independent work, with the AI serving as a drafting tool.
- AI-generated content is **declared** in frontmatter (`ai_assisted: true`) for transparency.

### AI Tools and Third-Party Training Data

Authors must not use AI tools to reproduce or reconstruct copyrighted content (e.g., asking an AI to reproduce an UpToDate article). The prohibition on using copyrighted third-party content applies equally when that content is obtained via an AI intermediary.

---

## 8. Reporting Copyright Concerns

Anyone who believes a Wikimedica article contains content that infringes a third party's copyright should contact:

**editorial@wikimedica.de**

Reports are investigated within **10 business days**. If an infringement is confirmed, the content is removed or corrected immediately and the affected article enters the retraction process (see `docs/editorial/peer-review-policy.md`).
