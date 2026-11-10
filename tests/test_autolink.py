"""Automatische Querverweise: Regeln aus dem Auftrag vom 10.11.2026 (Projekt 15, #712)."""

from __future__ import annotations

from conftest import load_script

al = load_script("scripts/publishing/autolink.py", "autolink")

TITLES = ["Arterielle Hypertonie", "Furosemid", "Herzinsuffizienz", "Chronische Herzinsuffizienz", "Niereninsuffizienz",
          "Ulcus cruris (offenes Bein)", "ACE", "Dosis"]
REDIRECTS = {"Lasix": "Furosemid", "Bluthochdruck": "Arterielle Hypertonie", "Hypertonie": "Arterielle Hypertonie"}


def linker():
    return al.Linker(al.build_targets(TITLES, REDIRECTS))


def run(text, own="Testartikel"):
    return linker().link(text, own)[0]


def test_erstes_vorkommen_und_weiterleitung_aufgeloest():
    out = run("Bluthochdruck ist häufig. Bluthochdruck bleibt oft unerkannt. Furosemid hilft, Furosemid wirkt rasch.")
    assert out.count("[[Arterielle Hypertonie|Bluthochdruck]]") == 1
    assert out.count("[[Furosemid]]") == 1
    assert out.count("Bluthochdruck") == 2  # eine verlinkt, eine als Klartext


def test_laengste_uebereinstimmung_zuerst():
    out = run("Chronische Herzinsuffizienz ist häufig.")
    assert "[[Chronische Herzinsuffizienz]]" in out
    assert "[[Herzinsuffizienz]]" not in out


def test_grossschreibung_nur_am_wortanfang_flexibel():
    assert "[[Arterielle Hypertonie|arterielle Hypertonie]]" in run("Die arterielle Hypertonie ist ...")
    assert "[[Furosemid" not in run("FUROSEMID ist laut.")


def test_keine_selbstlinks_auch_nicht_ueber_weiterleitung():
    assert "[[" not in run("Bluthochdruck und Hypertonie sind dasselbe.", own="Arterielle Hypertonie")


def test_geschuetzte_bereiche():
    text = (
        "== Furosemid bei Herzinsuffizienz ==\n"
        "Text<ref name=\"a\">Furosemid Studie</ref> mit {{Vorlage|Furosemid}} und <code>Furosemid</code>.\n"
        "<blockquote>Furosemid im Zitat</blockquote>\n"
        "{| class=\"wikitable\"\n! Furosemid\n|-\n| Zelle Niereninsuffizienz\n|}\n"
        "<!-- Furosemid -->\n"
        "Schon [[Furosemid|verlinkt]] hier. https://example.org/Furosemid\n"
    )
    out = run(text)
    assert out.count("[[Furosemid") == 1  # nur der vorhandene
    assert "== Furosemid bei Herzinsuffizienz ==" in out
    assert "<ref name=\"a\">Furosemid Studie</ref>" in out
    assert "[[Niereninsuffizienz]]" in out  # Tabellenzelle darf, Kopfzeile nicht
    assert "! Furosemid\n" in out


def test_abschnitte_siehe_auch_und_einzelnachweise_bleiben_unberuehrt():
    text = "Intro Furosemid.\n\n== Siehe auch ==\n* Niereninsuffizienz\n\n== Einzelnachweise ==\n<references />\n"
    out = run(text)
    assert "[[Furosemid]]" in out
    assert "* Niereninsuffizienz" in out and "[[Niereninsuffizienz" not in out


def test_woerter_innerhalb_anderer_woerter_werden_nicht_verlinkt():
    out = run("Antifurosemid, Furosemidtherapie und Furosemid-Gabe, aber Niereninsuffizienzen auch.")
    assert "[[" not in out


def test_mehrdeutig_und_zu_kurz_und_stoppwort():
    t = al.build_targets(["Alpha", "Beta", "Dosis", "ACE", "AB"], {"Gemeinsam": "Alpha"})
    assert "Dosis" not in t and "AB" not in t and "ACE" in t
    t2 = al.build_targets(["Alpha", "Beta"], {"Doppelt": "Alpha"})
    t2b = al.build_targets(["Alpha", "Beta"], {"Doppelt": "Alpha", "Alpha-Zwilling": "Beta"})
    assert "Doppelt" in t2 and "Alpha-Zwilling" in t2b
    amb = al.build_targets(["Zwei (Herz)", "Zwei (Niere)"])
    assert "Zwei" not in amb and "Zwei (Herz)" in amb  # Kurzform hat zwei Ziele: nie verlinken


def test_klammerzusatz_wird_als_kurzform_verlinkt():
    assert "[[Ulcus cruris (offenes Bein)|Ulcus cruris]]" in run("Ein Ulcus cruris entsteht.")


def test_beta_hinweis_nach_trennlinie_bleibt_unberuehrt():
    out = run("Furosemid.\n\n----\n'''BETA-Hinweis:''' Furosemid\n")
    assert out.count("[[Furosemid]]") == 1


def test_obergrenze():
    t = {f"Begriff{i}x": f"Ziel{i}" for i in range(10)}
    out, done = al.Linker(t).link(" ".join(t), "X", max_links=3)
    assert len(done) == 3
