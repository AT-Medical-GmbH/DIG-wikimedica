"""data/legal/disclaimers.yaml: complete, consistent and gated."""

from __future__ import annotations

import yaml

from conftest import REPO

DATA = yaml.safe_load((REPO / "data" / "legal" / "disclaimers.yaml").read_text(encoding="utf-8"))
SCHEMA = yaml.safe_load((REPO / "data" / "metadata" / "article-schema.yaml").read_text(encoding="utf-8"))


def all_referenced_blocks():
    names = [b for blocks in DATA["profiles"].values() for b in blocks]
    for group in DATA["rules"].values():
        for blocks in group.values():
            names += blocks
    return set(names)


def test_review_gate_exists_and_is_consistent():
    assert DATA["review_status"] in ("pending-legal-review", "approved")
    if DATA["review_status"] == "approved":
        assert DATA["approved_by"] and DATA["approved_on"]


def test_every_article_type_has_a_profile():
    assert set(DATA["profiles"]) == set(SCHEMA["fields"]["article_type"]["values"])


def test_every_referenced_block_is_defined():
    assert all_referenced_blocks() <= set(DATA["blocks"])


def test_no_block_is_unused():
    assert set(DATA["blocks"]) <= all_referenced_blocks()


def test_rules_use_valid_keys():
    kinds = set(SCHEMA["fields"]["content_kind"]["values"])
    risks = set(SCHEMA["fields"]["risk_level"]["values"])
    assert set(DATA["rules"]["by_content_kind"]) <= kinds
    assert set(DATA["rules"]["by_risk_level"]) <= risks


def test_emergency_notice_names_the_numbers_and_leads_patient_facing_profiles():
    text = DATA["blocks"]["emergency"]["text"]
    assert "112" in text and "116 117" in text
    for kind in ("patient", "consent", "discharge"):
        assert DATA["profiles"][kind][0] == "emergency"


def test_every_profile_carries_a_general_disclaimer():
    assert all("general" in blocks for blocks in DATA["profiles"].values())


def test_high_risk_content_always_gets_the_dosing_notice():
    assert "dosing" in DATA["rules"]["by_risk_level"]["high"]
    assert all("dosing" in DATA["profiles"][t] for t in SCHEMA["risk"]["high_risk_article_types"])


def test_texts_are_non_empty_and_free_of_placeholders():
    for name, block in DATA["blocks"].items():
        assert block["title"].strip() and block["text"].strip(), name
        assert "{{" not in block["text"] and "<" not in block["text"], f"{name}: markup/placeholder in text"
