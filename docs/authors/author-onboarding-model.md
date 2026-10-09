# Author Onboarding Model — Wikimedica

**Document version:** 1.0
**Owner:** AT Medical Digital Solutions — Editorial Board
**Last updated:** 2025-01-01

---

## 1. Overview

The Wikimedica author community is the foundation of the platform's quality and credibility. This document describes the application process, qualification requirements, role structure, and the tools and access provided to approved contributors.

---

## 2. Application Workflow

```text
1. Candidate submits Author Application Form
         │  forms/author-application/author-application-form.md
         ▼
2. Editorial Board reviews qualifications (within 10 business days)
         │
         ├── Incomplete application → candidate notified, 14-day response window
         ├── Qualifications unmet → polite rejection with explanation
         └── Qualifications met → proceed to onboarding
         ▼
3. Onboarding
         ├── AT Medical email account created (@wikimedica.de)
         ├── GitHub account linked to Wikimedica organisation
         ├── Nextcloud access provisioned (collaboration workspace)
         ├── GitHub team assignment (based on role and specialty)
         └── Welcome email with onboarding guide and resources
         ▼
4. First contribution
         ├── Candidate completes a test edit (minor correction or review task)
         ├── Editor evaluates quality and communication
         └── Full contributor status confirmed (or role-adjusted)
         ▼
5. Active contributor
         └── Ongoing access to GitHub, Nextcloud, editorial communications
```

---

## 3. Qualification Checklist

All applicants must meet the **General Requirements** and at least one set of **Role-Specific Requirements**.

### 3.1 General Requirements (All Roles)

- [ ] Valid medical qualification appropriate to the intended contribution area (see 3.2 below)
- [ ] Fluent in written German (primary publication language)
- [ ] Basic familiarity with Markdown or willingness to learn (training provided)
- [ ] Signed **Author Agreement** including:
  - Editorial policy acceptance
  - Declaration of conflicts of interest (CoI)
  - Consent to AT Medical email account creation
  - Acknowledgement of CC BY-SA 4.0 licensing for contributed content
- [ ] No unresolved disciplinary proceedings before a medical licensing board (Ärztekammer) or professional regulatory authority

### 3.2 Role-Specific Qualifications

#### Contributor (Author)

- Medical degree (Staatsexamen, MD, MBBS, or equivalent) **or** equivalent qualification appropriate to content type:
  - Pharmacist (Approbation) for Pharmaka articles
  - Registered nurse with advanced practice qualification for nursing/care content
  - Medical scientist for laboratory medicine / basic science content
- For specialty articles: undergraduate or postgraduate training in the specialty (Weiterbildungsassistent or above), or equivalent academic qualification

#### Reviewer

- All Contributor requirements
- Minimum **3 years** post-qualification clinical or academic experience in the specialty
- Evidence of specialty expertise: certificate of specialty training (Facharzt), academic appointment, or equivalent
- Approval by the Editorial Board (two existing editors must endorse the application)

#### Editor

- All Reviewer requirements
- Demonstrable editorial experience: academic publication record, membership in a guideline committee, or equivalent
- Appointment by the Medical Director
- Minimum commitment: 4 hours/month of editorial work

#### Medical Advisor

- Board-certified specialist (Facharzt) in the relevant specialty with active clinical practice
- No unresolved conflicts of interest in the specialty
- Formal advisory agreement signed with AT Medical Digital Solutions (including remuneration terms)
- Appointment by the Medical Director

---

## 4. Author Roles and Permissions Summary

| Role | Create Articles | Review Articles | Merge PRs | Archive Content | Manage Authors |
|---|---|---|---|---|---|
| Contributor | ✅ | ❌ | ❌ | ❌ | ❌ |
| Reviewer | ✅ | ✅ (own specialty) | ❌ | ❌ | ❌ |
| Editor | ✅ | ✅ (any) | ✅ | ✅ | ❌ |
| Medical Advisor | ✅ | ✅ (own specialty, high-risk) | ❌ | ❌ | ❌ |
| Medical Director | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 5. AT Medical Email Assignment

Approved contributors receive an AT Medical email address in the format:
`firstname.lastname@wikimedica.de`

This address is used for:

- GitHub organisation membership (the GitHub account should be associated with this email)
- Nextcloud access
- Editorial communications
- Official attribution in article metadata (optional — authors may use their institutional email for attribution if preferred)

The email account is deactivated when a contributor's access is revoked (voluntary departure, prolonged inactivity > 18 months without communication, or policy violation).

---

## 6. Nextcloud Access

All active contributors receive access to the AT Medical Nextcloud instance, which provides:

- **Shared reference library**: AWMF guidelines, ESC guidelines, selected textbooks (where licensed), AT Medical internal style guide
- **Author registry**: Contact details and specialty profiles for all active contributors
- **CoI declarations**: Securely stored conflict of interest declarations (access-restricted)
- **Editorial communications**: Shared folders for in-progress reviews, editorial decisions, meeting notes
- **Asset storage**: Approved images, diagrams, and media for articles (before publication to MediaWiki)

Nextcloud access uses SSO with the AT Medical identity provider. Credentials are the same as the `@wikimedica.de` email account.

---

## 7. Collaboration Privileges

### GitHub Organisation

Contributors are added to the `atmedical-wikimedica` GitHub organisation and assigned to:

- A **specialty team** (e.g., `team-kardiologie`) that has CODEOWNERS write access to the relevant specialty content directory
- A **role team** (`contributors`, `reviewers`, or `editors`) that controls PR approval permissions

### Communication Channels

- **Editorial mailing list** (`editorial@wikimedica.de`): All editors and medical advisors
- **Contributors list** (`contributors@wikimedica.de`): All active contributors
- **Specialty channels**: Optional encrypted messaging channels per specialty (AT Medical Signal/Matrix instance — future)
- **GitHub Discussions**: Platform-wide editorial discussion (public, linked to this repository)

---

## 8. Inactivity and Offboarding

- Contributors who have not made a contribution or review in **18 months** receive a check-in email.
- No response within 30 days → account placed in inactive status.
- Inactive accounts lose Nextcloud access but GitHub organisation membership is retained (read-only).
- Voluntary departure: contributor submits offboarding request to editorial@wikimedica.de; email and Nextcloud deactivated within 5 business days.
- Policy violation: Medical Director reviews; access may be suspended immediately pending investigation.
