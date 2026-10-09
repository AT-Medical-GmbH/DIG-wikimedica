# Security Incident Response — Wikimedica

**Owner:** DevOps · **Last updated:** 2026-10-09 · **Status:** Active

## Severity

| Class | Meaning | Reaction time |
|---|---|---|
| S1 | confirmed compromise, data leak, defaced or manipulated medical content | immediately, 24/7 |
| S2 | exploitable vulnerability, leaked secret | same day |
| S3 | hardening finding, low risk | next maintenance slot |

## Steps (S1/S2)

1. **Contain** — leaked secret: revoke/rotate it first (GitHub secret, bot password, SSH key, DB password, `MEDIAWIKI_SECRET_KEY` invalidates sessions).
   Compromised server: block traffic at Cloudflare (under-attack mode or maintenance page), do not wipe it yet.
2. **Preserve** — `docker logs`, web and auth logs, `last-backup.json`, `git log`, and a disk snapshot.
3. **Assess** — what was reached, was content changed (compare with Git: `import_to_mediawiki.py --dry-run` shows
   pages that differ from the repository), was personal data (user e-mails, password hashes) exposed.
4. **Recover** — rebuild from Git and the last known-good backup (`disaster-recovery.md`); re-import published content;
   rotate all secrets.
5. **Notify** — personal-data breach: Datenschutzbeauftragte/r and the supervisory authority within **72 hours** (Art. 33 GDPR);
   affected users where required (Art. 34). Manipulated medical content: Medical Advisor immediately, public correction note.
6. **Learn** — incident report within 5 working days, issue with actions, update this document.

## Standing controls

Branch protection and required review; deploy only release tags on main; secrets only in GitHub environments;
secret-shape scan in CI; Dependabot; bot account with minimal rights (edit pages in protected namespaces, nothing else);
email-confirmed accounts and the custom edit right for content namespaces; no `userrights` for bureaucrats.

## Contacts

security@wikimedica.de (placeholder, owner to confirm) · data protection officer: see `docs/legal/page-drafts` once filled in.
