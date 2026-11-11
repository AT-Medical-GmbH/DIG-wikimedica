"""Begriffsartikel-Werkzeuge: Prüfstatus setzen und Rückzug im Probelauf (#728)."""

from __future__ import annotations

from conftest import load_script

cr = load_script("scripts/editorial/concept_review.py", "concept_review")

MD = '---\ntitle: "Kreatinin"\nslug: "kreatinin"\nconcept_kind: "diagnostik"\nreview_status: "ungeprueft"\n---\n\nText.\n'


def test_review_status_setzen_und_zuruecknehmen(tmp_path):
    f = tmp_path / "content" / "articles" / "begriffe" / "kreatinin.md"
    f.parent.mkdir(parents=True)
    f.write_text(MD, encoding="utf-8")
    assert cr.set_status(f, "geprueft") is True
    assert 'review_status: "geprueft"' in f.read_text(encoding="utf-8")
    assert cr.set_status(f, "geprueft") is False  # unverändert
    assert cr.set_status(f, "ungeprueft") is True
    assert f.read_text(encoding="utf-8").endswith("---\n\nText.\n")


def test_nur_begriffsartikel_werden_gefunden(tmp_path):
    (tmp_path / "content" / "articles").mkdir(parents=True)
    (tmp_path / "content" / "articles" / "a.md").write_text(MD, encoding="utf-8")
    (tmp_path / "content" / "articles" / "b.md").write_text('---\ntitle: "B"\nslug: "b"\n---\n\nText.\n', encoding="utf-8")
    assert [f.stem for f, _ in cr.concept_files(tmp_path)] == ["a"]
