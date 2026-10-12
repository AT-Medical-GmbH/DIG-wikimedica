"""Public BETA rendering must retain safety while hiding internal draft status."""

from __future__ import annotations

from conftest import load_script


imp = load_script("scripts/publishing/import_merged_beta.py", "import_merged_beta")


def test_public_beta_header_has_no_ai_or_review_status_claim():
    header = imp.BETA_HEADER.lower()
    assert "beta" in header
    assert "individuelle diagnostik" in header
    assert "112" in header
    assert "ki-gest" not in header
    assert "review" not in header
    assert "freigabe" not in header


def test_public_beta_body_removes_internal_draft_notice_and_review_tasks():
    body = (
        "> **Redaktioneller Status: Entwurf – keine medizinische Fachfreigabe.**\n\n"
        "## Klinik\n\nText mit Quelle.[1]\n\n"
        "## Redaktionelle Prüfaufträge vor fachlicher Freigabe\n\nInterne Aufgabe\n"
    )
    public = imp.public_beta_body(body)
    assert "Redaktioneller Status" not in public
    assert "medizinische Fachfreigabe" not in public
    assert "Redaktionelle Prüfaufträge" not in public
    assert "Text mit Quelle.[1]" in public
