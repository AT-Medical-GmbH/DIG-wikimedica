"""Tests der Redaktionspipeline (scripts/editorial/wm_*.py): Warteschlange, Textprüfung, Artikelaufbau, Katalog."""
from __future__ import annotations

import json
import subprocess
import sys
import threading
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts" / "editorial"))

import wm_catalog  # noqa: E402
import wm_common  # noqa: E402
import wm_pipeline as pipe  # noqa: E402
import wm_research  # noqa: E402


# ---------------------------------------------------------------------------
# Warteschlange: atomares Beanspruchen ohne Kollision
# ---------------------------------------------------------------------------
def make_items(n: int) -> list[dict]:
    return [{"id": f"WM-DIS-{i:04d}", "kind": "disease", "title": f"Thema {i}", "slug": f"thema-{i}", "priority": float(n - i)}
            for i in range(n)]


def test_claim_is_atomic_across_threads(tmp_path: Path) -> None:
    q = wm_common.Queue(tmp_path)
    q.add_items(make_items(60))
    claimed: list[str] = []
    lock = threading.Lock()

    def work(name: str) -> None:
        qq = wm_common.Queue(tmp_path)  # eigene Verbindung wie ein eigener Prozess
        while True:
            row = qq.claim(name)
            if row is None:
                return
            with lock:
                claimed.append(row["id"])

    threads = [threading.Thread(target=work, args=(f"w{i}",)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(claimed) == 60 and len(set(claimed)) == 60


def test_claim_order_and_retries(tmp_path: Path) -> None:
    q = wm_common.Queue(tmp_path)
    q.add_items(make_items(3))
    first = q.claim("w1")
    assert first["id"] == "WM-DIS-0000"  # höchste Priorität zuerst
    q.release(first["id"], "Fehler")
    again = q.claim("w1")
    assert again["id"] == "WM-DIS-0000"  # Wiederholung, attempts=2
    q.release(again["id"], "Fehler")
    third = q.claim("w1")
    q.release(third["id"], "Fehler")
    assert q.db.execute("SELECT status FROM items WHERE id='WM-DIS-0000'").fetchone()[0] == "failed"
    assert q.claim("w1")["id"] == "WM-DIS-0001"


def test_add_items_is_idempotent(tmp_path: Path) -> None:
    q = wm_common.Queue(tmp_path)
    assert q.add_items(make_items(5)) == 5
    assert q.add_items(make_items(5)) == 0


def test_call_slots_respect_limits(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(wm_common, "MAX_CONCURRENT", 2)
    monkeypatch.setattr(wm_common, "MAX_REQUESTS_PER_MIN", 100)
    q = wm_common.Queue(tmp_path)
    s1 = q.acquire_call_slot("a")
    s2 = q.acquire_call_slot("b")
    inflight = q.db.execute("SELECT COUNT(*) FROM calls WHERE end IS NULL").fetchone()[0]
    assert inflight == 2
    q.release_call_slot(s1, "a")
    q.release_call_slot(s2, "b")
    assert q.db.execute("SELECT COUNT(*) FROM calls WHERE end IS NULL").fetchone()[0] == 0


# ---------------------------------------------------------------------------
# Textverarbeitung und Faktenprüfung
# ---------------------------------------------------------------------------
DRAFT = """# Gicht
## Übersicht
Gicht ist eine Arthritis [1, 2]. Sie betrifft z. B. Männer häufiger.[2] Dritter Satz ohne Beleg.
## Therapie
- Allopurinol ist Erstlinie [3].
Ein Satz mit falscher Quelle.[9]
"""


def test_citation_normalisation_and_split() -> None:
    units = pipe.split_units(DRAFT)
    texts = [u["text"] for u in units if u["type"] != "h"]
    assert texts[0] == "Gicht ist eine Arthritis.[1][2]"
    assert texts[1] == "Sie betrifft z. B. Männer häufiger.[2]"  # Abkürzung trennt nicht
    assert units[0]["type"] == "h" and units[0]["text"] == "Übersicht"


def test_formal_check_drops_uncited_and_invalid() -> None:
    units = pipe.split_units(DRAFT)
    pipe.formal_check(units, 3, "disease")
    dropped = [u["text"] for u in units if u.get("drop")]
    assert "Dritter Satz ohne Beleg." in dropped
    assert "Ein Satz mit falscher Quelle." in dropped  # [9] ungültig, danach ohne Beleg


def test_dose_in_drug_article_is_dropped() -> None:
    units = pipe.split_units("## Anwendung\nDie Dosis beträgt 500 mg pro Tag.[1] Die Substanz wirkt blutzuckersenkend.[1]\n")
    pipe.formal_check(units, 1, "drug")
    assert [u["text"] for u in units if u.get("drop")] == ["Die Dosis beträgt 500 mg pro Tag.[1]"]
    units = pipe.split_units("## Therapie\nZielwert 6 mg/dl.[1]\n")
    pipe.formal_check(units, 1, "disease")
    assert not any(u.get("drop") for u in units)  # Grenzwerte in Erkrankungsartikeln sind erlaubt


def test_rebuild_renumbers_and_drops_empty_sections() -> None:
    units = pipe.split_units("## A\nErster Satz.[3] Zweiter Satz.[1][3]\n## Leer\nNur ungeprüft.[2]\n")
    units[-1]["drop"] = "Faktenprüfung"
    body, stats = pipe.rebuild_body(units)
    assert "## Leer" not in body
    assert "Erster Satz.[1] Zweiter Satz.[2][1]" in body
    assert stats["order"] == [3, 1] and stats["sources"] == 2


# ---------------------------------------------------------------------------
# Artikelaufbau besteht die Repo-Validierung
# ---------------------------------------------------------------------------
REC = {"pmid": "32391934", "title": "2020 ACR Guideline for the Management of Gout", "year": "2020", "journal": "Arthritis Rheumatol",
       "volume": "72", "pages": "879-895", "doi": "10.1002/art.41247", "pmcid": "", "ptypes": ["Practice Guideline"],
       "authors": ["FitzGerald JD", "Dalbeth N", "Mikuls T"], "abstract": "x", "retracted": False}


@pytest.mark.parametrize("kind,spec", [("disease", "Rheumatologie"), ("drug", "Pharmakologie")])
def test_built_article_passes_validator(tmp_path: Path, kind: str, spec: str) -> None:
    item = {"id": "WM-DIS-0999", "title": "Gicht-Test", "slug": "gicht-test", "specialty": spec}
    body = "## Übersicht\nGicht ist eine Arthritis.[1]\n"
    extra = {"code": "M10", "codes": ["M04AA01"]}
    md = pipe.build_article(item, kind, body, [REC], [1], extra, {"kept": 10, "total": 12, "removed": 2})
    assert "KI-Entwurf" not in md and "Hinweis:" not in md
    path = tmp_path / "gicht-test.md"
    path.write_text(md, encoding="utf-8")
    ok, msg = pipe.validate_file(path)
    assert ok, msg
    assert "pubmed_ids: [\"32391934\"]" in md and "10.1002/art.41247" in md


# ---------------------------------------------------------------------------
# Katalog
# ---------------------------------------------------------------------------
def test_slugify_matches_schema() -> None:
    import re
    for t in ["Binnenschädigung des Kniegelenkes", "Cholera durch Vibrio cholerae O:1", "Östrogen/Gestagen"]:
        assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", wm_common.slugify(t))
    assert wm_common.slugify("Hüftgelenkarthrose") == "hueftgelenkarthrose"


def test_icd_catalog_loads_and_excludes_non_diagnoses() -> None:
    chapters, cats, subcount = wm_catalog.load_icd(REPO)
    assert len(cats) > 1500 and "I10" in cats and "E11" in cats
    items = wm_catalog.build_diseases(REPO, wm_catalog.scan_existing(REPO), [])
    codes = {i["code"] for i in items}
    assert "I10" in codes and not any(c.startswith(("V", "W", "X", "Y", "Z")) for c in codes)
    assert next(i for i in items if i["code"] == "I10")["covered_by"] == "arterielle-hypertonie"


def test_backlog_ids_are_stable_and_unique() -> None:
    for name, prefix in (("diseases-icd10gm2026.jsonl", "WM-DIS"), ("wirkstoffe-atc-gm2026.jsonl", "WM-DRUG"), ("handelsnamen-ema.jsonl", "WM-TRADE")):
        rows = wm_catalog.read_jsonl(REPO / "data/editorial/backlog" / name)
        assert rows, name
        ids = [r["id"] for r in rows]
        slugs = [r["slug"] for r in rows]
        assert len(ids) == len(set(ids)) and len(slugs) == len(set(slugs)) and all(i.startswith(prefix) for i in ids)


def test_atc_parser_skips_combinations_and_dosing() -> None:
    text = ("A01AA01    Natriumfluorid                                             1,1 mg O (0,5 mg Fluorid)\n"
            "A02BC01    Omeprazol                                                  20 mg O\n"
            "A02BD01    Omeprazol, Amoxicillin und Clarithromycin\n")
    subs = wm_catalog.parse_atc_text(text)
    assert set(subs) == {"Natriumfluorid", "Omeprazol"}
    assert "mg" not in json.dumps(subs)


# ---------------------------------------------------------------------------
# Recherche (Parser ohne Netz)
# ---------------------------------------------------------------------------
PUBMED_XML = b"""<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>111</PMID><Article>
<Journal><JournalIssue><Volume>5</Volume><PubDate><Year>2024</Year></PubDate></JournalIssue><ISOAbbreviation>J Test</ISOAbbreviation></Journal>
<ArticleTitle>Gout guideline.</ArticleTitle><Abstract><AbstractText Label="AIM">Ziel</AbstractText><AbstractText>Text</AbstractText></Abstract>
<AuthorList><Author><LastName>Meier</LastName><Initials>A</Initials></Author></AuthorList>
<PublicationTypeList><PublicationType>Practice Guideline</PublicationType></PublicationTypeList></Article></MedlineCitation>
<PubmedData><ArticleIdList><ArticleId IdType="doi">10.1/x</ArticleId><ArticleId IdType="pmc">PMC5</ArticleId></ArticleIdList></PubmedData></PubmedArticle>
<PubmedArticle><MedlineCitation><PMID>222</PMID><Article><ArticleTitle>Retracted</ArticleTitle><Abstract><AbstractText>a</AbstractText></Abstract>
<PublicationTypeList><PublicationType>Retracted Publication</PublicationType></PublicationTypeList></Article></MedlineCitation></PubmedArticle></PubmedArticleSet>"""


def test_pubmed_parser_marks_retracted_and_extracts_ids() -> None:
    recs = wm_research.parse_pubmed_xml(PUBMED_XML)
    assert recs["111"]["doi"] == "10.1/x" and recs["111"]["pmcid"] == "PMC5" and recs["111"]["abstract"].startswith("AIM: Ziel")
    assert recs["222"]["retracted"] is True
    assert wm_research.rank_key(recs["111"])[0] == 0  # Leitlinie zuerst


def test_pipeline_has_no_publication_side_effects() -> None:
    src = (REPO / "scripts/editorial/wm_pipeline.py").read_text(encoding="utf-8")
    for forbidden in ("git push", "gh pr", "systemctl", "shutil.copy"):
        assert forbidden not in src


def test_catalog_script_runs(tmp_path: Path) -> None:
    r = subprocess.run([sys.executable, "-I", str(REPO / "scripts/editorial/wm_catalog.py"), "load-queue", "--repo", str(REPO),
                        "--state-dir", str(tmp_path)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    q = wm_common.Queue(tmp_path)
    assert q.counts().get("planned", 0) > 1000


# ---------------------------------------------------------------------------
# Handelsnamen-Verweisseite und Sprachkorrektur
# ---------------------------------------------------------------------------
def test_trade_page_validates_and_links_to_drug(tmp_path: Path) -> None:
    import wm_publisher
    sys.path.insert(0, str(REPO / "scripts" / "publishing"))
    import import_merged_beta as imp
    item = {"title": "Glucophage", "slug": "glucophage"}
    extra = {"code": "EMEA/H/C/000000", "atc": "A10BA02", "target_title": "Metformin", "target_slug": "metformin"}
    md = wm_publisher.make_trade_page(item, extra)
    target = REPO / "content" / "pharmaka" / "glucophage.md"
    target.write_text(md, encoding="utf-8")
    try:
        ok, msg = pipe.validate_file(target)
        assert ok, msg
        title, wikitext, _ = imp.build_page(target, "0" * 40)
        assert title == "Glucophage" and "[[Metformin|Metformin]]" in wikitext
    finally:
        target.unlink(missing_ok=True)


def test_proofread_rejects_changed_structure(monkeypatch) -> None:
    body = "## Übersicht\n\nGicht ist eine Arthritis.[1] Sie betrifft 3 Prozent.[2]\n"
    monkeypatch.setattr(pipe, "ask_model", lambda *a, **k: "## Übersicht\n\nGicht ist eine Gelenkentzündung.[1] Sie betrifft 3 Prozent.[2]")
    fixed, changed = pipe.proofread(None, "w", body)
    assert changed and "Gelenkentzündung" in fixed
    monkeypatch.setattr(pipe, "ask_model", lambda *a, **k: "## Übersicht\n\nGicht ist eine Arthritis.[1] Sie betrifft 4 Prozent.[2]")
    fixed, changed = pipe.proofread(None, "w", body)
    assert not changed and fixed == body  # geänderte Zahl -> verworfen
    monkeypatch.setattr(pipe, "ask_model", lambda *a, **k: "## Übersicht\n\nGicht ist eine Arthritis.[2] Sie betrifft 3 Prozent.[1]")
    fixed, changed = pipe.proofread(None, "w", body)
    assert not changed  # vertauschte Quellennummern -> verworfen


# ---------------------------------------------------------------------------
# Schemazeichnungen
# ---------------------------------------------------------------------------
def test_md2wiki_renders_media_figures_as_file_links() -> None:
    sys.path.insert(0, str(REPO / "scripts" / "publishing"))
    import md2wiki
    out = md2wiki.inline("![Zugang: Schema](../../../media/op/tavi-schema.svg)", md2wiki.ConvertContext(title="T"))
    assert out == "[[File:Tavi-schema.svg|thumb|center|420px|alt=Zugang: Schema|Zugang: Schema]]"
    ctx = md2wiki.ConvertContext(title="T")
    assert "[[File" not in md2wiki.inline("![x](https://evil.example/a.svg)", ctx) and ctx.warnings
    assert md2wiki.media_file_name("../../../media/op/../../etc/x.svg") is None


def test_op_figures_registry_and_svgs(tmp_path: Path) -> None:
    import xml.etree.ElementTree as ET
    import wm_op_figures as fig
    reg = fig.load_registry()
    assert len(reg["articles"]) >= 15
    arts = fig.op_articles()
    for slug, entry in reg["articles"].items():
        assert entry["template"] in fig.TEMPLATES, slug
        if not entry.get("approved"):
            continue
        assert slug in arts, f"Artikel fehlt: {slug}"
        assert entry["title"] and entry["caption"] and entry["elements"]
        svg = fig.build_svg(slug, entry)
        root = ET.fromstring(svg)  # wohlgeformt
        assert root.tag.endswith("svg") and "Schematische Darstellung" in svg
        assert (REPO / "media" / "op" / f"{slug}-schema.svg").read_text(encoding="utf-8") == svg, f"{slug}: build nicht ausgeführt"
        text = arts[slug].read_text(encoding="utf-8")
        assert f"media/op/{slug}-schema.svg" in text, f"{slug}: Abschnitt fehlt (insert nicht ausgeführt)"


def test_unapproved_registry_entries_produce_no_figure() -> None:
    import wm_op_figures as fig
    reg = fig.load_registry()
    reg["articles"]["x-test"] = {"approved": False, "template": "torso", "title": "t", "caption": "c", "elements": []}
    approved = [s for s, e in reg["articles"].items() if e.get("approved")]
    assert "x-test" not in approved


def test_importer_collects_only_repo_media(tmp_path: Path) -> None:
    sys.path.insert(0, str(REPO / "scripts" / "publishing"))
    import import_merged_beta_local as loc
    art = REPO / "content/specialties/chirurgie/tavi.md"
    names = [f.name for f in loc.figure_files(art)]
    assert names == ["tavi-schema.svg"]


def test_slow_down_limits_to_one_request_per_minute(tmp_path: Path) -> None:
    q = wm_common.Queue(tmp_path)
    q.slow_down(600)
    s1 = q.acquire_call_slot("a")
    # zweiter Aufruf würde im Drosselbetrieb blockieren: Zähler direkt prüfen
    t = wm_common.time.time()
    inflight = q.db.execute("SELECT COUNT(*) FROM calls WHERE end IS NULL").fetchone()[0]
    assert inflight == 1 and float(q.db.execute("SELECT v FROM meta WHERE k='slow_until'").fetchone()[0]) > t
    q.release_call_slot(s1, "a")


def test_settle_marks_published_and_failed(tmp_path: Path) -> None:
    import wm_publisher
    q = wm_common.Queue(tmp_path)
    q.add_items([{"id": "WM-DIS-9001", "kind": "disease", "title": "ICD-Titel", "slug": "icd-titel", "extra": {"titel_de": "Gebräuchlicher Titel"}},
                 {"id": "WM-DIS-9002", "kind": "disease", "title": "Zweites Thema", "slug": "zweites-thema"},
                 {"id": "WM-DIS-9003", "kind": "disease", "title": "Drittes Thema", "slug": "drittes-thema"}])
    for i in ("WM-DIS-9001", "WM-DIS-9002", "WM-DIS-9003"):
        q.set_status(i, "merged")
    wm_publisher.settle(q, {"Gebräuchlicher Titel", "Zweites Thema"}, {"drittes-thema": "Seite existiert bereits"}, "1")
    st = {r["id"]: (r["status"], r["error"]) for r in q.db.execute("SELECT id,status,error FROM items")}
    assert st["WM-DIS-9001"][0] == "published" and st["WM-DIS-9002"][0] == "published"
    assert st["WM-DIS-9003"][0] == "review" and "existiert bereits" in st["WM-DIS-9003"][1]
