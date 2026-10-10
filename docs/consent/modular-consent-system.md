# Modular Consent System — Wikimedica

**Document version:** 1.0
**Owner:** AT Medical Digital Solutions — Editorial & Product
**Last updated:** 2025-01-01

---

## 1. Purpose

The Wikimedica Modular Consent System provides clinics, hospitals, and outpatient practices with ready-to-use, evidence-based, and patient-friendly consent documents (*Aufklärungsbögen*). The system is built on modular, reusable Markdown templates that can be combined, customised with clinic branding, and distributed digitally via QR code or in print.

---

## 2. Core Principles

### 2.1 Patient-Centred Language

All consent module content is written in accessible German (targeting B2 level or lower for the explanatory sections). Medical terminology is introduced only with a plain-language explanation. Risk information is presented clearly without minimising or exaggerating risk.

### 2.2 Evidence-Based Content

Every risk listed in a consent module is supported by a clinical reference (guideline, meta-analysis, or published incidence data). Risk frequencies are presented in absolute terms (e.g., "1 in 100 patients") rather than vague qualitative terms ("rare") where evidence permits.

### 2.3 Modular Architecture

The system is designed around **independently reusable modules**. A complex procedure can be assembled from:

- A **procedure module** (what is done, how)
- A **risk module** (procedure-specific risks)
- A **medication module** (anaesthesia, contrast agents, etc.)
- A **discharge advice module** (post-procedure care)
- A **QR media module** (links to animated or video explanations)

### 2.4 Clinic Branding

Modules include a `clinic_brandable: true` flag and a designated header/footer area for clinic logo, address, and contact information. The **Wikimedica credit line** is preserved in the document footer metadata and printed footer as required by the CC BY-SA 4.0 licence.

---

## 3. Module Types

| Module Type | Description | Template |
|---|---|---|
| Consent Module | Full *Aufklärungsbogen* for a procedure | `content/templates/consent-module.md` |
| Procedure Module | Standalone procedure description | Inline in consent module |
| Risk Checklist Module | Structured risk list | Section in consent module |
| Medication Module | Pre/post medication explanation | Inline section |
| Discharge Module | Post-procedure/discharge instructions | `content/templates/discharge-module.md` |
| Wound Care Module | Wound and dressing care | Subsection of discharge module |
| QR Media Module | QR code link to video/animation | Metadata field + inline QR reference |

---

## 4. Patient-Friendly Disease Explanations

Consent modules include a brief, patient-friendly explanation of the underlying condition or indication that makes the procedure necessary. These explanations:

- Are written at a B1–B2 reading level.
- Include an optional illustration or diagram reference (linked via `qr_media_url`).
- Are maintained as standalone content in `content/patient-info/` and **transcluded** into consent modules to avoid duplication.

---

## 5. QR-Code-Linked Media

Each consent module may reference multimedia explanations (animations, video walkthroughs, 3D anatomy visuals) via the `qr_media_url` field in the YAML frontmatter. The printed version of the module displays a QR code pointing to this URL, allowing patients to watch an animated explanation of the procedure before signing consent.

### QR Media Requirements

- URL must be stable and hosted on a Wikimedica-controlled domain (or a permanent redirect).
- Media must be accessible without login.
- Videos must be subtitled in German.
- Media content must be reviewed for medical accuracy by the same reviewers as the consent module.

---

## 6. Risk Checklists vs. Free-Text Approach

### Structured Risk Checklist (Recommended)

For most procedures, risks are presented as a structured checklist in the consent module:

```markdown
- [ ] Blutung / Nachblutung (ca. 1 von 100 Patienten)
- [ ] Infektion an der Einstichstelle
- [ ] Thrombose / Embolie (ca. 1 von 500 Patienten bei offenen Eingriffen)
- [ ] Nervenverletzung (selten, < 1 von 1.000 Patienten)
- [ ] Allergische Reaktion auf verwendete Materialien
```

The checklist approach:

- Is easier for patients to read and process.
- Allows the physician to check off risks discussed in the verbal consent session.
- Provides a clear audit trail.

### Free-Text Approach

For complex or atypical procedures where a checklist does not adequately capture the nuance, a free-text risk section is permitted. However, risk frequency data must still be included where available.

---

## 7. Clinic-Brandable Templates

Clinic-brandable templates include:

- A **header block** (defined in frontmatter as `clinic_name`, `clinic_address`, `clinic_logo_url`) that prints at the top of the document.
- The Wikimedica content in the body (not modified by the clinic).
- A **footer block** with the Wikimedica credit, CC BY-SA 4.0 licence notice, document version, and date.

Clinics may:

- Add their logo and contact details.
- Translate risk descriptions to other languages (but must retain the German original alongside, unless a full reviewed translation exists in the Wikimedica system).
- Print on clinic letterhead.

Clinics may **not**:

- Remove the Wikimedica credit.
- Modify clinical content without the changes being reviewed and approved via the Wikimedica editorial process.
- Remove or alter risk information.

---

## 8. Wikimedica Credits in Metadata and Footer

Every consent and discharge module carries the following credit, both in YAML metadata and in the rendered document footer:

```text
Erstellt auf Basis von Wikimedica (wikimedica.de) — AT Medical Digital Solutions
Lizenz: CC BY-SA 4.0 | Version: [version] | Letzte Aktualisierung: [updated]
```

This credit satisfies the attribution requirement of the CC BY-SA 4.0 licence and serves as a quality signal for patients and clinical staff.

---

## 9. Version Control and Update Process

Consent modules are versioned using semantic versioning (e.g., `1.0.0`). Version bumps follow the editorial corrections policy:

- **Patch (x.x.1)**: Typographical fixes, formatting corrections.
- **Minor (x.1.0)**: Addition of new risk information, updated frequency data, new sections.
- **Major (1.0.0 → 2.0.0)**: Fundamental change to the procedure description, retraction of previous version due to clinical error, major guideline-driven restructuring.

Clinics using a specific module version are encouraged to subscribe to update notifications (future feature).
