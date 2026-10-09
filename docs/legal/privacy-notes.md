# Privacy Notes and Tracking Decision — Wikimedica

**Document version:** 1.0
**Owner:** AT Medical Digital Solutions — Legal Reviewer / DevOps
**Last updated:** 2026-10-09
**Status:** Draft — working notes for the privacy statement; **needs review by the data protection officer / Legal**. Not legal advice.

---

## 1. Principles

1. **No patient data.** Wikimedica stores no patient data: no health records, no personal medical
   questions, no user-submitted case descriptions. Forms and comments that could invite health data
   are not offered. The consent/discharge modules are **blank templates**; filling them in happens
   at the clinic, outside Wikimedica.
2. **Data minimisation.** Readers browse without an account; no registration for reading.
3. **No unnecessary third parties.** No external fonts, analytics, social widgets or embedded
   third-party players in the default setup.
4. **Logs without content.** Access and error logs may contain IP addresses; they carry no health content.

## 2. What data arises

| Data | Whose | Purpose | Where | Retention (proposal) |
|---|---|---|---|---|
| Server access logs (IP, URL, user agent) | All visitors | Security, abuse defence, operations | Traefik / MediaWiki logs on the server | 7–14 days, then deleted 🧭 |
| CDN/WAF processing | All visitors | Delivery, DDoS protection | Cloudflare (processor) | per Cloudflare terms |
| Account data (name, e-mail, password hash) | Editorial staff only | Talk-page access, notifications | MariaDB | while the role exists |
| Session/login cookie | Logged-in staff | Authentication | Browser | session / short |
| E-mail sent by the wiki | Staff | Confirmation, notifications | SMTP provider (processor) | per provider |
| CAPTCHA token | Account creation / failed logins | Abuse defence | CAPTCHA provider | see §4 |
| Contact e-mail to editorial@ / tech@ | Senders | Answering requests | Mail system | as long as needed |

Reader-facing pages set **no cookies** beyond what MediaWiki needs for logged-in staff.

## 3. Cookie and tracking decision (DEC-5) 🧭

**Proposed decision:** *no analytics, no marketing cookies, no third-party embeds* → no consent
banner is needed for readers, because only technically necessary data is processed. If the owner later
wants reach measurement, use a **cookieless, self-hosted** tool (e.g. a privacy-friendly analytics
without cookies and with anonymised IPs) and have Legal re-assess; do not add Google Analytics.

| Option | Consent banner | Privacy impact | Recommendation |
|---|---|---|---|
| A — no analytics (default) | none | minimal | **Recommended** |
| B — self-hosted cookieless analytics | usually none (Legal to confirm) | low | later, if needed |
| C — third-party analytics/marketing | required | high; unsuitable for a medical site | not recommended |

Decision owner: AT Medical GmbH management. Record the decision and date here when taken:
**Decision:** *pending* · **Date:** *pending*

## 4. Third parties that need a decision or an agreement

| Service | Issue | Action |
|---|---|---|
| **Cloudflare** (DNS/CDN/WAF) | Processes visitor IPs; international transfer | Data-processing agreement; check transfer mechanism; mention in the privacy statement |
| **reCAPTCHA** (Google) | Third-party script, data sent to Google, usually needs consent | Prefer **hCaptcha** or Cloudflare Turnstile, or avoid CAPTCHA on public pages (reading needs none; it only runs for account creation/failed logins) — 🧭 DEC-4 |
| **SMTP provider** | Processes staff e-mail | Data-processing agreement |
| **Hosting provider** | Server, backups | Data-processing agreement |
| **Backup target** (S3/SFTP) | Contains DB dumps with staff account data | Encryption at rest and in transit; EU location; processor agreement |
| **Media hosting** for QR videos | Visitor IP to the host on playback | Link, do not embed; host in the EU; processor agreement; say so in the media record |

## 5. Technical measures that support privacy

- HTTPS only with HSTS (Traefik middleware); security headers; no `X-Powered-By`.
- No external resources in the CSP (`default-src 'self'`); the only exception today is
  `img-src … upload.wikimedia.org` and must be re-examined if unused. 🧭
- Database not reachable from outside; backups encrypted; secrets only in server `.env`/GitHub Secrets.
- No IP anonymisation is configured in MediaWiki for logged-out reading because there are no
  logged-out edits (anonymous editing is disabled).

## 6. Rights of data subjects

Provide a contact address (editorial@/privacy@ — 🧭 which one), a process for access, correction and
erasure of staff accounts, and the right to complain to the competent supervisory authority
(authority depends on the company seat — Legal to name it).

## 7. Pages to publish

Drafts with placeholders are in `docs/legal/page-drafts/`:
`impressum.md`, `datenschutz.md`, `haftungsausschluss.md`. They contain **placeholders for real company
data** (address, register number, managing director, VAT ID, authority) that must be filled by
AT Medical GmbH; they must not go live unreviewed.
