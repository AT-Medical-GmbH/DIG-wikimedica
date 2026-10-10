# Security Policy

## Reporting a vulnerability

Please do **not** open a public issue for security problems.

- Use GitHub's private vulnerability reporting for this repository
  (Security → Report a vulnerability), or
- write to security@wikimedica.de (placeholder mailbox — to be confirmed by the owner before
  go-live, see the go-live checklist).

We acknowledge reports within 3 working days and aim to give a first assessment within 10.
Please include affected URL or file, steps to reproduce and impact. Do not access data that is
not yours, and do not run denial-of-service or social-engineering tests.

## Scope

In scope: the repository (code, workflows, scripts), the deployment configuration, and
wikimedica.de once it is live. Medical content errors are **not** security reports — send them
to editorial@wikimedica.de (they are handled as patient-safety issues, see
`docs/editorial/content-lifecycle.md`, "safety hold").

## Handling

Incident process, severity classes and communication: [`docs/operations/security-response.md`](docs/operations/security-response.md).
Update and patch policy: [`docs/operations/update-policy.md`](docs/operations/update-policy.md).

## Rules for contributors

- Never commit secrets, tokens, keys, `.env` files or personal data. CI scans for them.
- Use placeholders (`REPLACE_WITH_…`) and document the variable in `infra/env/.env.example`.
- Production deploys only release tags on `main`; no workflow runs deployment from a pull request.
