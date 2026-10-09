"""scripts/publishing/render_system_pages.py"""

from __future__ import annotations

import yaml

from conftest import REPO, load_script

rsp = load_script("scripts/publishing/render_system_pages.py", "render_system_pages")

SCHEMA = yaml.safe_load((REPO / "data/metadata/article-schema.yaml").read_text("utf-8"))
DISCLAIMERS = yaml.safe_load((REPO / "data/legal/disclaimers.yaml").read_text("utf-8"))


def pages():
    return rsp.build_pages("staging", SCHEMA, DISCLAIMERS)


def test_every_specialty_and_every_category_used_by_articles_has_a_page():
    p = pages()
    for s in SCHEMA["fields"]["specialty"]["values"]:
        assert f"Category:{s}" in p, s
    import wikipage
    for a_type in wikipage.TYPE_LABEL.values():
        assert f"Category:Artikeltyp: {a_type}" in p
    for kind in wikipage.KIND_LABEL.values():
        assert f"Category:Artikeltyp: {kind}" in p
    for cat in ("Risikoklasse: hoch", "Gender-Medizin", "Gesperrt (Sicherheitsprüfung)", "Zurückgezogen", "Archiviert"):
        assert f"Category:{cat}" in p


def test_footer_messages_point_to_existing_pages():
    p = pages()
    for message, target in [("Aboutpage", "Wikimedica:Impressum"), ("Privacypage", "Wikimedica:Datenschutz"),
                            ("Disclaimerpage", "Wikimedica:Haftungsausschluss")]:
        assert p[f"MediaWiki:{message}"] == target and target in p


def test_disclaimer_page_contains_every_block_from_the_source():
    text = pages()["Wikimedica:Haftungsausschluss"]
    for block in DISCLAIMERS["blocks"].values():
        assert block["title"] in text and block["text"].split(".")[0] in text


def test_css_styles_all_classes_the_page_builder_emits():
    css = pages()["MediaWiki:Common.css"]
    for cls in ("wm-notice", "wm-emergency", "wm-withdrawn", "wm-infobox", "wm-versionbox"):
        assert cls in css


def test_legal_drafts_still_contain_placeholders():
    assert set(rsp.placeholders_left(pages())) == {"Wikimedica:Impressum", "Wikimedica:Datenschutz"}


def test_production_is_refused_while_disclaimers_are_unapproved(tmp_path, capsys):
    assert rsp.main(["--env", "production", "--out", str(tmp_path)]) == 2
    assert "not approved" in capsys.readouterr().err and not list(tmp_path.iterdir())


def test_production_is_refused_while_placeholders_remain(tmp_path, capsys):
    approved = tmp_path / "d.yaml"
    approved.write_text(yaml.safe_dump({**DISCLAIMERS, "review_status": "approved"}, allow_unicode=True))
    assert rsp.main(["--env", "production", "--out", str(tmp_path / "o"), "--disclaimers", str(approved)]) == 2
    assert "placeholders" in capsys.readouterr().err


def test_staging_renders_and_writes_an_index(tmp_path):
    assert rsp.main(["--env", "staging", "--out", str(tmp_path)]) == 0
    rows = [l.split("\t") for l in (tmp_path / "pages.tsv").read_text("utf-8").splitlines()]
    assert len(rows) >= 40 and all((tmp_path / f).exists() for _, f in rows)


def test_no_unsafe_markup_in_generated_pages():
    for title, text in pages().items():
        if title.startswith("MediaWiki:Common.css"):
            continue
        assert "{{" not in text and "<script" not in text, title
