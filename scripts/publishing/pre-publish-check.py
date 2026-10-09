#!/usr/bin/env python3
"""
pre-publish-check.py — Wikimedica Pre-Publication Checklist

Runs a comprehensive set of pre-publication checks on a Wikimedica article
before it can be promoted to 'published' status. This script is intended
to be run manually before a final merge, and as part of CI on PRs that
change article status to 'published'.

Checks performed:
  1. Metadata validation (required fields, types, allowed values)
  2. Required sections present (based on article_type)
  3. No TODO markers remaining
  4. At least one source cited (pubmed_ids or guidelines non-empty)
  5. Reviewer sign-off present (reviewers field non-empty)
  6. wikimedica_credit: true
  7. Version follows semver
  8. Updated date is not in the future

Usage:
    python scripts/publishing/pre-publish-check.py <article.md> [<article.md> ...]

Exit codes:
    0  All checks pass — article is ready for publication
    1  One or more checks failed — publication blocked
    2  Script error
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    sys.exit("ERROR: pyyaml not installed. Run: pip install pyyaml")

from datetime import date


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
TODO_RE = re.compile(r"\bTODO\b|\bFIXME\b|\bXXX\b|<!--.*?-->", re.IGNORECASE | re.DOTALL)
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")

# Required sections by article type (lowercase)
REQUIRED_SECTIONS: dict[str, list[str]] = {
    "professional": [
        "übersicht",
        "epidemiologie",
        "diagnostik",
        "therapie",
        "literatur",
    ],
    "patient": [
        "was ist das",
        "wie wird es festgestellt",
        "wie wird es behandelt",
    ],
    "consent": [
        "einleitung",
        "was wird durchgeführt",
        "mögliche risiken",
        "einwilligung",
    ],
    "discharge": [
        "diagnose",
        "medikamente",
        "nachsorge",
        "notfallkontakt",
    ],
    "pharmaka": [
        "übersicht",
        "indikationen",
        "dosierung",
        "nebenwirkungen",
        "literatur",
    ],
    "therapy": [
        "übersicht",
        "indikation",
        "durchführung",
        "literatur",
    ],
}

# Sections required for a content_kind; takes precedence over article_type.
REQUIRED_SECTIONS_BY_KIND: dict[str, list[str]] = {
    "guideline-summary": [
        "übersicht",
        "kernempfehlungen",
        "literatur",
    ],
    "qr-media-reference": [
        "medium",
        "transkript",
    ],
}

HEADING_RE = re.compile(r"^#{1,6}[ \t]+(.+?)[ \t]*$", re.MULTILINE)

# Minimum required fields for publication (in addition to all schema required fields)
PUBLISH_REQUIRED: list[str] = [
    "title", "specialty", "article_type", "status",
    "version", "authors", "created", "updated", "wikimedica_credit",
]


# ---------------------------------------------------------------------------
# Result tracking
# ---------------------------------------------------------------------------

class CheckResult:
    """Tracks pass/fail results for a single check."""

    def __init__(self, name: str, passed: bool, message: str = ""):
        self.name = name
        self.passed = passed
        self.message = message

    def __str__(self) -> str:
        icon = "✅" if self.passed else "❌"
        msg = f" — {self.message}" if self.message else ""
        return f"  {icon} {self.name}{msg}"


# ---------------------------------------------------------------------------
# Frontmatter extraction
# ---------------------------------------------------------------------------

def extract_frontmatter_and_body(file_path: Path) -> tuple[dict | None, str, int]:
    """
    Extract YAML frontmatter and body text from a Markdown file.

    Returns:
        (frontmatter_dict, body_text, frontmatter_end_line)
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: Cannot read file {file_path}: {exc}", file=sys.stderr)
        return None, "", 0

    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}, content, 0

    try:
        fm = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        return {"_yaml_error": str(exc)}, "", 0

    body = content[match.end():]
    end_line = match.group(1).count("\n") + 2
    return fm, body, end_line


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_metadata_required_fields(fm: dict) -> list[CheckResult]:
    """Check that all required fields are present and non-empty."""
    results = []
    for field in PUBLISH_REQUIRED:
        val = fm.get(field)
        passed = val is not None and val != "" and val != [] and val is not False
        results.append(CheckResult(
            f"Required field: {field}",
            passed,
            "" if passed else f"Missing or empty field '{field}'",
        ))
    return results


def check_yaml_valid(fm: dict) -> CheckResult:
    """Check that frontmatter parsed without errors."""
    if "_yaml_error" in fm:
        return CheckResult("YAML frontmatter valid", False, fm["_yaml_error"])
    return CheckResult("YAML frontmatter valid", True)


def check_status_approved_or_published(fm: dict) -> CheckResult:
    """Check that the article status is 'approved' or 'published' (not still a draft)."""
    status = fm.get("status", "")
    passed = status in ("approved", "published")
    return CheckResult(
        "Status is approved/published",
        passed,
        f"Status is '{status}'; must be 'approved' or 'published' before publishing." if not passed else "",
    )


def check_reviewers_present(fm: dict) -> CheckResult:
    """Check that at least one reviewer is listed."""
    reviewers = fm.get("reviewers", [])
    passed = isinstance(reviewers, list) and len(reviewers) > 0
    return CheckResult(
        "Reviewer(s) listed",
        passed,
        "No reviewers listed in frontmatter." if not passed else "",
    )


