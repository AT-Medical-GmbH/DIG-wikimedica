#!/usr/bin/env python3
"""
check-status-transitions.py — Wikimedica lifecycle guard for pull requests

validate-metadata.py looks at ONE file; it cannot know where an article came
from. This script compares the working tree against a base ref (default
origin/main) and enforces the lifecycle defined in
data/metadata/article-schema.yaml (`lifecycle.transitions`):

  * a status change must follow an allowed transition
        draft -> in-review -> approved -> published -> archived
        published -> in-review (update needed); in-review -> draft (revision)
  * a NEW article may only be introduced as draft / in-review
    (nobody can slip a brand-new file in as `published`)
  * approved / published content is FROZEN: any change to body or frontmatter
    requires a status change first (the sign-off covered the old text).
    Exception: `safety_hold` can be toggled at any time (patient-safety brake)
  * approved / published articles are never deleted (archive or retract them)
  * the slug (= file name) of an approved / published article is immutable;
    moving it to another directory with the same file name is fine

Usage:
    python scripts/validation/check-status-transitions.py [--base-ref origin/main] [paths...]

Exit codes:
    0  all changes follow the lifecycle
    1  at least one violation
    2  script / git error
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROZEN_STATUSES = {"approved", "published"}
# Keys that may change on frozen content without a status change. safety_hold is
# the emergency brake of the peer-review policy (section "Urgent Patient Safety
# Concerns") and must be settable on a published article at any time.
FREEZE_EXEMPT_KEYS = {"safety_hold"}


def load_validator():
    """Load validate-metadata.py (hyphenated name -> not importable normally)."""
    spec = importlib.util.spec_from_file_location("validate_metadata", HERE / "validate-metadata.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["validate_metadata"] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


vm = load_validator()


# ---------------------------------------------------------------------------
# Pure rules (unit-tested without git)
# ---------------------------------------------------------------------------

def check_transition(old: str | None, new: str | None, lifecycle: dict) -> str | None:
    """Return an error message if old -> new is not allowed, else None."""
    if old == new:
        return None
    statuses = lifecycle.get("statuses", [])
    if new not in statuses:
        return f"unknown status '{new}'"
    allowed = lifecycle.get("transitions", {}).get(old, [])
    if old not in statuses:
        return f"previous status '{old}' is unknown"
    if new not in allowed:
        opts = ", ".join(allowed) if allowed else "none (terminal status)"
        return f"transition '{old}' -> '{new}' is not allowed (allowed from '{old}': {opts})"
    return None


def frozen_view(parsed):
    """(frontmatter without exempt keys, body) — what the sign-off covered."""
    fm, body = parsed
    return {k: v for k, v in fm.items() if k not in FREEZE_EXEMPT_KEYS}, body


def check_new_article(new: str | None, lifecycle: dict) -> str | None:
    initial = lifecycle.get("initial_statuses", ["draft"])
    if new not in initial:
        return (f"new articles must start as {' or '.join(repr(s) for s in initial)}, "
                f"not '{new}'")
    return None


# ---------------------------------------------------------------------------
# Git plumbing
# ---------------------------------------------------------------------------

def git(*args: str, cwd: Path | None = None, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8"
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def changed_files(base: str, roots: list[str], cwd: Path | None) -> list[tuple[str, str, str | None]]:
    """(status_letter, path, old_path_for_renames) for Markdown files vs. merge-base."""
    out = git("diff", "--name-status", "-M", base, "--", *roots, cwd=cwd)
    untracked = git("ls-files", "--others", "--exclude-standard", "--", *roots, cwd=cwd)
    entries: list[tuple[str, str, str | None]] = []
    for line in out.splitlines():
        parts = line.split("\t")
        letter = parts[0][0]
        if letter == "R":
            entries.append(("R", parts[2], parts[1]))
        else:
            entries.append((letter, parts[1], None))
    entries += [("A", p, None) for p in untracked.splitlines()]
    return [e for e in entries if e[1].endswith(".md")]


def read_at(ref: str, path: str, cwd: Path | None) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"], cwd=cwd, capture_output=True, text=True, encoding="utf-8"
    )
    return result.stdout if result.returncode == 0 else None


def parse_text(text: str | None, path: str):
    """Parse article text through the validator's parser (via a temp-free path)."""
    if text is None:
        return None
    match = vm.FRONTMATTER_RE.match(text)
    if not match:
        return None
    import yaml
    try:
        fm = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return None
    return fm, text[match.end():]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check lifecycle status transitions vs. a base ref.")
    parser.add_argument("paths", nargs="*", default=["content"], help="Paths to check (default: content).")
    parser.add_argument("--base-ref", default="origin/main", help="Base ref (default: origin/main).")
    parser.add_argument("--schema", type=Path, default=vm.SCHEMA_PATH)
    parser.add_argument("--repo", type=Path, default=None, help="Repository root (default: cwd).")
    args = parser.parse_args(argv)

    schema = vm.load_schema(args.schema)
    lifecycle = schema["lifecycle"]
    try:
        base = git("merge-base", args.base_ref, "HEAD", cwd=args.repo).strip()
        entries = changed_files(base, args.paths, args.repo)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    problems: list[str] = []
    checked = 0
    repo = args.repo or Path(".")

    for letter, path, old_path in entries:
        if "templates" in Path(path).parts:
            continue
        old_ref_path = old_path or path
        old = parse_text(read_at(base, old_ref_path, args.repo), old_ref_path) if letter != "A" else None
        new = None
        if letter != "D":
            try:
                new = parse_text((repo / path).read_text(encoding="utf-8"), path)
            except OSError:
                new = None

        if old is None and new is None:
            continue  # not an article (no frontmatter) on either side
        checked += 1

        old_status = old[0].get("status") if old else None
        new_status = new[0].get("status") if new else None

        if letter == "D":
            if old_status in FROZEN_STATUSES:
                problems.append(f"{path}: deleting a '{old_status}' article is not allowed — "
                                "archive (status: archived) or retract it instead.")
            continue

        if old is None:  # new article
            msg = check_new_article(new_status, lifecycle)
            if msg:
                problems.append(f"{path}: {msg}")
            continue

        if letter == "R" and old_status in FROZEN_STATUSES \
                and Path(path).stem != Path(old_ref_path).stem:
            problems.append(f"{path}: renaming a '{old_status}' article changes its slug "
                            f"(was {old_ref_path}); slugs of approved/published articles are immutable.")

        msg = check_transition(old_status, new_status, lifecycle)
        if msg:
            problems.append(f"{path}: {msg}")
        elif old_status == new_status and old_status in FROZEN_STATUSES \
                and frozen_view(old) != frozen_view(new):
            problems.append(f"{path}: '{old_status}' content is frozen — changing it requires "
                            "setting status to 'in-review' (with a version bump) and a new review.")

    for p in problems:
        print(f"ERROR  {p}")
    print(f"\n--- Status transition check ---\nArticles examined: {checked}\n"
          f"Violations:        {len(problems)}  (base: {args.base_ref} @ {base[:10]})")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
