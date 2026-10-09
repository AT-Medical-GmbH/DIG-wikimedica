# Contributing to Wikimedica

> This repository is source-available, not open source (see [`LICENSE`](LICENSE)).
> You may propose contributions; use or reuse of the contents needs written permission.

## Medical content

1. Read [`docs/authors/author-onboarding-model.md`](docs/authors/author-onboarding-model.md) and apply via
   [`forms/author-application/`](forms/author-application/author-application-form.md).
2. Copy a template from `content/templates/`; fill every required frontmatter field.
3. Start with `status: draft`. Only reviewers change the status — never the author.
4. Rules that are checked by CI and by reviewers:
   - own wording, no copied text; every statement needs a source you actually read;
   - no dosage recommendations in drafts without Medical-Advisor review (`risk_level: high`);
   - assess sex/gender relevance (`sex_gender_relevance`);
   - declare AI assistance (`ai_assisted`, `ai_assistance_description`) — AI text is never published without human review;
   - the slug (file name) is permanent.
5. Run `python3 scripts/validation/validate-metadata.py` locally, open a pull request, request review per
   [`docs/editorial/peer-review-policy.md`](docs/editorial/peer-review-policy.md).

## Code, infrastructure and documentation

- Branches: `feature/…`, `fix/…`, `docs/…`; pull requests target `main` (protected, review required).
- Commit style: `<type>(<scope>): <summary>` with `feat|fix|docs|ci|chore|refactor|test`.
- Before pushing: `python3 -m pytest -q`, `shellcheck infra/deploy/*.sh`, markdownlint and cspell (see README).
- Infrastructure changes are tested on staging first; production changes ship only as a release tag.
- Never commit secrets or personal data.

## Conduct

See [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
