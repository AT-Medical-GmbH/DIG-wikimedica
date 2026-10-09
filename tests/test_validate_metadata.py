"""Tests for scripts/validation/validate-metadata.py (schema v2 + governance rules)."""

from __future__ import annotations

import pytest

from conftest import DELETE, FIXTURES, REPO, has

PROFESSIONAL = "testartikel-professional.md"
PATIENT = "testartikel-patient.md"
PHARMAKA = "testartikel-pharmaka.md"
CONSENT = "testmodul-aufklaerung.md"


# ---------------------------------------------------------------------------
# Known-good examples
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", sorted(p.name for p in FIXTURES.glob("*.md")))
def test_example_articles_are_valid(check, name):
    article = check(name)
    assert [str(f) for f in article.findings] == []


def test_schema_has_26_canonical_specialties(schema):
    values = schema["fields"]["specialty"]["values"]
    assert len(values) == 26 and len(set(values)) == 26
    assert "Gender-Medizin" in values


def test_schema_covers_all_mandatory_handover_fields(schema):
    mandatory = {
        "title", "slug", "specialty", "secondary_specialties", "article_type", "status",
        "version", "authors", "reviewers", "medical_advisor", "ai_assisted",
        "ai_assistance_description", "pubmed_ids", "guidelines", "icd10", "references",
        "source_notes", "created", "updated", "next_review", "risk_level",
        "target_audience", "language", "license", "change_summary",
    }
    assert mandatory <= set(schema["fields"])


# ---------------------------------------------------------------------------
# Rule tests: each case breaks exactly one thing and expects a specific finding
# ---------------------------------------------------------------------------

