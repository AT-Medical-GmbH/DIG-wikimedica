# Deployment Model — Wikimedica

**Document version:** 1.0
**Owner:** AT Medical Digital Solutions — Engineering
**Last updated:** 2025-01-01

---

## 1. Overview

This document describes the complete deployment infrastructure for Wikimedica, from the GitHub repository to the live site at `wikimedica.de`. All infrastructure is defined as code in the `infra/` directory.

---

## 2. Infrastructure Stack

| Component | Technology | Version |
|---|---|---|
| Version Control | GitHub | — |
| CI/CD | GitHub Actions | — |
| Host | VPS (KVM) | Debian 12 / Ubuntu 22.04 LTS |
| Container Runtime | Docker Engine | 24.x+ |
| Orchestration | Docker Compose | v2.x |
| Reverse Proxy | Traefik | v3.x |
| TLS | Let's Encrypt (DNS-01 via Cloudflare) | — |
| DNS / CDN / WAF | Cloudflare | — |
| Application | MediaWiki | Latest LTS (1.42.x) |
| Database | MariaDB | 10.11 LTS |

---

## 3. GitHub → CI/CD → VPS Flow

```text
Developer pushes tag to main (e.g., v1.2.3)
    │
    ▼
GitHub Actions: deploy.yml
    ├── Checkout repository at tag
    ├── SSH to VPS using SSH_PRIVATE_KEY secret
    └── Execute infra/deploy/deploy.sh on VPS
             │
             ├── git pull origin main (or checkout tag)
             ├── docker compose pull
             ├── docker compose up -d --remove-orphans
             ├── docker compose ps (health check)
             └── Notify on failure (email / GitHub issue)
```

All deployments are triggered by **git tags** on `main`, not by every commit. This ensures only explicitly versioned releases reach production.

---

## 4. Docker Compose Setup

### Production Compose (`infra/docker/docker-compose.yml`)

Services:

- **traefik**: Reverse proxy. Reads dynamic config from `infra/traefik/dynamic/`. Stores Let's Encrypt certificates in a named volume.
- **mediawiki**: The MediaWiki application. PHP-FPM + Apache. Mounts `LocalSettings.php` and uploads directory.
- **mariadb**: Database. Uses a named volume for data persistence. Only accessible on the internal Docker network.

Named volumes:

- `db_data`: MariaDB data files
- `mediawiki_images`: MediaWiki uploaded images
- `traefik_certs`: Let's Encrypt certificate storage

Networks:

- `traefik_net`: External-facing; Traefik + MediaWiki
- `internal_net`: Internal-only; MediaWiki ↔ MariaDB

### Dev Override (`infra/docker/docker-compose.override.yml`)

Used for local development:

- Ports exposed directly (no Traefik TLS)
- Local volume mounts for MediaWiki source
- TLS disabled
- Database port exposed for local SQL clients

---

## 5. Traefik Configuration

### Static Config (`infra/traefik/traefik.yml`)

