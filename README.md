# Wikimedica

> **Medizinisches Wissen. Strukturiert. Geprüft. Frei zugänglich.**
>
> A modular, evidence-based medical knowledge platform for healthcare professionals and patients — governed by editorial policy, powered by MediaWiki, and orchestrated through GitHub.

---

## Table of Contents

1. [What is Wikimedica?](#what-is-wikimedica)
2. [Platform Architecture](#platform-architecture)
3. [Content Model](#content-model)
4. [Editorial Model](#editorial-model)
5. [GitHub as Source of Truth](#github-as-source-of-truth)
6. [Deployment Model](#deployment-model)
7. [PubMed Surveillance](#pubmed-surveillance)
8. [Contributing](#contributing)
9. [License](#license)
10. [Contact](#contact)

---

## What is Wikimedica?

**Wikimedica** (wikimedica.de) is a German-language medical knowledge platform developed and maintained by **AT Medical Digital Solutions**. It serves three core audiences:

- **Healthcare professionals** — structured, guideline-aligned clinical articles with references, ICD-10 codes, and versioned update history.
- **Patients** — plain-language explanations of diagnoses, procedures, and medications at an accessible reading level.
- **Clinical teams** — modular consent forms (*Aufklärungsbögen*), discharge instructions, and wound-care guides that clinics can brand and deploy via QR code.

Wikimedica is **not** a copy of existing encyclopaedias. Every article is independently authored, peer-reviewed by specialty-qualified medical professionals, and released under a Creative Commons licence.

### Flagship Focus: Gender-Medizin

Gender-Medizin (sex- and gender-sensitive medicine) is a cross-cutting editorial priority. Articles across all specialties are evaluated for sex- and gender-disaggregated evidence, and a dedicated Gender-Medizin specialty area publishes original content on this topic.

---

## Platform Architecture

```text
GitHub (source of truth)
    │
    ├── content/         ← Markdown articles, templates, consent modules
    ├── docs/            ← Architecture, governance, legal, editorial policy
    ├── data/            ← PubMed records, guideline registry, scoring data
    ├── scripts/         ← Automation (PubMed search, validation, reporting)
    └── infra/           ← Docker, Traefik, deploy scripts
         │
         └── CI/CD (GitHub Actions)
                  │
                  ▼
         VPS (wikimedica.de)
         ├── Traefik (reverse proxy, TLS via Cloudflare DNS challenge)
         ├── MediaWiki (public frontend)
         └── MariaDB (content database)
                  │
         Cloudflare (DNS, DDoS protection, CDN)
```

See [`docs/architecture/system-overview.md`](docs/architecture/system-overview.md) for the full architecture document.

---

## Content Model

Content is organised into the following types:

| Type | Description | Audience |
|---|---|---|
| Professional Article | Guideline-aligned clinical articles | Physicians, nurses, pharmacists |
| Patient Article | Plain-language disease/procedure explanations | Patients, caregivers |
| Consent Module | Modular *Aufklärungsbögen* for procedures | Patients + clinical staff |
| Discharge Module | Post-discharge instructions and wound care | Patients + clinical staff |
| Pharmaka | Structured drug information | Physicians, pharmacists |
| Therapy | Evidence-based therapy protocols | Physicians |

All content lives in `content/` as Markdown files with YAML frontmatter. Templates are in `content/templates/`.

### Specialty Taxonomy

Wikimedica covers 26 clinical specialty areas:

Innere Medizin · Kardiologie · Pneumologie · Gastroenterologie · Nephrologie · Endokrinologie/Diabetologie · Hämatologie/Onkologie · Infektiologie · Rheumatologie · Neurologie · Psychiatrie · Dermatologie · Pädiatrie · Gynäkologie/Geburtshilfe · Urologie · Orthopädie/Unfallchirurgie · Anästhesiologie · Intensivmedizin · Notfallmedizin · Chirurgie · Radiologie · Labormedizin · Pharmakologie · Palliativmedizin · Prävention/Public Health · Gender-Medizin

---

## Editorial Model

All content follows a structured lifecycle:

```text
Draft → Peer Review → Editorial Review → Medical Advisor Sign-off → Published
```

Key principles:

- Every article requires at least one peer review by a **specialty-qualified reviewer**.
- Medical advisors sign off on articles in high-risk areas (drug dosing, emergency medicine, oncology protocols).
- Articles are flagged for review when new AWMF/ESC guidelines are published or when PubMed surveillance identifies significant new evidence.
- AI-assisted drafting is permitted but must be declared in the article metadata and requires full human review.

See [`docs/editorial/editorial-governance.md`](docs/editorial/editorial-governance.md) for the full governance document.

---

## GitHub as Source of Truth

GitHub is the **canonical source** for all Wikimedica content and infrastructure configuration. This means:

- Every article, policy, and configuration file lives in this repository.
- All changes go through Pull Requests with required reviewers.
- Article status is tracked in YAML frontmatter (`draft`, `in-review`, `approved`, `published`, `archived`).
- The PubMed surveillance workflow commits results directly to `data/pubmed/` and opens Issues for editorial follow-up.
- Guideline review reminders are generated as GitHub Issues on a monthly schedule.
- Deployments are triggered by tagged releases on `main` via GitHub Actions.

CODEOWNERS (`.github/CODEOWNERS`) enforce that changes to `docs/`, `content/`, and `infra/` require approval from the respective team.

---

## Deployment Model

| Component | Technology |
|---|---|
| Hosting | VPS (KVM, Debian/Ubuntu) |
| Reverse Proxy | Traefik v3 |
| TLS | Let's Encrypt via Cloudflare DNS-01 challenge |
| DNS / CDN | Cloudflare |
| Application | MediaWiki (latest LTS) |
| Database | MariaDB 10.11+ |
| Container Runtime | Docker Compose |

Deployments are executed by `infra/deploy/deploy.sh` on the VPS, triggered via SSH from a GitHub Actions workflow on tagged release pushes to `main`.

See [`docs/deployment/deployment-model.md`](docs/deployment/deployment-model.md) and `infra/` for full details.

---

## PubMed Surveillance

A daily GitHub Actions workflow (`scripts/pubmed/pubmed-daily-search.py`) queries the NCBI PubMed API using specialty-specific search strategies defined in `scripts/pubmed/search-terms.yaml`. Results are:

1. Normalised and stored as JSONL in `data/pubmed/`.
2. Classified for relevance (stub model — to be extended with ML).
3. Mapped to Wikimedica specialties.
4. Actioned automatically:
   - **High relevance** → GitHub Issue opened for editorial review.
   - **Medium relevance** → Logged for monthly review.
   - **Low relevance** → Stored but no action.

Gender-Medizin has an expanded search term set reflecting the flagship priority.

See [`docs/pubmed/pubmed-surveillance-architecture.md`](docs/pubmed/pubmed-surveillance-architecture.md).

---

## Contributing

### For Medical Authors

1. Read [`docs/authors/author-onboarding-model.md`](docs/authors/author-onboarding-model.md).
2. Complete the author application form at [`forms/author-application/author-application-form.md`](forms/author-application/author-application-form.md).
3. Once approved, create articles using templates in `content/templates/`.
4. Submit via Pull Request against `main`.

### For Reviewers

1. Review the checklist at [`forms/reviewer-checklists/medical-content-review-checklist.md`](forms/reviewer-checklists/medical-content-review-checklist.md).
2. Add yourself as a reviewer on the PR.
3. Complete the sign-off form at [`forms/editorial-review/editorial-sign-off.md`](forms/editorial-review/editorial-sign-off.md).

### For Infrastructure / Developers

1. Use `infra/env/.env.example` to set up your local environment.
2. `docker compose -f infra/docker/docker-compose.yml -f infra/docker/docker-compose.override.yml up -d` to run locally.
3. Submit infrastructure changes via PR; `infra/` requires DevOps team approval.

---

## License

**Wikimedica content** (articles, patient information, consent modules) is released under the **Creative Commons Attribution–ShareAlike 4.0 International** licence ([CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)), unless otherwise noted.

**Platform code, scripts, and infrastructure configuration** are © AT Medical Digital Solutions. All rights reserved unless a separate open-source licence is specified in the file header.

See [`docs/legal/copyright-and-sourcing-policy.md`](docs/legal/copyright-and-sourcing-policy.md) for details.

---

## Contact

**AT Medical Digital Solutions**
Website: [wikimedica.de](https://wikimedica.de)
Editorial enquiries: editorial@wikimedica.de
Technical enquiries: tech@wikimedica.de
Git-based product and content backbone for Wikimedica, AT Medical’s modular medical knowledge, patient education, and consent platform. Includes editorial governance, review workflows, PubMed surveillance, structured content architecture, and deployment preparation for wikimedica.de
> ⚠️ This repository is **source-available but not open source**. All rights are reserved by AT Medical GmbH. See the [`LICENSE`](LICENSE) file for details.

# Wikimedica

**Structured Medical Knowledge and Patient Education Platform**

Wikimedica is a modular, AI-assisted medical knowledge, patient education, and consent platform developed by **AT Medical Digital Solutions**.

It is designed to combine structured medical content, editorial governance, AI-supported review workflows, and GitHub-driven publishing preparation into a scalable medical knowledge ecosystem.

---

## Vision

To create a modern, structured, and continuously reviewable medical knowledge platform for both healthcare professionals and patients.

---

## Core Areas

Wikimedica is being prepared as a modular knowledge system covering areas such as:

- diseases / Erkrankungen
- therapies / Therapien
- pharmacology / Pharmaka
- patient education
- consent modules / Aufklärungsbögen
- discharge and aftercare
- guideline summaries
- QR-linked media and explanatory content

---

## Core Principles

- **Human review before publication**
- **AI as support, not autonomous publisher**
- **Structured editorial governance**
- **Evidence-aware content development**
- **Separation of professional and patient-friendly language layers**
- **Future-ready for public platform deployment**

---

## Repository Role

This repository is the operational backbone for the future Wikimedica platform and is intended to host:

- content architecture
- editorial governance
- review workflows
- source tracking
- PubMed surveillance preparation
- guideline review structures
- author onboarding models
- deployment and publishing scaffolding

---

## Product Direction

Wikimedica is designed to support:

- medical specialty structures
- knowledge articles
- patient-friendly explanatory materials
- modular consent content
- structured discharge information
- future media-linked patient information journeys

The long-term platform target is a professional public medical knowledge product with controlled editorial quality.

---

## Relationship to MediGuard

Wikimedica and MediGuard are separate but connected systems.

| Wikimedica | MediGuard |
|-----------|----------|
| explains | evaluates |
| content | context |
| patient education | patient safety support |
| structured knowledge | structured clinical support |

Wikimedica provides the knowledge layer. MediGuard builds the contextual patient-safety layer on top of structured medical understanding.

---

## Deployment Direction

This repository is being prepared for GitHub-driven deployment to the AT Medical VPS.

Target domains include:

- `wikimedica.de`
- `www.wikimedica.de`
- optional later:
  - `media.wikimedica.de`
  - `authors.wikimedica.de`

The live platform direction is aligned with domain-based, structured production deployment.

---

## Public Visibility

This repository is publicly visible to communicate:

- product vision
- editorial architecture
- medical knowledge strategy
- contribution possibilities
- future publishing model

Public visibility does **not** grant permission to use, deploy, copy, adapt, commercialize, or redistribute the project.

---

## License

This repository is licensed under the **AT Medical Proprietary Source-Available License v1.0**.

In practical terms:

- viewing is allowed
- feedback is welcome
- contributions may be proposed
- use, deployment, adaptation, redistribution, or commercialization are **not** allowed without explicit written permission from AT Medical GmbH

See [`LICENSE`](LICENSE) for the full text.

---

## Contributing

Contributions, issues, and suggestions are welcome under controlled review.

Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) before opening a pull request or proposing changes.

---

## Maintained by

**AT Medical GmbH**  
Digital Solutions Division