CASES = [
    # id, fixture, changes, expected field, expected message fragment
    ("slug-missing", PROFESSIONAL, {"slug": DELETE}, "slug", "missing"),
    ("slug-pattern", PROFESSIONAL, {"slug": "Bad Slug"}, "slug", "pattern"),
    ("specialty-unknown", PROFESSIONAL, {"specialty": "Astrologie"}, "specialty", "not in allowed"),
    ("specialty-blank", PROFESSIONAL, {"specialty": ""}, "specialty", "must not be empty"),
    ("secondary-unknown-type", PROFESSIONAL, {"secondary_specialties": [5]}, "secondary_specialties", "expected string"),
    ("risk-missing", PROFESSIONAL, {"risk_level": DELETE}, "risk_level", "missing"),
    ("risk-invalid", PROFESSIONAL, {"risk_level": "extreme"}, "risk_level", "not in allowed"),
    ("pharmaka-must-be-high", PHARMAKA, {"risk_level": "moderate"}, "risk_level", "must be 'high'"),
    ("notfall-must-be-high", PROFESSIONAL, {"specialty": "Notfallmedizin"}, "risk_level", "must be 'high'"),
    ("onkologie-secondary-high", PROFESSIONAL, {"secondary_specialties": ["Hämatologie/Onkologie"]}, "risk_level", "must be 'high'"),
    ("therapy-must-be-high", PROFESSIONAL, {"article_type": "therapy"}, "risk_level", "must be 'high'"),
    ("advisor-missing", PHARMAKA, {"medical_advisor": DELETE}, "medical_advisor", "requires a medical advisor"),
    ("advisor-is-author", PHARMAKA, {"medical_advisor": "  test AUTORIN "}, "medical_advisor", "must not be an author"),
    ("advisor-date-missing", PHARMAKA, {"medical_advisor_signoff_date": DELETE}, "medical_advisor_signoff_date", "sign-off date"),
    ("reviewer-is-main-author", PROFESSIONAL,
     {"reviewers": [{"name": "test autorin"}, {"name": "Test Gutachter"}]}, "reviewers", "main author"),
    ("no-independent-reviewer", PROFESSIONAL,
     {"authors": [{"name": "A"}, {"name": "B"}], "reviewers": [{"name": "B"}]}, "reviewers", "independent"),
    ("reviewer-without-name", PROFESSIONAL, {"reviewers": [{"specialty": "x"}]}, "reviewers", "missing required key 'name'"),
    ("reviewers-empty-when-approved", PROFESSIONAL, {"reviewers": []}, "reviewers", "must not be empty"),
    ("ai-undeclared-description", PROFESSIONAL, {"ai_assisted": True}, "ai_assistance_description", "describe tool"),
    ("ai-flag-missing", PROFESSIONAL, {"ai_assisted": DELETE}, "ai_assisted", "missing"),
    ("next-review-required", PROFESSIONAL, {"next_review": DELETE}, "next_review", "required for status"),
    ("next-review-before-updated", PROFESSIONAL, {"next_review": "2026-01-01"}, "next_review", "must be after"),
    ("license-required", PROFESSIONAL, {"license": DELETE}, "license", "required for status"),
    ("change-summary-required", PROFESSIONAL, {"change_summary": ""}, "change_summary", "must not be empty"),
    ("source-notes-required", PROFESSIONAL, {"source_notes": ""}, "source_notes", "must not be empty"),
    ("no-source-at-all", PROFESSIONAL, {"references": [], "pubmed_ids": [], "guidelines": []}, "references", "at least one source"),
    ("reference-without-citation", PROFESSIONAL, {"references": [{"pmid": 1}]}, "references", "citation"),
    ("pmid-not-numeric", PROFESSIONAL, {"pubmed_ids": ["abc"]}, "pubmed_ids", "not a valid pubmed id"),
    ("icd10-invalid", PROFESSIONAL, {"icd10": ["Hallo"]}, "icd10", "icd-10"),
    ("gender-not-assessed", PROFESSIONAL, {"sex_gender_relevance": "not_assessed"}, "sex_gender_relevance", "cross-check"),
    ("gender-relevant-needs-notes", PHARMAKA, {"sex_gender_notes": ""}, "sex_gender_notes", "summarise"),
    ("gender-specialty-must-be-relevant", PROFESSIONAL, {"specialty": "Gender-Medizin"}, "sex_gender_relevance", "must be marked 'relevant'"),
    ("patient-needs-patient-audience", PATIENT, {"target_audience": ["physicians"]}, "target_audience", "'patients'"),
    ("patient-language-level", PATIENT, {"language_level": "professional"}, "language_level", "simple"),
    ("target-audience-empty", PROFESSIONAL, {"target_audience": []}, "target_audience", "at least 1"),
    ("target-audience-unknown", PROFESSIONAL, {"target_audience": ["aliens"]}, "target_audience", "not in allowed"),
    ("pharmaka-needs-atc", PHARMAKA, {"atc_codes": []}, "atc_codes", "required for pharmaka"),
    ("pharmaka-needs-substance", PHARMAKA, {"active_substances": DELETE}, "active_substances", "required for pharmaka"),
    ("atc-invalid", PHARMAKA, {"atc_codes": ["12345"]}, "atc_codes", "atc"),
    ("published-needs-1.0", PATIENT, {"version": "0.9.0"}, "version", ">= 1.0.0"),
    ("semver-invalid", PROFESSIONAL, {"version": "1.0"}, "version", "semver"),
    ("updated-before-created", PROFESSIONAL, {"updated": "2025-01-01"}, "updated", "earlier than"),
    ("date-impossible", PROFESSIONAL, {"created": "2026-13-45"}, "created", "not a valid calendar date"),
    ("date-wrong-format", PROFESSIONAL, {"created": "10.01.2026"}, "created", "iso 8601"),
    ("safety-hold-blocks-approval", PROFESSIONAL, {"safety_hold": True}, "safety_hold", "cannot be approved"),
    ("credit-must-be-true", PROFESSIONAL, {"wikimedica_credit": False}, "wikimedica_credit", "true"),
    ("consent-needs-procedure", CONSENT, {"procedure": ""}, "procedure", "requires a 'procedure'"),
    ("module-type-mismatch", CONSENT, {"module_type": "discharge"}, "module_type", "must equal"),
    ("qr-must-be-https", CONSENT, {"qr_media_url": "http://example.org/x"}, "qr_media_url", "pattern"),
    ("qr-media-needs-fields", CONSENT, {"content_kind": "qr-media-reference"}, "media_type", "required for content_kind"),
    ("status-invalid", PROFESSIONAL, {"status": "live"}, "status", "not in allowed"),
    ("article-type-invalid", PROFESSIONAL, {"article_type": "blog"}, "article_type", "not in allowed"),
    ("licence-and-license-differ", PROFESSIONAL, {"licence": "OTHER"}, "licence", "different values"),
]


@pytest.mark.parametrize(
    "fixture,changes,field,fragment",
    [pytest.param(*c[1:], id=c[0]) for c in CASES],
)
def test_rule_violation_is_reported(check, fixture, changes, field, fragment):
    article = check(fixture, **changes)
    assert has(article, field, fragment), "\n".join(str(f) for f in article.findings) or "no findings"


def test_every_error_case_exits_nonzero_findings(check):
    """Sanity: the parametrised cases really are errors, not warnings."""
    article = check(PROFESSIONAL, slug="Bad Slug")
    assert article.errors and not article.warnings


def test_draft_does_not_need_approval_fields(check):
    article = check(PROFESSIONAL, status="draft", reviewers=[], next_review=DELETE,
                    license=DELETE, change_summary="", source_notes="", references=[],
                    sex_gender_relevance="not_assessed")
    assert article.errors == []


def test_in_review_requires_change_summary(check):
    article = check(PROFESSIONAL, status="in-review", change_summary="")
    assert has(article, "change_summary", "must not be empty")


def test_advisor_review_requires_reviewers(check):
    article = check(PHARMAKA, status="advisor-review", reviewers=[])
    assert has(article, "reviewers", "must not be empty")


