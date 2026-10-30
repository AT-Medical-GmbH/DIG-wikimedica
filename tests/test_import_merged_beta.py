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


def test_page_extras_categories_from_metadata():
    fm = {"title": "Testkrankheit", "specialty": "Innere Medizin", "article_type": "professional",
          "content_kind": "article", "risk_level": "moderate", "icd10": []}
    see, cats = imp.page_extras("testkrankheit", fm, "## Klinik\n\nText.\n")
    assert "[[Kategorie:Innere Medizin]]" in cats
    assert "[[Kategorie:Artikeltyp: Fachartikel]]" in cats
    assert see == ""


def test_related_articles_need_three_and_respect_codes(monkeypatch):
    index = {
        "a": {"title": "A", "specialty": "Kardiologie", "type": "professional", "icd": ["I10"], "atc": []},
        "b": {"title": "B", "specialty": "Kardiologie", "type": "professional", "icd": ["I11"], "atc": []},
        "c": {"title": "C", "specialty": "Neurologie", "type": "professional", "icd": ["I15"], "atc": []},
        "d": {"title": "D", "specialty": "Kardiologie", "type": "professional", "icd": ["K35"], "atc": []},
        "e": {"title": "E", "specialty": "Kardiologie", "type": "professional", "icd": ["I50"], "atc": []},
    }
    monkeypatch.setattr(imp, "_ARTICLE_INDEX", index)
    fm = {"title": "X", "specialty": "Kardiologie", "icd10": ["I12.0"]}
    assert imp.related_articles("x", fm) == ["B", "A", "C"]  # nach Abstand, gleiches Fachgebiet zuerst
    assert imp.related_articles("x", {"title": "Y", "specialty": "Kardiologie", "icd10": ["K80"]}) == []
    drugs = {
        "m1": {"title": "Metoprolol", "specialty": "Pharmakologie", "type": "pharmaka", "icd": [], "atc": ["C07AB02"]},
        "m2": {"title": "Bisoprolol", "specialty": "Pharmakologie", "type": "pharmaka", "icd": [], "atc": ["C07AB07"]},
        "m3": {"title": "Propranolol", "specialty": "Pharmakologie", "type": "pharmaka", "icd": [], "atc": ["C07AA05"]},
        "m4": {"title": "Ramipril", "specialty": "Pharmakologie", "type": "pharmaka", "icd": [], "atc": ["C09AA05"]},
    }
    monkeypatch.setattr(imp, "_ARTICLE_INDEX", drugs)
    rel = imp.related_articles("atenolol", {"title": "Atenolol", "atc_codes": ["C07AB03"]})
    assert rel == ["Bisoprolol", "Metoprolol", "Propranolol"]
