#!/usr/bin/env python3
"""
generate-review-report.py — Wikimedica Content Review Status Report

Scans the content/ directory for articles with YAML frontmatter,
groups them by specialty and status, calculates staleness (articles
not updated in >6 months), and produces a Markdown report.

Usage:
    python scripts/review/generate-review-report.py [--output PATH] [--stale-days N]

Output:
    Markdown report (printed to stdout or written to --output path)

Exit codes:
    0  Report generated successfully
    1  Script error
"""

import argparse
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("ERROR: pyyaml not installed. Run: pip install pyyaml")

import re


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONTENT_DIR = Path("content")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
DEFAULT_STALE_DAYS = 180  # 6 months

STATUSES = ["draft", "in-review", "advisor-review", "approved", "published", "archived", "retracted"]

SPECIALTIES = [
    "Innere Medizin", "Kardiologie", "Pneumologie", "Gastroenterologie",
    "Nephrologie", "Endokrinologie/Diabetologie", "Hämatologie/Onkologie",
    "Infektiologie", "Rheumatologie", "Neurologie", "Psychiatrie",
    "Dermatologie", "Pädiatrie", "Gynäkologie/Geburtshilfe", "Urologie",
    "Orthopädie/Unfallchirurgie", "Augenheilkunde", "Anästhesiologie", "Intensivmedizin",
    "Notfallmedizin", "Chirurgie", "Radiologie", "Labormedizin",
    "Pharmakologie", "Palliativmedizin", "Prävention/Public Health",
    "Gender-Medizin",
]


# ---------------------------------------------------------------------------
# Frontmatter extraction
# ---------------------------------------------------------------------------

def extract_frontmatter(file_path: Path) -> dict | None:
    """Parse YAML frontmatter from a Markdown file. Returns dict or None."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError:
        return None

    match = FRONTMATTER_RE.match(content)
    if not match:
        return None

    try:
        parsed = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None

    return parsed if isinstance(parsed, dict) else None


# ---------------------------------------------------------------------------
# Staleness check
# ---------------------------------------------------------------------------

def is_stale(frontmatter: dict, stale_days: int) -> bool:
    """Return True if the article has not been updated within stale_days."""
    updated_str = frontmatter.get("updated")
    if not updated_str:
        return True  # Missing updated date → treat as stale

    try:
        updated = date.fromisoformat(str(updated_str))
    except ValueError:
        return True

    threshold = date.today() - timedelta(days=stale_days)
    return updated < threshold


# ---------------------------------------------------------------------------
# Article scanning
# ---------------------------------------------------------------------------

def scan_content(content_dir: Path, stale_days: int) -> list[dict]:
    """
    Recursively scan content_dir for Markdown articles with frontmatter.
    Returns a list of dicts with article metadata for reporting.
    """
    results = []
    for md_file in sorted(content_dir.rglob("*.md")):
        # Skip README files and templates
        if md_file.name.lower() in ("readme.md",) or "templates" in md_file.parts:
            continue

        fm = extract_frontmatter(md_file)
        if not fm:
            continue

        stale = is_stale(fm, stale_days)
        # Only flag stale for published/approved articles (drafts expected to be in-progress)
        active_status = fm.get("status") in ("published", "approved")

        results.append({
            "path": md_file,
            "title": fm.get("title", md_file.stem),
            "specialty": fm.get("specialty", "Unknown"),
            "article_type": fm.get("article_type", "unknown"),
            "status": fm.get("status", "unknown"),
            "updated": fm.get("updated", ""),
            "version": fm.get("version", ""),
            "stale": stale and active_status,
        })

    return results


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(articles: list[dict], stale_days: int) -> str:
    """Generate a Markdown review status report from article data."""
    today = date.today().isoformat()
    lines: list[str] = []

    # Header
    lines += [
        "# Wikimedica Content Review Status Report",
        "",
        f"**Generated:** {today}",
        f"**Stale threshold:** {stale_days} days ({stale_days // 30} months)",
        f"**Total articles scanned:** {len(articles)}",
        "",
        "---",
        "",
    ]

    # Overall status counts
    status_counts: dict[str, int] = defaultdict(int)
    for article in articles:
        status_counts[article["status"]] += 1

    lines += ["## Overall Status Summary", ""]
    lines += ["| Status | Count |", "|---|---|"]
    for status in STATUSES:
        count = status_counts.get(status, 0)
        if count > 0:
            lines.append(f"| {status} | {count} |")
    lines += ["", "---", ""]

    # Stale articles
    stale_articles = [a for a in articles if a["stale"]]
    lines += [
        f"## ⚠️ Stale Articles ({len(stale_articles)})",
        "",
        f"*Articles with `published` or `approved` status not updated in >{stale_days} days.*",
        "",
    ]
    if stale_articles:
        lines += ["| Title | Specialty | Status | Last Updated | Path |", "|---|---|---|---|---|"]
        for a in stale_articles:
            path_str = str(a["path"])
            lines.append(
                f"| {a['title'][:60]} | {a['specialty']} | {a['status']} "
                f"| {a['updated']} | `{path_str}` |"
            )
    else:
        lines.append("*No stale articles found.*")
    lines += ["", "---", ""]

    # Per-specialty breakdown
    lines += ["## Breakdown by Specialty", ""]

    specialty_articles: dict[str, list[dict]] = defaultdict(list)
    for article in articles:
        specialty_articles[article["specialty"]].append(article)

    # Show known specialties first, then any others
    ordered_specialties = [s for s in SPECIALTIES if s in specialty_articles]
    other_specialties = [s for s in specialty_articles if s not in SPECIALTIES]

    for specialty in ordered_specialties + other_specialties:
        articles_in_specialty = specialty_articles[specialty]
        stale_count = sum(1 for a in articles_in_specialty if a["stale"])
        stale_tag = f" ⚠️ {stale_count} stale" if stale_count > 0 else ""

        lines += [
            f"### {specialty} ({len(articles_in_specialty)} articles{stale_tag})",
            "",
            "| Title | Type | Status | Updated | Version |",
            "|---|---|---|---|---|",
        ]
        for a in sorted(articles_in_specialty, key=lambda x: x["status"]):
            stale_flag = " ⚠️" if a["stale"] else ""
            lines.append(
                f"| {a['title'][:55]}{stale_flag} | {a['article_type']} "
                f"| {a['status']} | {a['updated']} | {a['version']} |"
            )
        lines.append("")

    # Footer
    lines += [
        "---",
        "",
        "*This report was generated automatically by `scripts/review/generate-review-report.py`.*",
        "*Wikimedica / AT Medical Digital Solutions · wikimedica.de*",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate Wikimedica content review status report."
    )
    parser.add_argument(
        "--content-dir",
        type=Path,
        default=CONTENT_DIR,
        help=f"Root content directory to scan (default: {CONTENT_DIR})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write report to this file path (default: print to stdout)",
    )
    parser.add_argument(
        "--stale-days",
        type=int,
        default=DEFAULT_STALE_DAYS,
        help=f"Days without update to consider an article stale (default: {DEFAULT_STALE_DAYS})",
    )
    args = parser.parse_args()

    if not args.content_dir.exists():
        print(f"ERROR: Content directory not found: {args.content_dir}", file=sys.stderr)
        return 1

    articles = scan_content(args.content_dir, args.stale_days)
    report = generate_report(articles, args.stale_days)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(report)

    # Exit with non-zero if there are stale articles (signals CI to open an issue)
    stale_count = sum(1 for a in articles if a["stale"])
    return 1 if stale_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
