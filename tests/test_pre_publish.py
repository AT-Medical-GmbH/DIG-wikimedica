"""pre-publish-check.py: the checks the importer reuses."""

from __future__ import annotations

import pytest

from conftest import REPO, load_script

pp = load_script("scripts/publishing/pre-publish-check.py", "pre_publish_check_t")


@pytest.mark.parametrize("body,ok", [
    ("## Übersicht\n\nText.\n", True),
    ("## Übersicht\n\nText <!-- Leitfaden --> mehr.\n", False),
    ("<!--\nmehrzeilig\n-->\n## A\n", False),
    ("Das ist TODO: ergänzen\n", False),
    ("FIXME später\n", False),
    ("```\n<!-- im Codeblock ok -->\nTODO im Codeblock\n```\n", True),
    ("Wort XXXL ist kein Marker\n", True),
])
def test_leftover_comments_and_todos(body, ok):
    assert pp.check_no_todo_markers(body).passed is ok


def test_required_sections_are_matched_on_headings_only():
    fm = {"article_type": "professional", "content_kind": "article"}
    body_text_only = "Übersicht Epidemiologie Diagnostik Therapie Literatur stehen nur im Fließtext.\n"
    assert not pp.check_required_sections(fm, body_text_only).passed
    body = "## Übersicht\n## Epidemiologie\n## Diagnostik\n## Therapie\n## Literatur\n"
    assert pp.check_required_sections(fm, body).passed


def test_guideline_summary_uses_its_own_sections():
    fm = {"article_type": "professional", "content_kind": "guideline-summary"}
    assert pp.check_required_sections(fm, "## Übersicht\n## Kernempfehlungen\n## Literatur\n").passed
    assert not pp.check_required_sections(fm, "## Übersicht\n## Epidemiologie\n").passed
