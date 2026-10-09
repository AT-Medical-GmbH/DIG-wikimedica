#!/usr/bin/env python3
"""
validate-metadata.py — Wikimedica Article Frontmatter Validator

Validates YAML frontmatter (and a few body heuristics) of Wikimedica Markdown
articles against the canonical schema in data/metadata/article-schema.yaml.

What it enforces (beyond per-field type/enum/pattern checks):
  * status gating     — fields such as reviewers, next_review, license,
                        change_summary, source_notes are mandatory from
                        approval on (see `required_for_status` in the schema)
  * risk governance   — pharmaka/therapy/Notfall/Intensiv/Onkologie must be
                        risk_level high; high risk needs a Medical Advisor
                        sign-off (name + date) who is not an author
  * review integrity  — reviewer must not be the main author; at least one
                        reviewer independent of all authors
  * AI declaration    — ai_assisted: true requires ai_assistance_description
  * sex/gender review — sex_gender_relevance must be assessed before approval
  * patient content   — audience/reading level + heuristic warnings for
                        individual-instruction phrasing, dosages, readability

Usage:
    python scripts/validation/validate-metadata.py [options] <files-or-dirs...>

    --templates   validate content/templates/* in STRUCTURE mode (see below)
    --strict      treat warnings as errors
    --schema PATH use a different schema file

Template handling:
    Files under content/templates/ are blank scaffolds and are SKIPPED in the
    normal mode (so editing a template never turns CI red). With --templates
    they are checked structurally: every required schema key must be present,
    no unknown keys, and article_type must be valid.

Exit codes:
    0  All files valid (warnings allowed unless --strict)
    1  One or more validation errors (or warnings with --strict)
    2  Script error (missing schema, unreadable file, etc.)

Dependencies:
    pip install pyyaml
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    sys.exit("ERROR: pyyaml not installed. Run: pip install pyyaml")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCHEMA_PATH = Path("data/metadata/article-schema.yaml")
FRONTMATTER_RE = re.compile(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", re.DOTALL)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
ICD10_RE = re.compile(r"^[A-TV-Z]\d{2}(\.(\d{1,2}[-+*!]?|-))?$")
ATC_RE = re.compile(r"^[A-Z]\d{2}[A-Z]{2}\d{2}$")
PMID_RE = re.compile(r"^\d{1,9}$")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)

# Statuses from which the article counts as "approved or beyond".
APPROVED_PLUS = {"approved", "published"}

# Heuristics for patient texts (warnings only — a human reviewer decides).
DOSAGE_RE = re.compile(r"\b\d+(?:[.,]\d+)?\s?(?:mg|µg|mcg|g|ml|IE|I\.E\.)\b", re.IGNORECASE)
INSTRUCTION_PHRASES = (
    "nehmen sie", "setzen sie", "erhöhen sie", "reduzieren sie",
    "verdoppeln sie", "halbieren sie", "ihre dosis", "ihre dosierung",
)
READABILITY_MIN_SENTENCES = 5
READABILITY_WARN_BELOW = 50.0  # Flesch-Amstad: < 50 = difficult for lay readers


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    """A single validation finding (error or warning)."""

    file_path: Path
    line: int | None
    field: str
    message: str
    level: str = "ERROR"  # ERROR | WARN

    def __str__(self) -> str:
        loc = f":{self.line}" if self.line else ""
        return f"{self.level:<5}  {self.file_path}{loc}  [{self.field}]  {self.message}"


@dataclass
class Article:
    """A parsed Markdown article."""

    path: Path
    frontmatter: dict[str, Any] | None
    body: str
    fm_text: str = ""
    yaml_error: str | None = None
    findings: list[Finding] = field(default_factory=list)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "ERROR"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "WARN"]


# ---------------------------------------------------------------------------
# Schema loading
# ---------------------------------------------------------------------------

def load_schema(schema_path: Path) -> dict[str, Any]:
    """Load the article schema; returns the full document (fields, lifecycle, risk)."""
    if not schema_path.exists():
        print(f"ERROR: Schema file not found: {schema_path}", file=sys.stderr)
        sys.exit(2)
    with schema_path.open(encoding="utf-8") as fh:
        schema = yaml.safe_load(fh)
    if not isinstance(schema, dict) or "fields" not in schema:
        print("ERROR: Schema file missing 'fields' key.", file=sys.stderr)
        sys.exit(2)
    schema.setdefault("lifecycle", {})
    schema.setdefault("risk", {})
    return schema


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_article(path: Path) -> Article:
    """Read a Markdown file and split it into frontmatter and body."""
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return Article(path=path, frontmatter=None, body="")

    match = FRONTMATTER_RE.match(content)
    if not match:
        return Article(path=path, frontmatter=None, body=content)

    fm_text = match.group(1)
    body = content[match.end():]
    try:
        parsed = yaml.safe_load(fm_text)
    except yaml.YAMLError as exc:
        return Article(path, {}, body, fm_text, yaml_error=str(exc))
    if not isinstance(parsed, dict):
        parsed = {}
    return Article(path, parsed, body, fm_text)


def key_line(fm_text: str, key: str) -> int | None:
    """1-based file line of a top-level frontmatter key (line 1 is the opening ---)."""
    for idx, line in enumerate(fm_text.splitlines(), start=2):
        if re.match(rf"^{re.escape(key)}\s*:", line):
            return idx
    return None


def normalize_dates(fm: dict[str, Any], schema_fields: dict[str, Any]) -> None:
    """PyYAML turns an unquoted 2026-01-31 into a date object; use ISO strings."""
    for name, spec in schema_fields.items():
        if spec.get("format") == "YYYY-MM-DD" and isinstance(fm.get(name), date):
            fm[name] = fm[name].isoformat()
    for entry in fm.get("reviewers") or []:
        if isinstance(entry, dict) and isinstance(entry.get("reviewed_date"), date):
            entry["reviewed_date"] = entry["reviewed_date"].isoformat()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_blank(value: Any) -> bool:
    """None, empty/whitespace string, empty list/dict."""
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def norm_name(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()


def names_of(entries: Any) -> list[str]:
    """Normalised names of authors/reviewers entries."""
    out: list[str] = []
    for entry in entries or []:
        if isinstance(entry, dict) and not is_blank(entry.get("name")):
            out.append(norm_name(entry["name"]))
    return out


def all_specialties(fm: dict[str, Any]) -> list[str]:
    result = []
    if isinstance(fm.get("specialty"), str):
        result.append(fm["specialty"])
    for item in fm.get("secondary_specialties") or []:
        if isinstance(item, str):
            result.append(item)
    return result


def strip_markup(body: str) -> str:
    """Prose-only text for readability heuristics (no comments, code, tables, headings)."""
    text = HTML_COMMENT_RE.sub(" ", body)
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "|", ">", "---", "*Dieser")):
            continue
        stripped = re.sub(r"^[-*\d.]+\s+", "", stripped)
        stripped = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", stripped)
        stripped = re.sub(r"[*_`]", "", stripped)
        lines.append(stripped)
    return " ".join(lines)


def count_syllables(word: str) -> int:
    """Rough German syllable count: groups of consecutive vowels."""
    groups = re.findall(r"[aeiouyäöü]+", word.lower())
    return max(1, len(groups))


def flesch_amstad(text: str) -> tuple[float, int] | None:
    """Flesch reading ease, German calibration (Amstad). Returns (score, sentences)."""
    sentences = [s for s in re.split(r"[.!?]+(?:\s|$)", text) if s.strip()]
    words = re.findall(r"[A-Za-zÄÖÜäöüß]+", text)
    if len(sentences) < READABILITY_MIN_SENTENCES or not words:
        return None
    asl = len(words) / len(sentences)
    asw = sum(count_syllables(w) for w in words) / len(words)
    return 180.0 - asl - 58.5 * asw, len(sentences)


# ---------------------------------------------------------------------------
# Validation — per-field
# ---------------------------------------------------------------------------

def validate_field(name: str, spec: dict[str, Any], value: Any, add) -> None:
    """Type / enum / pattern / format / list-item checks for one present field."""
    type_map = {"str": str, "int": int, "list": list, "bool": bool, "dict": dict}
    expected = type_map.get(spec.get("type", ""))
    if expected and not isinstance(value, expected):
        add(name, f"Expected type '{spec['type']}', got '{type(value).__name__}' "
                  f"(value: {repr(value)[:60]})")
        return

    if spec.get("type") == "str" and isinstance(value, str) and is_blank(value):
        return  # blank optional strings are treated as "not set"

    allowed = spec.get("values")
    if allowed is not None and value not in allowed:
        add(name, f"Value '{value}' is not in allowed values: {allowed}")

    pattern = spec.get("pattern")
    if pattern and isinstance(value, str) and not re.match(pattern, value):
        add(name, f"Value '{value}' does not match required pattern {pattern}")

    if spec.get("format") == "YYYY-MM-DD" and isinstance(value, str):
        if not DATE_RE.match(value):
            add(name, f"Expected ISO 8601 date (YYYY-MM-DD), got '{value}'.")
        else:
            try:
                date.fromisoformat(value)
            except ValueError:
                add(name, f"'{value}' is not a valid calendar date.")

    if isinstance(value, list):
        min_len = spec.get("min_length")
        if min_len and len(value) < min_len:
            add(name, f"List must have at least {min_len} item(s); got {len(value)}.")
        validate_items(name, spec, value, add)


def validate_items(name: str, spec: dict[str, Any], items: list, add) -> None:
    item_type = spec.get("item_type")
    item_values = spec.get("item_values")
    for idx, item in enumerate(items):
        where = f"{name}[{idx}]"
        if item_type == "str" and not isinstance(item, str):
            add(name, f"{where}: expected string, got {type(item).__name__}.")
        elif item_type == "pmid":
            if isinstance(item, bool) or not PMID_RE.match(str(item)):
                add(name, f"{where}: '{item}' is not a valid PubMed ID (digits only).")
        elif item_type == "dict":
            if not isinstance(item, dict):
                add(name, f"{where}: expected a mapping, got {type(item).__name__}.")
                continue
            for req in spec.get("item_required", []):
                if is_blank(item.get(req)):
                    add(name, f"{where}: missing required key '{req}'.")
        if item_values is not None and item not in item_values:
            add(name, f"{where}: '{item}' is not in allowed values: {item_values}")
    if item_type == "pmid":
        seen: set[str] = set()
        for item in items:
            if str(item) in seen:
                add(name, f"Duplicate PubMed ID {item}.", "WARN")
            seen.add(str(item))


# ---------------------------------------------------------------------------
# Validation — whole article
# ---------------------------------------------------------------------------

def validate_article(
    article: Article, schema: dict[str, Any], *, template_mode: bool = False
) -> list[Finding]:
    """Validate one parsed article. Findings are also stored on the article."""
    path = article.path
    findings = article.findings
    fm = article.frontmatter or {}
    fields: dict[str, Any] = schema["fields"]
    end_line = article.fm_text.count("\n") + 2 if article.fm_text else None

    def add(field_name: str, message: str, level: str = "ERROR") -> None:
        base = field_name.split("[")[0]
        line = key_line(article.fm_text, base) or end_line
        findings.append(Finding(path, line, field_name, message, level))

    if article.yaml_error:
        add("YAML", f"YAML parse error: {article.yaml_error}")
        return findings

    if template_mode:
        return validate_template(article, schema, add)

    normalize_dates(fm, fields)
    # A deprecated alias (licence) satisfies its canonical field (license).
    for name, spec in fields.items():
        alias = spec.get("alias_of")
        if alias and not is_blank(fm.get(name)) and is_blank(fm.get(alias)):
            fm[alias] = fm[name]
    status = fm.get("status")
    gated = status  # status value used for required_for_status

    # ---- per-field checks -------------------------------------------------
    for name, spec in fields.items():
        value = fm.get(name)
        if spec.get("deprecated") and value is not None:
            add(name, f"'{name}' is deprecated; use '{spec.get('alias_of')}'.", "WARN")

        if value is None:
            if spec.get("required"):
                add(name, f"Required field '{name}' is missing.")
            elif gated in (spec.get("required_for_status") or []):
                add(name, f"Field '{name}' is required for status '{gated}'.")
            continue

        if spec.get("required") and spec.get("type") == "str" \
                and not spec.get("allow_blank") and is_blank(value):
            add(name, f"Required field '{name}' must not be empty.")
            continue

        if gated in (spec.get("required_for_status") or []) and is_blank(value):
            add(name, f"Field '{name}' must not be empty for status '{gated}'.")
            continue

        validate_field(name, spec, value, add)

    unknown = sorted(set(fm) - set(fields))
    for key in unknown:
        add(key, f"Unknown frontmatter key '{key}' (typo? add it to the schema if intended).", "WARN")

    # ---- cross-field checks ----------------------------------------------
    validate_cross_field(article, fm, schema, add)
    if fm.get("article_type") == "patient":
        validate_patient_text(article, fm, add)
    return findings


def validate_cross_field(article: Article, fm: dict[str, Any], schema: dict[str, Any], add) -> None:
    status = fm.get("status")
    article_type = fm.get("article_type")
    risk_cfg = schema.get("risk", {})

    # slug must equal file stem (importer idempotency key)
    slug = fm.get("slug")
    if isinstance(slug, str) and article.path.stem.lower() != "readme" \
            and slug != article.path.stem:
        add("slug", f"slug '{slug}' must equal the file name '{article.path.stem}'.")

    # version: semver; published >= 1.0.0
    version = fm.get("version")
    if version is not None:
        if not SEMVER_RE.match(str(version)):
            add("version", f"Version '{version}' must follow semver (MAJOR.MINOR.PATCH).")
        elif status == "published" and int(str(version).split(".")[0]) < 1:
            add("version", "Published articles must have version >= 1.0.0.")

    # dates
    created, updated, next_review = fm.get("created"), fm.get("updated"), fm.get("next_review")
    try:
        if created and updated and date.fromisoformat(str(updated)) < date.fromisoformat(str(created)):
            add("updated", f"'updated' ({updated}) cannot be earlier than 'created' ({created}).")
        if updated and next_review and status in APPROVED_PLUS \
                and date.fromisoformat(str(next_review)) <= date.fromisoformat(str(updated)):
            add("next_review", f"'next_review' ({next_review}) must be after 'updated' ({updated}).")
        if next_review and status == "published" \
                and date.fromisoformat(str(next_review)) < date.today():
            add("next_review", f"Review overdue: next_review {next_review} is in the past "
                               "(stale content — see generate-review-report.py).", "WARN")
    except ValueError:
        pass  # malformed dates are reported by the field check

    # consent / discharge
    if article_type in ("consent", "discharge") and is_blank(fm.get("procedure")):
        add("procedure", f"Article type '{article_type}' requires a 'procedure' field.")
    module_type = fm.get("module_type")
    if module_type and article_type in ("consent", "discharge") and module_type != article_type:
        add("module_type", f"module_type '{module_type}' must equal article_type '{article_type}'.")

    # wikimedica_credit
    if "wikimedica_credit" in fm and fm["wikimedica_credit"] is not True:
        add("wikimedica_credit", "wikimedica_credit must be true (boolean).")

    # license alias consistency
    if not is_blank(fm.get("license")) and not is_blank(fm.get("licence")) \
            and fm["license"] != fm["licence"]:
        add("licence", "Both 'license' and deprecated 'licence' are set with different values.")

    # ---- AI declaration ----------------------------------------------------
    if fm.get("ai_assisted") is True and is_blank(fm.get("ai_assistance_description")):
        add("ai_assistance_description",
            "ai_assisted is true: describe tool, task and human verification.")
    if fm.get("ai_assisted") is False and not is_blank(fm.get("ai_assistance_description")):
        add("ai_assisted", "ai_assistance_description is set but ai_assisted is false.", "WARN")

    # ---- risk governance ---------------------------------------------------
    specialties = all_specialties(fm)
    reasons = []
    if article_type in risk_cfg.get("high_risk_article_types", []):
        reasons.append(f"article_type '{article_type}'")
    reasons += [f"specialty '{s}'" for s in specialties if s in risk_cfg.get("high_risk_specialties", [])]
    risk_level = fm.get("risk_level")
    if reasons and risk_level and risk_level != "high":
        add("risk_level", f"risk_level must be 'high' because of {', '.join(reasons)}.")

    if risk_level == "high" and status in APPROVED_PLUS:
        if is_blank(fm.get("medical_advisor")):
            add("medical_advisor", "High-risk content requires a Medical Advisor sign-off.")
        elif norm_name(fm["medical_advisor"]) in names_of(fm.get("authors")):
            add("medical_advisor", "The Medical Advisor must not be an author of the article.")
        if is_blank(fm.get("medical_advisor_signoff_date")):
            add("medical_advisor_signoff_date", "High-risk content requires the sign-off date.")

    # ---- review integrity --------------------------------------------------
    authors, reviewers = names_of(fm.get("authors")), names_of(fm.get("reviewers"))
    if authors and reviewers:
        if authors[0] in reviewers:
            add("reviewers", "A reviewer must not be the main author.")
        if status in APPROVED_PLUS and not (set(reviewers) - set(authors)):
            add("reviewers", "At least one reviewer must be independent of all authors.")

    # ---- sources -----------------------------------------------------------
    if status in APPROVED_PLUS and all(
        is_blank(fm.get(k)) for k in ("references", "pubmed_ids", "guidelines")
    ):
        add("references", "At least one source (references, pubmed_ids or guidelines) is required.")

    # ---- safety hold -------------------------------------------------------
    if fm.get("safety_hold") is True:
        if status in ("approved",):
            add("safety_hold", "An article under safety hold cannot be approved.")
        elif status == "published":
            add("safety_hold", "Published article is under safety hold — "
                               "it must be withdrawn from the wiki until released.", "WARN")

    # ---- sex / gender review -----------------------------------------------
    relevance = fm.get("sex_gender_relevance")
    if status in APPROVED_PLUS and relevance == "not_assessed" \
            and fm.get("content_kind") != "qr-media-reference":
        add("sex_gender_relevance", "The sex/gender cross-check must be completed before approval.")
    if relevance == "relevant" and is_blank(fm.get("sex_gender_notes")):
        add("sex_gender_notes", "sex_gender_relevance is 'relevant': summarise the aspects.")
    if "Gender-Medizin" in specialties and relevance == "none" and status in APPROVED_PLUS:
        add("sex_gender_relevance", "Gender-Medizin articles must be marked 'relevant'.")

    # ---- audience ----------------------------------------------------------
    audience = fm.get("target_audience") or []
    if article_type == "patient":
        if "patients" not in audience:
            add("target_audience", "Patient articles must include 'patients' in target_audience.")
        if fm.get("language_level") not in ("simple", "layperson"):
            add("language_level", "Patient articles must use language_level 'simple' or 'layperson'.")

    # ---- pharmaka ----------------------------------------------------------
    if article_type == "pharmaka":
        if status in APPROVED_PLUS:
            for key in ("active_substances", "atc_codes"):
                if is_blank(fm.get(key)):
                    add(key, f"'{key}' is required for pharmaka from approval on.")
        for code in fm.get("atc_codes") or []:
            if not ATC_RE.match(str(code)):
                add("atc_codes", f"'{code}' is not a valid 7-character ATC code.")

    for code in fm.get("icd10") or []:
        if not ICD10_RE.match(str(code)):
            add("icd10", f"'{code}' does not look like an ICD-10-GM code.")

    # ---- QR media records --------------------------------------------------
    if fm.get("content_kind") == "qr-media-reference":
        for key in ("media_type", "parent_slug", "qr_media_url"):
            if is_blank(fm.get(key)):
                add(key, f"'{key}' is required for content_kind 'qr-media-reference'.")
        if status in APPROVED_PLUS and fm.get("media_type") in ("audio", "video", "animation") \
                and fm.get("media_transcript") is not True:
            add("media_transcript", "Audio/video media need a transcript/captions (accessibility).")


def validate_patient_text(article: Article, fm: dict[str, Any], add) -> None:
    """Heuristic warnings for patient texts. They support, never replace, the human review."""
    prose = strip_markup(article.body)
    if not prose:
        return
    lowered = prose.lower()
    hits = sorted({p for p in INSTRUCTION_PHRASES if p in lowered})
    if hits:
        add("body", "Patient text contains individual-instruction phrasing "
                    f"({', '.join(repr(h) for h in hits)}). Patient content must be general "
                    "information, not an individual medical instruction.", "WARN")
    if DOSAGE_RE.search(prose):
        add("body", "Patient text contains a dosage. Reviewers must confirm it is general, "
                    "sourced information and not an individual recommendation.", "WARN")
    result = flesch_amstad(prose)
    if result and result[0] < READABILITY_WARN_BELOW:
        add("body", f"Readability (Flesch-Amstad) {result[0]:.0f} < {READABILITY_WARN_BELOW:.0f}: "
                    "text may be too complex for lay readers (heuristic).", "WARN")


def validate_template(article: Article, schema: dict[str, Any], add) -> list[Finding]:
    """Structure-only validation of blank templates."""
    fm = article.frontmatter or {}
    fields = schema["fields"]
    for name, spec in fields.items():
        if spec.get("required") and name not in fm:
            add(name, f"Template is missing required key '{name}'.")
    for key in sorted(set(fm) - set(fields)):
        add(key, f"Template contains unknown key '{key}'.")
    if fm.get("article_type") not in fields["article_type"]["values"]:
        add("article_type", f"Template article_type '{fm.get('article_type')}' is invalid.")
    if fm.get("status") != "draft":
        add("status", "Templates must start with status 'draft'.")
    return article.findings


# ---------------------------------------------------------------------------
# File scanning
# ---------------------------------------------------------------------------

def is_template(path: Path) -> bool:
    return "templates" in path.parts and "content" in path.parts


def collect_files(paths: list[Path]) -> list[Path]:
    """Collect all Markdown files from the provided paths (files or directories)."""
    md_files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix == ".md":
            md_files.append(path)
        elif path.is_dir():
            md_files.extend(sorted(path.rglob("*.md")))
        else:
            print(f"WARNING: Skipping non-Markdown or non-existent path: {path}", file=sys.stderr)
    return md_files


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate Wikimedica article frontmatter against the article schema."
    )
    parser.add_argument("paths", nargs="+", type=Path, help="Markdown files or directories.")
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH,
                        help=f"Path to article schema YAML (default: {SCHEMA_PATH})")
    parser.add_argument("--templates", action="store_true",
                        help="Validate content/templates/* in structure mode (otherwise skipped).")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors.")
    args = parser.parse_args(argv)

    schema = load_schema(args.schema)
    files = collect_files(args.paths)
    if not files:
        print("No Markdown files found.")
        return 0

    n_valid = n_skipped = n_files_err = n_err = n_warn = 0

    for file_path in files:
        template = is_template(file_path)
        if template and not args.templates:
            n_skipped += 1
            continue

        article = parse_article(file_path)
        if article.frontmatter is None:
            n_skipped += 1  # README/policy files without frontmatter are not articles
            continue

        validate_article(article, schema, template_mode=template)
        n_valid += 1
        for finding in article.findings:
            print(finding)
        errs, warns = len(article.errors), len(article.warnings)
        n_err, n_warn = n_err + errs, n_warn + warns
        if errs or (args.strict and warns):
            n_files_err += 1
        elif not warns:
            print(f"OK     {file_path}")

    print(
        "\n--- Validation Summary ---\n"
        f"Files validated:    {n_valid}\n"
        f"Files skipped:      {n_skipped}\n"
        f"Files with errors:  {n_files_err}\n"
        f"Total errors:       {n_err}\n"
        f"Total warnings:     {n_warn}\n"
    )
    return 1 if (n_err or (args.strict and n_warn)) else 0


if __name__ == "__main__":
    sys.exit(main())
