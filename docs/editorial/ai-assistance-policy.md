# AI Assistance Policy — Wikimedica

**Document version:** 1.0
**Owner:** AT Medical Digital Solutions — Editorial Board
**Last updated:** 2026-10-09
**Status:** Active — supersedes the short "AI Usage Policy" in `editorial-governance.md` §7 (that section now points here)

---

## 1. Principle

AI may **support** people who write and review Wikimedica content. It never decides, never
reviews and never publishes.

> No medical content reaches readers without a qualified human author, a qualified human
> reviewer and — for high-risk content — a Medical Advisor. AI use changes neither this chain nor
> anyone's responsibility for the text.

The responsible human is always the **author** who submits the pull request. "The AI wrote it" is
never an acceptable explanation for an error.

---

## 2. What counts as AI-assisted

Declare `ai_assisted: true` when a generative AI system (a) wrote or rewrote text, tables or
structured data that ends up in the article or its metadata, (b) translated or summarised a source
for you, or (c) restructured the article beyond spelling and grammar correction.

Not AI-assisted in this sense: spell checkers and grammar checkers that only correct, and the
relevance scoring of the PubMed pipeline (it never writes article text). **When in doubt, declare.**
Declaring is never penalised; leaving it out is.

---

## 3. Permitted, conditional and prohibited uses

| Use | Status | Condition |
|---|---|---|
| Outline / structure suggestions | Permitted | Declare |
| Language polishing, shortening | Permitted | Declare; the author re-reads every sentence |
| Simplifying wording for patient text | Conditional | Declare; separate comprehensibility review is mandatory |
| Translation between languages | Conditional | Declare; full medical review of the translated text |
| Summarising a guideline or study you have read | Conditional | You check each statement against the source; summaries are your own wording, no verbatim protected text |
| Drafting dosing, thresholds or contraindications | **Prohibited** as a source | Values come from the primary source (Fachinformation, guideline); AI may not be the origin |
| Generating references, PMIDs, DOIs or guideline citations | **Prohibited** | Every reference is looked up and opened by a human |
| Inventing or "filling gaps" in clinical data, statistics, study results | **Prohibited** | — |
| Acting as reviewer, Medical Advisor or sign-off | **Prohibited** | Review is human by definition |
| Publishing or merging content autonomously | **Prohibited** | — |
| Entering patient data or other personal data into an AI service | **Prohibited** | No patient data in Wikimedica, in prompts, or in logs |
| Uploading protected full texts to an external AI service | **Prohibited** | Respect `docs/legal/copyright-and-sourcing-policy.md` |
| Generating images/media of patients, real persons or clinical findings | **Prohibited** without Editorial Board approval | Anatomical/illustrative media need review like text |

Tools: only AI tools **approved in writing by the Editorial Board** may be used. The Editorial Board
maintains the list; until it exists, ask before you use a tool. Data protection decides — the
AT Medical rule applies that personal medical or customer data is never placed into external model
services.

---

## 4. How to declare

In the frontmatter:

```yaml
ai_assisted: true
ai_assistance_description: >
  Tool: <name and version>. Task: first outline and plain-language rewrite of the
  section "Was ist das?". Verification: all statements checked against the cited
  guideline by <author>; references looked up manually.
```

A good description names the **tool**, the **task / sections**, and the **human verification**.
`validate-metadata.py` fails the pull request if `ai_assisted: true` has no description, and warns
if a description exists while `ai_assisted` is `false`.

---

## 5. Consequences for review

- The review level does **not** change with AI use (it follows `risk_level`), but the reviewer is
  told: the sign-off form has an AI field, and the reviewer verifies **every factual statement**
  of an AI-assisted high-risk text against its source rather than sampling.
- Reviewers who suspect undeclared AI use report it to the Editor. Undeclared use found after
  publication triggers the correction process, and in serious cases the retraction process
  (`peer-review-policy.md` §8).
- The Editorial Board reviews the share of AI-assisted articles and the findings per year.

---

## 6. Transparency towards readers

For AI-assisted articles the importer adds a short notice from `data/legal/disclaimers.yaml`
(block `ai_assisted`): AI tools supported the creation, and qualified people reviewed and approved
the content. The Editorial Board may change this wording; it is part of the legally reviewed
disclaimer set.

---

## 7. Automation boundary (architecture)

| Component | Uses AI? | Rule |
|---|---|---|
| `scripts/pubmed/` | Rule-based scoring (ML optional later) | Classifies **relevance of metadata** only; creates issues; never edits articles |
| `scripts/publishing/` (validate, convert, import) | **No** | Deterministic code. No model call in the publishing path |
| GitHub Actions | **No** | They run validators and scripts; they do not generate content |
| Future assistants | Only after an Editorial Board decision | Must keep the human chain in §1 |

Anything that would put a model call between an approved Markdown file and the live wiki is
**out of scope** for this policy and needs a new, explicit decision.

---

## 8. Open points for the owner

- 🧭 Approved-tools list and the process to add a tool (Editorial Board, with Data Protection).
- 🧭 Legal review: whether transparency duties beyond §6 (e.g. EU AI Act) apply to a public medical
  knowledge platform. This policy does not give legal advice.
- 🧭 Boundary to MediGuard: patient-specific decision support is **not** part of Wikimedica; any AI
  feature of that kind belongs to MediGuard and its own regulatory assessment.