def check_sources_present(fm: dict) -> CheckResult:
    """Check that at least one source (PMID or guideline) is cited."""
    pmids = fm.get("pubmed_ids", []) or []
    guidelines = fm.get("guidelines", []) or []
    passed = len(pmids) > 0 or len(guidelines) > 0
    return CheckResult(
        "At least one source cited",
        passed,
        "No pubmed_ids or guidelines listed in frontmatter." if not passed else "",
    )


def check_wikimedica_credit(fm: dict) -> CheckResult:
    """Check that wikimedica_credit is set to True."""
    passed = fm.get("wikimedica_credit") is True
    return CheckResult(
        "wikimedica_credit: true",
        passed,
        "wikimedica_credit must be set to true." if not passed else "",
    )


def check_version_semver(fm: dict) -> CheckResult:
    """Check that version follows semver format."""
    version = str(fm.get("version", ""))
    passed = bool(SEMVER_RE.match(version))
    return CheckResult(
        "Version follows semver",
        passed,
        f"Version '{version}' is not valid semver (MAJOR.MINOR.PATCH)." if not passed else "",
    )


def check_updated_not_future(fm: dict) -> CheckResult:
    """Check that the updated date is not in the future."""
    updated_str = fm.get("updated", "")
    if not updated_str:
        return CheckResult("Updated date not in future", False, "Missing 'updated' field.")
    try:
        updated = date.fromisoformat(str(updated_str))
        passed = updated <= date.today()
        return CheckResult(
            "Updated date not in future",
            passed,
            f"'updated' date {updated_str} is in the future." if not passed else "",
        )
    except ValueError:
        return CheckResult("Updated date not in future", False, f"Invalid date: '{updated_str}'.")


def check_required_sections(fm: dict, body: str) -> CheckResult:
    """Check that all required sections are present as HEADINGS in the body.

    The content_kind (guideline-summary, qr-media-reference) takes precedence
    over the article_type; matching is done against heading lines only, so a
    word in running text can no longer satisfy a required section.
    """
    article_type = fm.get("article_type", "professional")
    content_kind = fm.get("content_kind", "article")
    required = REQUIRED_SECTIONS_BY_KIND.get(content_kind) or REQUIRED_SECTIONS.get(article_type, [])

    if not required:
        return CheckResult(
            "Required sections present",
            True,
            f"No section requirements defined for article_type '{article_type}'.",
        )

    headings = [h.lower() for h in HEADING_RE.findall(body)]
    missing = [section for section in required if not any(section in h for h in headings)]

    passed = len(missing) == 0
    return CheckResult(
        "Required sections present",
        passed,
        f"Missing sections: {missing}" if not passed else "",
    )


def check_no_todo_markers(body: str) -> CheckResult:
    """Check that no TODO/FIXME/XXX markers or HTML comments remain in the article body.

    Template guidance lives in HTML comments; an article that still contains
    them is not finished. Text inside fenced code blocks is ignored.
    """
    prose = re.sub(r"(```|~~~).*?\1", "", body, flags=re.DOTALL)
    comments = re.findall(r"<!--.*?-->", prose, flags=re.DOTALL)
    without_comments = re.sub(r"<!--.*?-->", "", prose, flags=re.DOTALL)
    todos = re.findall(r"\b(?:TODO|FIXME|XXX)\b", without_comments)
    problems = []
    if comments:
        problems.append(f"{len(comments)} HTML comment(s) (template guidance must be removed)")
    if todos:
        problems.append(f"{len(todos)} TODO/FIXME/XXX marker(s)")
    return CheckResult(
        "No TODO markers or leftover comments",
        not problems,
        "Found " + " and ".join(problems) + " in article body." if problems else "",
    )


# ---------------------------------------------------------------------------
# Main check runner
# ---------------------------------------------------------------------------

def run_checks(file_path: Path) -> tuple[bool, list[CheckResult]]:
    """Run all pre-publication checks on a single article file."""
    fm, body, _end_line = extract_frontmatter_and_body(file_path)

    if fm is None:
        return False, [CheckResult("File readable", False, f"Cannot read file: {file_path}")]

    results: list[CheckResult] = []

    results.append(check_yaml_valid(fm))
    if not results[-1].passed:
        return False, results  # Cannot run further checks with broken YAML

    results.extend(check_metadata_required_fields(fm))
    results.append(check_status_approved_or_published(fm))
    results.append(check_reviewers_present(fm))
    results.append(check_sources_present(fm))
    results.append(check_wikimedica_credit(fm))
    results.append(check_version_semver(fm))
    results.append(check_updated_not_future(fm))
    results.append(check_required_sections(fm, body))
    results.append(check_no_todo_markers(body))

    all_passed = all(r.passed for r in results)
    return all_passed, results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run pre-publication checks on Wikimedica article files."
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="One or more article Markdown files to check.",
    )
    args = parser.parse_args()

    overall_pass = True

    for file_path in args.files:
        if not file_path.exists():
            print(f"\n❌ File not found: {file_path}")
            overall_pass = False
            continue

        passed, results = run_checks(file_path)
        overall_pass = overall_pass and passed

        status_icon = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status_icon}  {file_path}")
        for result in results:
            print(str(result))

    print("\n" + ("=" * 60))
    if overall_pass:
        print("✅ All pre-publication checks passed.")
    else:
        print("❌ Pre-publication checks failed. Fix the issues above before publishing.")
    print("=" * 60)

    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
