# Wikimedica

> **Medizinisches Wissen. Strukturiert. Geprüft. Frei zugänglich.**
>
> A modular, evidence-based German-language medical knowledge platform (wikimedica.de) for
> healthcare professionals and patients — governed by editorial policy, powered by MediaWiki,
> orchestrated through GitHub. WikiMedica **explains**; [MediGuard](https://github.com/AT-Medical-GmbH/DIG-mediguard)
> **evaluates**. WikiMedica is not the internal company wiki (ATMED-wiki).

## Status

**Pre-production.** The platform, the publishing pipeline, backup/restore and CI are built and
tested. Going live is gated by owner decisions and operator tasks that engineering must not
take over — see [`docs/deployment/go-live-checklist.md`](docs/deployment/go-live-checklist.md).
No article is published yet; all textbook-derived articles are drafts awaiting qualified review.

## How it works

```text
GitHub (single source of truth)
  content/*.md  ──PR + review──►  main  ──release tag vX.Y.Z──►  deploy workflow ──ssh──► server
        │                                                          (backup → update → health check → auto rollback)
        └─ status published + tag ──► import_to_mediawiki.py ──► MediaWiki 1.43 LTS (+ MariaDB 10.11)
```

- **Content** is Markdown with YAML frontmatter (schema: `data/metadata/article-schema.yaml`).
  Lifecycle: `draft → in-review → (advisor-review) → approved → published → archived/retracted`.
  Approved and published content is frozen; the slug is immutable.
- **Publishing** is one-way GitHub → MediaWiki (`scripts/publishing/`): safe Markdown→wikitext
  conversion, idempotent, never overwrites pages it does not own, production only for
  `published` articles at a release tag.
- **Operations** (`infra/deploy/`): tag-only deploy, verified backups (7 daily / 4 weekly /
  3 monthly), restore with safety dump, rollback, health check, monthly restore test.
- **Surveillance**: daily PubMed search and monthly guideline review reminders create GitHub
  issues; nothing is published automatically.
- **AI assistance** is allowed for drafting only, must be declared in the metadata, and never
  replaces human review (`docs/editorial/ai-assistance-policy.md`).

## Repository map

| Path | Content |
|---|---|
| `content/` | Articles by type and status, templates (`content/templates/`) |
| `data/` | Metadata schema, legal texts, source inventory, PubMed/guideline data |
| `docs/` | Architecture, editorial, legal, deployment and operations documentation |
| `forms/` | Author application, review checklists, sign-off |
| `infra/` | Docker Compose, MediaWiki settings, Traefik, env example, deploy scripts |
| `scripts/` | Validation, publishing (importer, converter), PubMed surveillance |
| `tests/` | Unit, deploy, backup/restore and (opt-in) real-MediaWiki integration tests |

## Develop and test

```bash
pip install -r requirements-dev.txt
python3 -m pytest -q                      # default suite
WM_REAL_MW=1 python3 -m pytest tests/integration -q   # real MediaWiki (needs php + sqlite; opt-in)
python3 scripts/validation/validate-metadata.py       # content metadata
npm ci && npx markdownlint-cli "**/*.md" --ignore node_modules && npx cspell "**/*.md"
```

CI (`.github/workflows/ci.yml`) runs the same checks; the aggregate job `ci-ok` is the
single required status check.

## Documentation entry points

- Concept and decisions: [`docs/architecture/production-readiness-concept.md`](docs/architecture/production-readiness-concept.md)
- Go-live checklist: [`docs/deployment/go-live-checklist.md`](docs/deployment/go-live-checklist.md)
- Staging first: [`docs/deployment/staging-first-deployment.md`](docs/deployment/staging-first-deployment.md)
- Operations: [`runbook`](docs/operations/runbook.md) · [`backup & restore`](docs/operations/backup-restore-runbook.md) · [`disaster recovery`](docs/operations/disaster-recovery.md) · [`monitoring`](docs/operations/monitoring.md) · [`maintenance`](docs/operations/maintenance.md) · [`updates`](docs/operations/update-policy.md) · [`security response`](docs/operations/security-response.md)
- Editorial: [`docs/editorial/`](docs/editorial/editorial-governance.md)

## License

The repository's [`LICENSE`](LICENSE) file is authoritative: *AT Medical Proprietary
Source-Available License v1.0* (viewing allowed; use, deployment and redistribution need
written permission). Which licence the published **articles** carry (e.g. CC BY-SA 4.0) is an
open owner decision, [`docs/legal/license-decision-needed.md`](docs/legal/license-decision-needed.md);
until it is made, no article may declare a licence and nothing is published.

## Contact

Editorial: editorial@wikimedica.de · Technical: tech@wikimedica.de ·
Security: see [`SECURITY.md`](SECURITY.md)