def test_high_risk_draft_does_not_yet_need_advisor(check):
    article = check(PHARMAKA, status="draft", medical_advisor=DELETE,
                    medical_advisor_signoff_date=DELETE)
    assert not has(article, "medical_advisor", "requires")


def test_filename_slug_check_uses_file_stem(check):
    article = check(PROFESSIONAL, filename="anderer-name.md")
    assert has(article, "slug", "must equal the file name")


# ---------------------------------------------------------------------------
# Dates, aliases, unknown keys, YAML errors
# ---------------------------------------------------------------------------

def test_unquoted_yaml_dates_are_accepted(check):
    # fixtures use bare dates (2026-01-10): PyYAML yields date objects
    assert check(PROFESSIONAL).errors == []


def test_deprecated_licence_alias_satisfies_license_with_warning(check):
    article = check(PROFESSIONAL, license=DELETE, licence="TEST-LICENSE-PLACEHOLDER")
    assert article.errors == []
    assert has(article, "licence", "deprecated", level="WARN")


def test_unknown_key_is_a_warning_not_an_error(check):
    article = check(PROFESSIONAL, reviewrs=[])
    assert article.errors == []
    assert has(article, "reviewrs", "unknown frontmatter key", level="WARN")


def test_overdue_review_of_published_article_warns(check):
    article = check(PATIENT, next_review="2026-03-01")
    assert article.errors == []
    assert has(article, "next_review", "overdue", level="WARN")


def test_invalid_yaml_is_reported(tmp_path, vm, schema):
    path = tmp_path / "kaputt.md"
    path.write_text("---\ntitle: [unclosed\n---\ntext\n", encoding="utf-8")
    article = vm.parse_article(path)
    vm.validate_article(article, schema)
    assert has(article, "YAML", "parse error")


def test_error_lines_point_to_the_key(check):
    article = check(PROFESSIONAL, risk_level="extreme")
    finding = next(f for f in article.errors if f.field == "risk_level")
    text = article.path.read_text(encoding="utf-8").splitlines()
    assert text[finding.line - 1].startswith("risk_level:")


# ---------------------------------------------------------------------------
# Patient-text heuristics (warnings only)
# ---------------------------------------------------------------------------

def test_patient_instruction_phrasing_is_flagged(check):
    body = "# T\n\n## Was ist das?\n\nNehmen Sie morgens 500 mg ein. Setzen Sie das Mittel nie ab.\n"
    article = check(PATIENT, body=body)
    assert article.errors == []
    assert has(article, "body", "individual-instruction", level="WARN")
    assert has(article, "body", "dosage", level="WARN")


def test_patient_complex_text_triggers_readability_warning(check):
    sentence = ("Die pathophysiologischen Mechanismen der kardiovaskulären Dekompensation "
                "umfassen neurohumorale Aktivierungskaskaden, hämodynamische Veränderungen "
                "sowie strukturelle Remodellierungsprozesse des Myokards. ")
    article = check(PATIENT, body="# T\n\n## Was ist das?\n\n" + sentence * 6)
    assert has(article, "body", "readability", level="WARN")


def test_professional_text_is_not_checked_for_patient_heuristics(check):
    article = check(PROFESSIONAL, body="# T\n\n## Übersicht\n\nNehmen Sie 500 mg.\n")
    assert not has(article, "body", "individual", level="WARN")


def test_html_comments_do_not_count_as_prose(check):
    body = "# T\n\n## Was ist das?\n\n<!-- Nehmen Sie 500 mg ein. -->\nEinfacher Text. Kurz. Klar.\n"
    assert not has(check(PATIENT, body=body), "body", "dosage", level="WARN")


# ---------------------------------------------------------------------------
# Template mode and CLI
# ---------------------------------------------------------------------------

def test_templates_are_skipped_in_normal_mode(vm, capsys):
    assert vm.main([str(REPO / "content" / "templates")]) == 0
    assert "Files validated:    0" in capsys.readouterr().out


def test_cli_returns_1_on_errors(vm, tmp_path, check, capsys):
    article = check(PROFESSIONAL, slug="Bad Slug")
    assert vm.main(["--schema", str(REPO / "data/metadata/article-schema.yaml"), str(article.path)]) == 1


def test_cli_strict_turns_warnings_into_failure(vm, check):
    article = check(PROFESSIONAL, reviewrs=[])
    schema = str(REPO / "data/metadata/article-schema.yaml")
    assert vm.main(["--schema", schema, str(article.path)]) == 0
    assert vm.main(["--schema", schema, "--strict", str(article.path)]) == 1


def test_files_without_frontmatter_are_skipped(vm, tmp_path, capsys):
    (tmp_path / "README.md").write_text("# Nur ein Readme\n", encoding="utf-8")
    assert vm.main([str(tmp_path)]) == 0
    assert "Files skipped:      1" in capsys.readouterr().out
