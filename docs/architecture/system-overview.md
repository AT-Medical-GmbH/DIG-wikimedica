# System Architecture Overview — Wikimedica

**Document version:** 1.0
**Owner:** AT Medical Digital Solutions — Engineering
**Last updated:** 2025-01-01

---

## 1. Introduction

This document describes the overall system architecture of Wikimedica (wikimedica.de). The platform is designed around the principle that **GitHub is the single source of truth** for all content, configuration, and infrastructure code, while **MediaWiki** provides the public-facing reading experience.

---

## 2. High-Level Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                     INTERNET / USERS                        │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTPS
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     CLOUDFLARE                              │
│   DNS · DDoS protection · CDN · TLS termination passthrough │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTPS (TLS forwarded)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  VPS  (Debian / Ubuntu)                     │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Traefik v3  (reverse proxy, Let's Encrypt via CF)   │   │
│  └───────┬──────────────────────────────────────────────┘   │
│          │ internal Docker network                          │
│  ┌───────▼──────────┐   ┌──────────────────────────────┐   │
│  │   MediaWiki      │   │   MariaDB 10.11+             │   │
│  │   (PHP/FPM)      │◄──►   (named volume: db_data)   │   │
│  └──────────────────┘   └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
          ▲
          │ SSH deploy trigger
          │
┌─────────────────────────────────────────────────────────────┐
│                   GITHUB (source of truth)                  │
│                                                             │
│  Repository: DIG-wikimedica                                 │
│  ├── content/        Markdown articles, templates           │
│  ├── docs/           Governance, architecture, legal        │
│  ├── data/           PubMed records, guideline registry     │
│  ├── scripts/        Automation scripts (Python)            │
│  └── infra/          Docker, Traefik, deploy scripts        │
│                                                             │
│  GitHub Actions                                             │
│  ├── markdown-lint.yml         → lint on push/PR            │
│  ├── metadata-validation.yml   → validate frontmatter       │
│  ├── link-check.yml            → weekly link check          │
│  ├── spelling-check.yml        → medical spelling check     │
│  ├── pubmed-daily.yml          → daily PubMed surveillance  │
│  ├── guideline-review.yml      → monthly guideline alert    │
│  └── deploy.yml                → deploy on tagged release   │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Component Descriptions

### 3.1 GitHub

GitHub serves as the **operational backbone** of Wikimedica:

- **Content authoring**: Articles are written as Markdown with YAML frontmatter, committed to `content/`.
- **Governance**: All changes require Pull Requests. CODEOWNERS enforce reviewer requirements.
- **Automation**: GitHub Actions handle linting, validation, PubMed surveillance, guideline monitoring, and deployment.
- **Issue tracking**: PubMed alerts, guideline reminders, and content update requests are tracked as GitHub Issues.

### 3.2 Cloudflare

- Provides authoritative DNS for `wikimedica.de` and all subdomains.
- Acts as a CDN and DDoS mitigation layer.
- TLS certificates for the public domain are issued by Let's Encrypt via the **Cloudflare DNS-01 challenge** (managed by Traefik using the `CLOUDFLARE_API_TOKEN`).
- Cloudflare proxies traffic to the VPS but passes TLS through to Traefik for end-to-end encryption control.

### 3.3 Traefik

Traefik v3 runs as a Docker container on the VPS and provides:

- **HTTP → HTTPS redirect** (middleware: `redirect-to-https`)
- **Security headers** (HSTS, CSP, X-Frame-Options — see `infra/traefik/dynamic/middlewares.yml`)
- **Automatic TLS** via Let's Encrypt DNS-01 challenge using Cloudflare API
- **Rate limiting** middleware to protect against abuse
- **Container-based routing** via Docker labels on the MediaWiki service

Static configuration: `infra/traefik/traefik.yml`
Dynamic configuration: `infra/traefik/dynamic/`

### 3.4 MediaWiki

MediaWiki is the public-facing content platform at `wikimedica.de`. Key configuration:

- **LocalSettings.php** is generated from `infra/mediawiki/LocalSettings.example.php` + environment variables.
- **Extensions** enabled at minimum: VisualEditor, WikiEditor, CategoryTree, ParserFunctions, Cite, TemplateStyles.
- **Skin**: Vector (2022) or custom AT Medical skin.
- Content is maintained in MediaWiki's MySQL/MariaDB database. GitHub is the **canonical authoring environment**; MediaWiki content is populated via import scripts (future implementation).

### 3.5 MariaDB

- Provides persistent storage for MediaWiki.
- Runs in a Docker container with a named volume (`db_data`) for data persistence.
- Backed up daily via `infra/deploy/backup.sh`.

---

## 4. Content Flow

```text
Author (GitHub PR)
    │
    ├── validate-metadata.py  ─────→ fails → PR blocked
    ├── markdown-lint.yml     ─────→ fails → PR blocked
    └── peer review (CODEOWNERS)
         │
         ▼
    Merge to main (approved)
         │
         ▼
    Article status: "approved"
         │
         ▼
    [Future] Import script → MediaWiki API → Live on wikimedica.de
         │
         ▼
    Cloudflare CDN cache invalidation
```

---

## 5. Data Model Overview

All articles use a standardised YAML frontmatter schema. See `data/metadata/article-schema.yaml` for the full schema definition.

Key fields:

| Field | Type | Description |
|---|---|---|
| `title` | string | Article title |
| `specialty` | string | One of 26 defined specialties |
| `article_type` | enum | `professional`, `patient`, `consent`, `discharge`, `pharmaka`, `therapy` |
| `status` | enum | `draft`, `in-review`, `approved`, `published`, `archived` |
| `version` | semver | Article version (e.g. `1.2.0`) |
| `authors` | list | Author names/IDs |
| `reviewers` | list | Reviewer names/IDs |
| `pubmed_ids` | list | Supporting PMID references |
| `guidelines` | list | Referenced AWMF/ESC/other guidelines |
| `icd10` | list | Relevant ICD-10 codes |
| `created` | ISO 8601 | Creation date |
| `updated` | ISO 8601 | Last update date |

---

## 6. Security Considerations

- All secrets (database passwords, API tokens, SSH keys) are stored in **GitHub Actions Secrets** and injected as environment variables at runtime. They are **never committed** to the repository.
- The `.env.example` file contains only placeholder values.
- Traefik enforces HTTPS-only access with HSTS headers.
- MediaWiki is configured to disable user registration without admin approval.
- VPS access is key-only SSH; password authentication is disabled.
- Regular automated database backups are encrypted and stored off-VPS.

---

## 7. Future Extensions

- **MediaWiki API import pipeline**: automate promotion of GitHub-approved articles to MediaWiki.
- **ML-based relevance classifier**: replace stub relevance scoring in PubMed surveillance.
- **Multilingual support**: English and French article variants via MediaWiki content translation.
- **FHIR integration**: expose structured article data as FHIR resources for clinical system integration.
- **Clinic white-label portal**: allow clinics to embed branded consent/discharge modules via subdomain or API.
