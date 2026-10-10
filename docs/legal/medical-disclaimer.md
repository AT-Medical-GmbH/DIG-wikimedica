# Medical Disclaimer Policy — Wikimedica

**Document version:** 1.0
**Owner:** AT Medical Digital Solutions — Legal Reviewer / Editorial Board
**Last updated:** 2026-10-09
**Status:** Draft — **the wording requires Legal review before production** (`data/legal/disclaimers.yaml` → `review_status`)

> This document describes how disclaimers work. The exact wording lives in **one** place,
> `data/legal/disclaimers.yaml`, so it cannot drift between documents, pages and PDF output.
> It is not legal advice.

---

## 1. Purpose

Wikimedica explains medicine in general terms. It does not examine, diagnose or treat, and it does
not replace individual medical advice. Readers — especially patients — must be able to see this
and know what to do in an emergency, on **every page** they can land on.

## 2. Where disclaimers appear

| Place | Content | Mechanism |
|---|---|---|
| Every article | Notice blocks chosen by `article_type`, `content_kind`, `risk_level`, `ai_assisted` | The importer renders them from `disclaimers.yaml` (Phase 4); authors do not copy text into articles |
| Patient-facing articles, consent and discharge modules | **Emergency notice first** (112, 116 117), then the general and type-specific notice | `profiles` in `disclaimers.yaml` |
| High-risk content, pharmaka, therapy | Additional dosing notice | `rules.by_risk_level.high` |
| Site footer on every page | Links "Datenschutz", "Impressum", "Haftungsausschluss" | MediaWiki messages `privacypage`/`privacy`, `aboutpage`/`aboutsite`, `disclaimerpage`/`disclaimers` pointing to the pages in `docs/legal/page-drafts/` |
| Printed/PDF clinic output | Same blocks as the article | Same source; the clinic adds its own conversation notice |

## 3. Content rules

1. **Emergency notice is never hidden** behind a click or placed after the text on patient-facing pages.
2. Disclaimers state limits; they do **not** replace safe content. A dangerous statement stays
   dangerous with a disclaimer.
3. Patient wording stays general ("Ändern Sie … nie ohne Rücksprache"), never an individual instruction.
4. A dosing notice is shown wherever doses appear; doses always carry source and Stand in the text.
5. AI transparency: AI-assisted articles show the `ai_assisted` block (see the AI assistance policy).
6. Consent modules say that they do not replace the personal Aufklärungsgespräch.

## 4. Governance

- Text changes in `data/legal/` need review by the **Legal Reviewer** and the **Editorial Board**
  (CODEOWNERS) and reset `review_status` to `pending-legal-review`.
- The **production import refuses to run** while `review_status` is not `approved`. Staging may use
  the draft wording to test layout.
- Approval is recorded in the file (`approved_by`, `approved_on`) and in the pull request.
- Review at least yearly and whenever the legal situation or the product scope changes.

## 5. Boundary to MediGuard and regulatory scope

Wikimedica provides general knowledge. It does not compute patient-specific recommendations; that
belongs to MediGuard. If a Wikimedica feature ever produced individual recommendations (calculators,
decision support), that feature would need its own regulatory assessment (e.g. as medical-device
software) **before** release, and these disclaimers would not be sufficient.
Legal Reviewer to confirm the current classification of the planned scope. 🧭

## 6. Open points 🧭

- Legal approval of the German wording in `disclaimers.yaml`.
- Whether the Heilmittelwerbegesetz or other advertising rules affect pharmaka pages (no product
  advertising is intended; the Legal Reviewer confirms).
- English wording, if English articles are published (`language: en`).
