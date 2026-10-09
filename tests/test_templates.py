"""Tests for content/templates/*.md — templates must be complete, consistent and fillable."""

from __future__ import annotations

import re

import pytest
import yaml

from conftest import REPO, load_script, render

TEMPLATES = sorted(p for p in (REPO / "content" / "templates").glob("*.md") if p.name != "README.md")
HEADING_RE = re.compile(r"^#{1,6}[ \t]+(.+?)[ \t]*$", re.MULTILINE)
PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-z_]+)\s*\}\}")

# Placeholders the importer substitutes from frontmatter (content/templates/README.md).
# {{ x }} is a TRANSCLUSION in wikitext, so unknown placeholders must never exist.
ALLOWED_PLACEHOLDERS = {
    "title", "specialty", "status", "version", "updated", "license", "procedure",
    "parent_slug", "qr_media_url", "clinic_name", "clinic_address", "clinic_phone",
}

EXPECTED_TEMPLATES = {
    "article-professional.md", "article-patient.md", "consent-module.md",
    "discharge-module.md", "article-pharmaka.md", "article-therapy.md",
    "guideline-summary.md", "qr-media-reference.md",
}

pre_publish = load_script("scripts/publishing/pre-publish-check.py", "pre_publish_check")


def split(path):
    text = path.read_text(encoding="utf-8")
    end = text.index("\n---\n", 4)
    return yaml.safe_load(text[4:end]), text[end + 5:], text


def headings(body):
    return [h.lower() for h in HEADING_RE.findall(body)]


def test_all_eight_handover_templates_exist():
    assert {p.name for p in TEMPLATES} == EXPECTED_TEMPLATES


@pytest.mark.parametrize("path", TEMPLATES, ids=lambda p: p.name)
class TestEveryTemplate:
    def test_structure_is_valid(self, path, vm, schema):
        article = vm.parse_article(path)
        vm.validate_article(article, schema, template_mode=True)
        assert [str(f) for f in article.findings] == []

    def test_carries_handover_metadata(self, path):
        fm, _, _ = split(path)
        for key in ("risk_level", "target_audience", "next_review", "change_summary",
                    "ai_assisted", "ai_assistance_description", "references",
                    "source_notes", "sex_gender_relevance", "license", "reviewers"):
            assert key in fm, f"{path.name} lacks '{key}'"

    def test_has_sources_review_history_changelog_and_disclaimer(self, path):
        _, body, _ = split(path)
        h = headings(body)
        assert any(x in " ".join(h) for x in ("literatur", "quellen")), "no source section"
        assert any("review-historie" in x for x in h)
        assert any("änderungsverlauf" in x for x in h)
        assert any("haftungsausschluss" in x for x in h)

    def test_status_starts_as_draft_and_version_is_semver(self, path):
        fm, _, _ = split(path)
        assert fm["status"] == "draft"
        assert re.fullmatch(r"\d+\.\d+\.\d+", fm["version"])

    def test_does_not_hardcode_a_license(self, path):
        """The licence model is an open owner decision (DEC-2)."""
        fm, _, text = split(path)
        assert fm["license"] == ""
        assert "CC BY-SA" not in text and "licence:" not in text

    def test_only_known_placeholders(self, path):
        _, body, _ = split(path)
        unknown = set(PLACEHOLDER_RE.findall(body)) - ALLOWED_PLACEHOLDERS
        assert not unknown, f"unknown placeholders (wikitext transclusion risk): {unknown}"

    def test_risk_level_policy(self, path, schema):
        fm, _, _ = split(path)
        high_types = schema["risk"]["high_risk_article_types"]
        if fm["article_type"] in high_types:
            assert fm["risk_level"] == "high"

    def test_contains_required_sections_of_pre_publish_check(self, path):
        fm, body, _ = split(path)
        kind, a_type = fm["content_kind"], fm["article_type"]
        required = (pre_publish.REQUIRED_SECTIONS_BY_KIND.get(kind)
                    or pre_publish.REQUIRED_SECTIONS.get(a_type, []))
        have = headings(body)
        missing = [s for s in required if not any(s in h for h in have)]
        assert not missing, f"missing headings required by pre-publish-check: {missing}"


# ---------------------------------------------------------------------------
# A filled-in template must become a valid article
# ---------------------------------------------------------------------------

FILL_IN = {
    "common": {
        "title": "Ausgefüllt", "specialty": "Innere Medizin", "created": "2026-01-01",
        "updated": "2026-01-01",
        "authors": [{"name": "Test Autorin"}],
    },
    "article-professional.md": {"risk_level": "low"},
    "article-patient.md": {"risk_level": "low"},
    "consent-module.md": {"risk_level": "moderate", "procedure": "Testeingriff"},
    "discharge-module.md": {"risk_level": "moderate", "procedure": "Testeingriff"},
    "article-pharmaka.md": {},
    "article-therapy.md": {},
    "guideline-summary.md": {"risk_level": "low", "guidelines": [{"title": "Test-Leitlinie"}]},
    "qr-media-reference.md": {"risk_level": "low", "media_type": "video",
                              "parent_slug": "anderer-artikel",
                              "qr_media_url": "https://example.org/"},
}


@pytest.mark.parametrize("path", TEMPLATES, ids=lambda p: p.name)
def test_filled_template_passes_validation(path, vm, schema, tmp_path):
    fm, body, _ = split(path)
    fm.update(FILL_IN["common"])
    fm.update(FILL_IN[path.name])
    fm["slug"] = path.stem
    target = tmp_path / f"{path.stem}.md"
    target.write_text(render(fm, body), encoding="utf-8")

    article = vm.parse_article(target)
    vm.validate_article(article, schema)
    assert [str(f) for f in article.errors] == []


def test_unfilled_template_is_rejected_as_article(vm, schema, tmp_path):
    """An untouched template must not slip through as a real article."""
    fm, body, _ = split(REPO / "content/templates/article-professional.md")
    target = tmp_path / "x.md"
    target.write_text(render(fm, body), encoding="utf-8")
    article = vm.parse_article(target)
    vm.validate_article(article, schema)
    assert article.errors