- **Entrypoints**: `web` (HTTP:80), `websecure` (HTTPS:443)
- **Certificate resolver**: `cloudflare-dns` (Let's Encrypt DNS-01 via Cloudflare API)
- **Providers**: Docker (reads container labels), File (reads `dynamic/` directory)
- **Log level**: INFO (production), DEBUG (staging)
- **Access logs**: enabled, JSON format

### Dynamic Config (`infra/traefik/dynamic/middlewares.yml`)

- `redirect-to-https`: HTTP → HTTPS permanent redirect
- `security-headers`: HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, CSP
- `rate-limit`: 100 requests/second burst, 50 average

### Container Labels (in docker-compose.yml)

MediaWiki container carries Traefik labels that:

- Enable Traefik routing for the `websecure` entrypoint
- Attach the `cloudflare-dns` certificate resolver
- Apply the `redirect-to-https` and `security-headers` middlewares
- Set the rule `Host(\`wikimedica.de\`)` for the main domain

---

## 6. Cloudflare DNS Setup

DNS records are managed in the Cloudflare dashboard for `wikimedica.de`:

| Type | Name | Value | Proxy |
|---|---|---|---|
| A | `@` | VPS IP address | ✅ Proxied |
| A | `www` | VPS IP address | ✅ Proxied |
| CNAME | `wiki` | `wikimedica.de` | ✅ Proxied |

TLS certificates are issued by Let's Encrypt via **Cloudflare DNS-01 challenge**. Traefik uses the `CLOUDFLARE_API_TOKEN` environment variable to create the required TXT records automatically during certificate issuance and renewal.

Cloudflare SSL/TLS mode is set to **Full (strict)** — end-to-end TLS from browser to VPS.

---

## 7. Let's Encrypt TLS

- Certificates are requested and renewed automatically by Traefik using the ACME DNS-01 challenge.
- Challenge provider: Cloudflare (configured in `traefik.yml` under `certificatesResolvers`).
- Certificate files are stored in the `traefik_certs` Docker named volume.
- Automatic renewal occurs when certificates are within **30 days** of expiry.
- A renewal failure generates a Traefik log warning; monitoring should alert on this.

---

## 8. MediaWiki Configuration

### LocalSettings.php

`LocalSettings.php` is **not committed** to the repository. An example is provided at `infra/mediawiki/LocalSettings.example.php`.

On the VPS, `LocalSettings.php` is generated during initial setup using `infra/env/.env` values. Key configuration:

| Setting | Source |
|---|---|
| `$wgDBserver` | `MEDIAWIKI_DB_HOST` env var |
| `$wgDBname` | `MEDIAWIKI_DB_NAME` env var |
| `$wgDBuser` | `MEDIAWIKI_DB_USER` env var |
| `$wgDBpassword` | `MEDIAWIKI_DB_PASSWORD` env var |
| `$wgSecretKey` | `MEDIAWIKI_SECRET_KEY` env var |
| `$wgServer` | `https://wikimedica.de` |
| `$wgSitename` | `Wikimedica` |

### Enabled Extensions (Minimum)

- VisualEditor
- WikiEditor
- CategoryTree
- ParserFunctions
- Cite
- TemplateStyles
- SyntaxHighlight_GeSHi
- Echo (notifications)

---

## 9. Environment Variable Management

All sensitive configuration is managed via environment variables. On the VPS:

1. Copy `infra/env/.env.example` to `infra/env/.env`.
2. Fill in all values (see the example file for the full list).
3. The `.env` file is referenced by Docker Compose using `env_file: ../env/.env`.
4. The `.env` file is **never committed** to the repository (enforced by `.gitignore`).

In GitHub Actions, secrets are stored in the repository's **Secrets** configuration and injected as environment variables at workflow runtime.

---

## 10. Rollback Process

If a deployment causes an issue, roll back using `infra/deploy/rollback.sh`:

```bash
./infra/deploy/rollback.sh [previous-tag-or-commit]
```

The rollback script:

1. Stops all running containers.
2. Checks out the specified previous tag or commit.
3. Restarts the Docker Compose stack.
4. Verifies health.

Database schema rollbacks require manual intervention; see the backup/restore procedure below.

---

## 11. Backup and Restore Strategy

### Automated Backups

`infra/deploy/backup.sh` runs daily (cron job on VPS):

1. `mysqldump` of the MariaDB database → compressed `.sql.gz`.
2. Archive of the `mediawiki_images` volume → `.tar.gz`.
3. Upload to backup storage (S3-compatible object store or remote SFTP — configured via env vars).
4. Rotation: keep last 7 daily, 4 weekly, 3 monthly backups.

### Restore Procedure

1. Stop MediaWiki container.
2. Restore database from backup: `mysql -u root < backup.sql`.
3. Restore images volume from archive.
4. Restart containers.
5. Test MediaWiki is functional.

Backup verification (restore test) is performed **monthly** in a staging environment.
