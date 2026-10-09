# License Decision Needed — Wikimedica

**Document version:** 1.0
**Owner:** AT Medical GmbH — Management / Legal (decision) · Digital Solutions — Engineering (preparation)
**Last updated:** 2026-10-09
**Status:** Active — **open owner decision** (🧭 DEC-2)

---

## 1. Why this document exists

There is a **live contradiction** between the repository's `LICENSE` file and
`README.md`. On a publicly visible repository this is a real legal-clarity
defect: the effective license a reader infers depends on which paragraph they
read. Per the handover and ATMED governance, **engineering does not change an
existing `LICENSE` without an explicit owner decision**. This document records
the conflict, lays out the options, and states exactly what engineering changed
versus what remains the owner's decision.

---

## 2. The contradiction (evidence)

- **`LICENSE`** (authoritative file): *"AT Medical Proprietary Source-Available
  License v1.0 — Copyright (c) 2026 AT Medical GmbH. All rights reserved."*
  Viewing/evaluation allowed; use, modification, deployment, redistribution,
  commercialisation prohibited without written permission.
- **`README.md`** contains **two different, conflicting license statements**
  (the file was assembled from two drafts and also duplicates its title,
  "License", and "Contributing" sections):
  - one block: **content under CC BY-SA 4.0**, code "© AT Medical Digital
    Solutions, all rights reserved";
  - another block: the **entire repository** under the **AT Medical Proprietary
    Source-Available License v1.0**, with adaptation/redistribution not allowed.
- **`data/metadata/article-schema.yaml`** defaults each article's `licence`
  field to **CC BY-SA 4.0**.

So the repo simultaneously implies "proprietary, all rights reserved" **and**
"content is CC BY-SA 4.0". These cannot both be true for the same artifacts.

---

## 3. Options for the owner

### Option 1 — Proprietary source-available for everything

Keep `LICENSE` as-is for code **and** content. Simple, maximally protective,
grants no rights away.
*Trade-off:* incompatible with a "freely accessible / wiki-style reusable
knowledge" positioning and with the schema's CC BY-SA default; external
contribution/reuse is effectively blocked.

### Option 2 — Apache-2.0 (code) + CC BY-SA 4.0 (content)

Standard open split: permissive code license, share-alike content license.
*Trade-off:* this is an **open-source / open-content** switch — it grants broad
reuse and redistribution rights that cannot be revoked later. Matches a "free
public knowledge" vision but gives up proprietary control.

### Option 3 — Split: proprietary/source-available code + CC content

Code stays proprietary/source-available; **content** is CC BY-SA 4.0 **or**
CC BY-NC-SA 4.0 (NC = non-commercial).
*Trade-off:* keeps platform/code control while allowing (optionally
non-commercial) reuse of medical content; needs a clear per-file boundary
(what is "code" vs. "content") and consistent per-article `license` metadata.

---

## 4. Recommendation stance (engineering, non-binding)

For **production preparation**, the safe default is **grant no rights away and
make no open-source switch without an explicit owner decision** — i.e. remain on
Option 1 *until* the owner deliberately chooses otherwise. Whichever option is
chosen, the following must then be made consistent: `LICENSE`, `README.md`,
`CONTRIBUTING.md`, and the schema's `license` default/field.

If the "freely accessible medical knowledge" vision in the README is a genuine
product goal, **Option 3** is the most likely fit (platform protected, content
reusable) — but that is an owner decision, not an engineering one.

---

## 5. What engineering changed vs. what is still open

- 🛠️ **Done (no rights changed):** the `README.md` is to be de-duplicated so it
  no longer asserts a license that contradicts `LICENSE`; until the decision is
  made the README defers to `LICENSE` as authoritative. The authoritative
  `LICENSE` file itself is **left untouched**.
- 🧭 **Open (owner):** choose Option 1/2/3; then engineering updates `LICENSE`
  (if changed), `README.md`, `CONTRIBUTING.md`, and the schema `license` field
  **consistently** in one reviewed change.

---

## 6. Decision log

| Date | Decision | Decided by |
|---|---|---|
| *pending* | *Option 1 / 2 / 3* | AT Medical GmbH |
