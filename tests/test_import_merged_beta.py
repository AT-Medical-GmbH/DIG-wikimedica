"""Public BETA rendering must retain safety while hiding internal draft status."""

from __future__ import annotations

import re

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


def test_page_extras_merges_specialty_aliases():
    fm = {"title": "Amiodaron", "specialty": "Pharmakologie", "secondary_specialties": ["Kardiologie", "Endokrinologie"],
          "article_type": "pharmaka", "content_kind": "article", "risk_level": "high"}
    _, cats = imp.page_extras("amiodaron", fm, "Text.")
    assert "[[Kategorie:Endokrinologie/Diabetologie]]" in cats
    assert "[[Kategorie:Endokrinologie]]" not in cats


def test_page_extras_links_patient_information(monkeypatch):
    index = {
        "arterielle-hypertonie-patienteninformation": {"title": "Bluthochdruck – Patienteninformation", "specialty": "Kardiologie",
                                                        "type": "patient", "icd": ["I10"], "atc": [], "related": "arterielle-hypertonie"},
    }
    monkeypatch.setattr(imp, "_ARTICLE_INDEX", index)
    fm = {"title": "Arterielle Hypertonie", "specialty": "Kardiologie", "article_type": "professional", "content_kind": "article",
          "risk_level": "moderate", "icd10": ["I10"]}
    see, _ = imp.page_extras("arterielle-hypertonie", fm, "Text.")
    assert "== Für Patientinnen und Patienten ==" in see
    assert "[[Bluthochdruck – Patienteninformation]]" in see


# --- Automatische Querverweise und Rückverweise (Auftrag Andreas 10.11.2026, #712) ---------------------------------

def _fake_index(n=9):
    return {f"wirkstoff-{i}": {"title": f"Wirkstoff{i}x", "specialty": "Kardiologie", "type": "pharmaka", "icd": [],
                               "atc": [f"C03CA0{i}"], "related": ""} for i in range(n)}


def test_rueckverweise_ergaenzen_das_siehe_auch(monkeypatch):
    index = _fake_index()
    monkeypatch.setattr(imp, "article_index", lambda: index)
    monkeypatch.setattr(imp, "_REVERSE_RELATED", None)
    monkeypatch.setattr(imp, "eingriffe_verwandt", lambda: {})
    fm = {"title": "Wirkstoff8x", "atc_codes": ["C03CA08"], "specialty": "Kardiologie"}
    forward = imp._related_forward("wirkstoff-8", fm)
    both = imp.related_articles("wirkstoff-8", fm)
    assert set(forward) <= set(both) and len(both) <= len(forward) + imp.REVERSE_LIMIT
    assert "Wirkstoff8x" not in both  # nie sich selbst


def test_rueckverweis_nur_wenn_der_andere_artikel_den_titel_nennt(monkeypatch):
    index = _fake_index()
    monkeypatch.setattr(imp, "article_index", lambda: index)
    monkeypatch.setattr(imp, "_REVERSE_RELATED", None)
    monkeypatch.setattr(imp, "eingriffe_verwandt", lambda: {})
    rev = imp.reverse_related()
    for target, sources in rev.items():
        for source in sources:
            info = next(i for i in index.values() if i["title"] == source)
            fm = {"title": source, "atc_codes": info["atc"], "specialty": info["specialty"]}
            assert target in imp._related_forward(next(s for s, i in index.items() if i["title"] == source), fm)


def test_build_page_verlinkt_und_notbremse(monkeypatch):
    import autolink
    word = path = None
    for p in sorted((imp.ROOT / "content" / "pharmaka").glob("*.md"))[:400]:
        text = p.read_text(encoding="utf-8")
        w = next((w for w in ("Niere", "Leber", "Herz", "Schmerz") if re.search(rf"(?m)^[^#>|\n].*\b{w}\b", text)), None)
        if w:
            word, path = w, p
            break
    assert path is not None, "kein geeigneter Artikel für den Test im Quellbestand"
    monkeypatch.setattr(imp, "_LINKER", autolink.Linker({word: "Zielseite"}))
    monkeypatch.setenv("WIKIMEDICA_AUTOLINK", "1")
    _, on, _ = imp.build_page(path, "0" * 40)
    monkeypatch.setenv("WIKIMEDICA_AUTOLINK", "0")
    _, off, _ = imp.build_page(path, "0" * 40)
    assert "Zielseite" in on and "[[Zielseite" not in off
