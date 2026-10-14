#!/usr/bin/env python3
"""Dauerbetrieb-Arbeiter der WikiMedica-Redaktionspipeline (lokales Modell über das AT-AI-Gateway).

Ablauf je Thema (Erkrankung oder Wirkstoff):
  1. Thema aus der SQLite-Warteschlange beanspruchen (atomar, mehrere Arbeiter ohne Kollision)
  2. englischen PubMed-Suchbegriff bestimmen (1 kurzer Modellaufruf)
  3. Recherche: PubMed (Leitlinien 10 J., Metaanalysen/Reviews 5 J.), PMC-Open-Access-Auszüge (wm_research)
  4. Entwurf mit nummerierten Quellen (1 Modellaufruf)
  5. Faktenprüfung: formale Prüfung (Quellennummern, Dosisangaben bei Arzneimitteln) und zweiter Modelldurchlauf
     je Satz gegen die abgerufenen Zusammenfassungen/Volltextauszüge; nicht belegte Sätze entfallen
  6. Bestehensgrenzen; sonst Prüfliste (Status review), NICHT veröffentlichen
  7. Artikel im Repo-Format mit PMID/DOI erzeugen, mit validate-metadata prüfen, in outbox/ ablegen

Veröffentlichung macht ausschließlich wm_publisher.py (Sammel-PR). Dieses Programm ändert weder Git noch MediaWiki.
Gateway-Grenzen: zentraler Zähler in der Warteschlange (wm_common.MAX_REQUESTS_PER_MIN / MAX_CONCURRENT).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request
from collections import OrderedDict
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import wm_research as research  # noqa: E402
from wm_common import DEFAULT_STATE_DIR, Queue, log, norm_title, slugify  # noqa: E402

GATEWAY = os.environ.get("AT_AI_BASE_URL", "http://10.90.0.1:8188/v1")
MODEL = os.environ.get("AT_AI_MODEL", "Qwen/Qwen3.6-35B-A3B-FP8")
HTTP_TIMEOUT_S = 1500
# Das Gateway erlaubt höchstens 8192 Ausgabetoken je Anfrage (HTTP 422 darüber). Die Denkphase des Modells zählt mit;
# deshalb wird sie mit dem Top-Level-Feld enable_thinking=false abgeschaltet (Messung 14.10.2026: 323 statt 4000+ Token,
# 4 s statt 40 s). Ohne diese Abschaltung wurden die Entwürfe der ersten zehn Themen abgeschnitten.
MAX_TOKENS_DRAFT = 8000
MAX_TOKENS_CHECK = 6000
MAX_TOKENS_SHORT = 1500
VALIDATOR = HERE.parent / "validation" / "validate-metadata.py"

DOSE_RE = re.compile(r"\b\d+([.,]\d+)?\s?(mg|µg|mcg|g|ml|IE|I\.E\.|mmol|ng|E)\s?(/|pro|je|täglich|am Tag|alle)", re.I)
CITE_RE = re.compile(r"\[(\d{1,2})\]")
ABBREV = re.compile(r"\b(z\.\s?B|d\.\s?h|u\.\s?a|u\.\s?U|v\.\s?a|i\.\s?d\.\s?R|bzw|ca|vs|ggf|inkl|evtl|sog|Nr|Abb|vgl|Tab|et al)\.")

DISEASE_SECTIONS = ["Übersicht", "Epidemiologie", "Ursachen und Pathophysiologie", "Klinik und Warnzeichen", "Diagnostik",
                    "Therapie", "Verlauf und Prognose", "Besonderheiten bei Frauen und Männern",
                    "Informationen für Patientinnen und Patienten"]
DRUG_SECTIONS = ["Übersicht", "Wirkmechanismus", "Indikationen", "Kontraindikationen und Warnhinweise", "Nebenwirkungen",
                 "Wechselwirkungen", "Besondere Patientengruppen", "Hinweise zur sicheren Anwendung"]

SYSTEM_DRAFT = (
    "Du bist Redaktionsassistent der deutschsprachigen medizinischen Wissensplattform WikiMedica (Zielgruppe: Gesundheitsfachpersonen). "
    "Schreibe einen eigenständigen, sachlichen Fachartikel in eigenen Worten (keine wörtlichen Übernahmen, keine Studienaufzählung). Regeln:\n"
    "1. Verwende ausschließlich Aussagen, die durch die nummerierten Quellen unten gedeckt sind; bevorzuge Leitlinien und neuere Quellen und "
    "nenne Abweichungen zwischen Quellen.\n"
    "2. Jeder Satz mit einer Sachaussage endet mit Satzzeichen und direkt danach der Quellennummer in eckigen Klammern, z. B. „... .[2]“ oder „... .[1][4]“. "
    "Verwende nur Nummern der Quellenliste. Keine PMIDs, keine Autorennamen, keine Fußnotentexte im Fließtext.\n"
    "3. Keine erfundenen Zahlen, Grenzwerte oder Dosierungen. Keine Dosierungsangaben zu Arzneimitteln.\n"
    "4. Gibt es zu einem Abschnitt keine belegten Aussagen, lasse den Abschnitt ersatzlos weg. Keine Platzhalter, keine Hinweise auf fehlende Quellen, "
    "keine Hinweise auf KI oder Entwurfsstatus.\n"
    "5. Sachlicher Ton, kein individueller Patientenrat, keine Tabellen. Fließtext in Absätzen; Aufzählungen nur wenn nötig.\n"
    "6. Gliederung mit Überschriften der Ebene 2 („## ...“) in dieser Reihenfolge, soweit belegbar: {sections}.\n"
    "7. Umfang 700 bis 1500 Wörter. Gib NUR den Artikeltext als Markdown aus: kein Frontmatter, keine Titelzeile, keine Einleitung, keine Schlussbemerkung, keine Quellenliste."
)

SYSTEM_CHECK = (
    "Du bist Faktenprüfer für medizinische Texte. Du erhältst nummerierte Quellen (Zusammenfassung oder Volltextauszug) und nummerierte Sätze eines "
    "Artikelentwurfs, die jeweils mit Quellennummern in eckigen Klammern belegt sind. Beurteile je Satz streng anhand der genannten Quellen:\n"
    "s = supported: die Kernaussage (inkl. genannter Zahlen, Gruppen, Richtung des Effekts) wird von mindestens einer der genannten Quellen gedeckt.\n"
    "p = partly: nur teilweise oder verallgemeinert gedeckt, Details/Zahlen nicht sicher.\n"
    "u = unsupported: nicht gedeckt, widersprochen oder stammt erkennbar nicht aus den genannten Quellen.\n"
    "Antworte NUR mit JSON, ohne Erklärung davor oder danach: {\"urteile\":[{\"id\":1,\"v\":\"s\"},{\"id\":2,\"v\":\"u\",\"g\":\"kurzer Grund\"}]}. "
    "Jede Satz-ID genau einmal."
)


class Truncated(RuntimeError):
    """Modellantwort wurde wegen max_tokens abgeschnitten."""


# ---------------------------------------------------------------------------
# Gateway
# ---------------------------------------------------------------------------
def ask_model(q: Queue, worker: str, prompt: str, max_tokens: int) -> str:
    cid, tok = os.environ.get("AT_AI_CLIENT_ID", ""), os.environ.get("AT_AI_CLIENT_TOKEN", "")
    if not cid or not tok:
        raise RuntimeError("AT_AI_CLIENT_ID/AT_AI_CLIENT_TOKEN fehlen (EnvironmentFile)")
    body = json.dumps({"model": MODEL, "max_tokens": max_tokens, "temperature": 0.2, "enable_thinking": False,
                       "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
    headers = {"Content-Type": "application/json", "x-at-ai-client-id": cid, "x-at-ai-client-token": tok}
    last = None
    for attempt in range(3):
        slot = q.acquire_call_slot(worker)
        try:
            req = urllib.request.Request(f"{GATEWAY}/chat/completions", data=body, headers=headers)
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            choice = data["choices"][0]
            text = (choice["message"].get("content") or "").strip()
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
            if choice.get("finish_reason") != "stop":
                raise Truncated(f"finish_reason={choice.get('finish_reason')} (max_tokens={max_tokens})")
            if not text:
                raise RuntimeError("Leere Modellantwort")
            return text
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
            last = exc
            time.sleep(20 * (attempt + 1))
        finally:
            q.release_call_slot(slot, worker)
    raise RuntimeError(f"Gateway nicht erreichbar: {last}")


def parse_json_answer(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("kein JSON in der Antwort")
    return json.loads(m.group(0))


# ---------------------------------------------------------------------------
# Textverarbeitung (reine Funktionen, getestet)
# ---------------------------------------------------------------------------
def normalize_citations(text: str) -> str:
    """„Satz [1, 2].“ / „Satz [1].“ / „Satz.[1]“ -> einheitlich „Satz.[1][2]“."""
    def expand(m: re.Match) -> str:
        nums = re.findall(r"\d+", m.group(0))
        return "".join(f"[{n}]" for n in nums)
    text = re.sub(r"\[(?:\d{1,2}(?:\s*[,;–-]\s*\d{1,2})*)\]", expand, text)
    text = re.sub(r"\s*((?:\[\d{1,2}\])+)\s*([.!?])(?!\d)", r"\2\1", text)  # Punkt vor die Quellen ziehen
    return text


def split_sentences(par: str) -> list[str]:
    t = ABBREV.sub(lambda m: m.group(0).replace(".", "\u2219"), par).strip()
    out, pos = [], 0
    for m in re.finditer(r"(.+?[.!?](?:\[\d{1,2}\])*)(?:\s+(?=[A-ZÄÖÜ0-9„\"(])|\s*$)", t, re.S):
        out.append(m.group(1).strip())
        pos = m.end()
    if t[pos:].strip():
        out.append(t[pos:].strip())
    return [s.replace("\u2219", ".") for s in out if s.strip()]


def split_units(body: str) -> list[dict]:
    """Zerlegt den Artikeltext in Überschriften und Sätze. Jede Einheit: {type, text, [section]}."""
    units, section = [], ""
    for line in normalize_citations(body).splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            title = s.lstrip("#").strip()
            if s.startswith("##"):
                section = title
                units.append({"type": "h", "text": title})
            continue  # Titelzeile (#) wird verworfen, der Titel kommt aus den Metadaten
        bullet = re.match(r"^([-*]|\d+\.)\s+(.*)$", s)
        if bullet:
            units.append({"type": "b", "text": bullet.group(2), "section": section})
        else:
            for sent in split_sentences(s):
                units.append({"type": "s", "text": sent, "section": section})
    return units


def cites(text: str) -> list[int]:
    return [int(x) for x in CITE_RE.findall(text)]


def formal_check(units: list[dict], n_sources: int, kind: str) -> dict:
    """Formale Prüfung: gültige Quellennummern, Belegpflicht, Dosisangaben bei Arzneimitteln."""
    removed = []
    for u in units:
        if u["type"] == "h":
            continue
        valid = [c for c in cites(u["text"]) if 1 <= c <= n_sources]
        if cites(u["text"]) and len(valid) != len(cites(u["text"])):
            # ungültige Nummern entfernen
            u["text"] = CITE_RE.sub(lambda m: m.group(0) if 1 <= int(m.group(1)) <= n_sources else "", u["text"])
        if not valid:
            u["drop"] = "ohne gültige Quellennummer"
        elif kind == "drug" and DOSE_RE.search(u["text"]):
            u["drop"] = "Dosisangabe in Wirkstoffartikel"
        if u.get("drop"):
            removed.append({"text": u["text"][:200], "grund": u["drop"]})
    return {"removed": removed}


def rebuild_body(units: list[dict]) -> tuple[str, dict]:
    """Baut den Text aus den behaltenen Einheiten; leere Abschnitte entfallen; Quellen werden neu nummeriert."""
    kept, current = [], None
    for u in units:
        if u["type"] == "h":
            current = {"h": u, "items": []}
            kept.append(current)
        elif not u.get("drop"):
            if current is None:
                current = {"h": {"text": "Übersicht"}, "items": []}
                kept.append(current)
            current["items"].append(u)
    kept = [k for k in kept if k["items"]]
    order: "OrderedDict[int, int]" = OrderedDict()
    for k in kept:
        for it in k["items"]:
            for c in cites(it["text"]):
                order.setdefault(c, len(order) + 1)

    def renum(t: str) -> str:
        t = CITE_RE.sub(lambda m: f"[{order[int(m.group(1))]}]", t)
        return re.sub(r"(\[(\d+)\])\1+", r"\1", t)  # doppelte identische Nummern zusammenfassen
    lines = []
    for k in kept:
        lines.append(f"## {k['h']['text']}\n")
        par, bullets = [], []
        for it in k["items"]:
            if it["type"] == "b":
                if par:
                    lines.append(" ".join(par) + "\n")
                    par = []
                bullets.append(f"- {renum(it['text'])}")
            else:
                if bullets:
                    lines.append("\n".join(bullets) + "\n")
                    bullets = []
                par.append(renum(it["text"]))
        if par:
            lines.append(" ".join(par) + "\n")
        if bullets:
            lines.append("\n".join(bullets) + "\n")
    stats = {"sections": len(kept), "sentences": sum(len(k["items"]) for k in kept), "sources": len(order)}
    return "\n".join(lines).strip() + "\n", {"order": list(order), **stats}


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------
def source_block(recs: list[dict]) -> str:
    parts = []
    for i, r in enumerate(recs, 1):
        kind = "Leitlinie" if any("guideline" in p.lower() for p in r["ptypes"]) else \
            "Metaanalyse/systematische Übersicht" if any(p in ("Meta-Analysis", "Systematic Review") for p in r["ptypes"]) else "Übersichtsarbeit"
        txt = f"[{i}] ({kind}, {r['year']}, {r['journal']}) {r['title']}\nZusammenfassung: {r['abstract'][:2800]}"
        if r.get("fulltext"):
            txt += f"\nVolltextauszug (Open Access): {r['fulltext']}"
        parts.append(txt)
    return "\n\n".join(parts)


def draft_prompt(item, kind: str, recs: list[dict]) -> str:
    sections = DRUG_SECTIONS if kind == "drug" else DISEASE_SECTIONS
    topic = f"Thema: {item['title']}" + (" (Arzneimittelwirkstoff)" if kind == "drug" else " (Diagnose nach ICD-10-GM)")
    ex = json.loads(item["extra"]) if isinstance(item.get("extra"), str) else (item.get("extra") or {})
    if kind == "disease" and ex.get("icd_title") and ex["icd_title"] != item["title"]:
        topic += f"; Klassifikationsbezeichnung: {ex['icd_title']}"
    return (SYSTEM_DRAFT.format(sections=", ".join(sections)) + f"\n\n---\n{topic}\n\nQuellen (nur diese verwenden):\n\n{source_block(recs)}")


def check_prompt(units: list[dict], recs: list[dict]) -> tuple[str, list[int]]:
    id_map, lines = [], []
    n = 0
    for pos, u in enumerate(units):
        if u["type"] == "h" or u.get("drop"):
            continue
        n += 1
        id_map.append(pos)
        lines.append(f"{n}. {u['text']}")
    return (SYSTEM_CHECK + f"\n\n---\nQuellen:\n\n{source_block(recs)}\n\n---\nSätze:\n" + "\n".join(lines)), id_map


# ---------------------------------------------------------------------------
# Artikel erzeugen
# ---------------------------------------------------------------------------
HIGH_RISK_SPECIALTIES = {"Notfallmedizin", "Intensivmedizin", "Hämatologie/Onkologie"}


def yq(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def build_article(item, kind: str, body: str, recs: list[dict], order: list[int], extra: dict, report: dict) -> str:
    today = date.today().isoformat()
    used = [recs[i - 1] for i in order]
    refs = [{"citation": research.citation(r), "pmid": r["pmid"], "doi": r["doi"],
             "url": f"https://pubmed.ncbi.nlm.nih.gov/{r['pmid']}/"} for r in used]
    guidelines = [{"title": r["title"], "issuer": "", "year": int(r["year"]) if r["year"].isdigit() else None,
                   "url": f"https://pubmed.ncbi.nlm.nih.gov/{r['pmid']}/"}
                  for r in used if any("guideline" in p.lower() for p in r["ptypes"])]
    for g in research.awmf_guidelines(item["slug"]):
        guidelines.append(g)
    spec = item["specialty"] or "Innere Medizin"
    risk = "high" if (kind == "drug" or spec in HIGH_RISK_SPECIALTIES) else "moderate"
    meta = [
        f"title: {yq(item['title'])}", f"slug: {yq(item['slug'])}", f"specialty: {yq(spec)}",
        "secondary_specialties: []", f"article_type: {yq('pharmaka' if kind == 'drug' else 'professional')}",
        'content_kind: "article"', 'status: "draft"', 'version: "0.1.0"',
        f"change_summary: {yq('Automatisch erstellter, quellenbasierter Erstentwurf mit maschineller Faktenprüfung gegen PubMed-Quellen; fachärztliche Prüfung steht aus.')}",
        'authors: [{name: "WikiMedica-Redaktion"}]', "reviewers: []", f'created: "{today}"', f'updated: "{today}"',
        f"risk_level: {yq(risk)}",
        "target_audience: " + ('["physicians", "pharmacists"]' if kind == "drug" else '["medical-professionals"]'),
        'sex_gender_relevance: "not_assessed"', 'sex_gender_notes: ""', "safety_hold: false", 'language: "de"', 'language_level: "professional"',
    ]
    if kind == "drug":
        meta += [f"active_substances: [{yq(item['title'])}]", "atc_codes: " + json.dumps(extra.get("codes") or [extra.get("code")], ensure_ascii=False)]
    meta += [
        "icd10: " + (json.dumps([extra["code"]]) if kind == "disease" and extra.get("code") else "[]"), "ops: []",
        "pubmed_ids: " + json.dumps([r["pmid"] for r in used]),
        "guidelines: " + json.dumps(guidelines, ensure_ascii=False),
        "references: " + json.dumps(refs, ensure_ascii=False),
        f"source_notes: {yq('Eigene Zusammenfassung von PubMed-Zusammenfassungen und, wo Creative-Commons-Lizenz vorliegt, PubMed-Central-Volltextauszügen; keine wörtliche Übernahme. Alle zitierten PMIDs wurden gegen PubMed aufgelöst. Katalogbezug: ' + ('ICD-10-GM 2026 (BfArM)' if kind == 'disease' else 'ATC-GM mit DDD 2026 (BfArM; Urheber WIdO, beruht auf WHO ATC-Index), keine DDD übernommen') + '.')}",
        "ai_assisted: true",
        f"ai_assistance_description: {yq('Entwurf und satzweise Faktenprüfung durch ' + MODEL + ' über das AT-AI-Gateway (Hetzner) auf Grundlage automatisch abgerufener PubMed-Quellen. Maschinelle Faktenprüfung: ' + str(report['kept']) + ' von ' + str(report['total']) + ' Sätzen bestätigt, ' + str(report['removed']) + ' nicht belegte Sätze entfernt. Keine menschliche fachliche Prüfung.')}",
        "wikimedica_credit: true", "corrections: []",
    ]
    lit = "\n".join(f"{i}. {r['citation']} PMID: {r['pmid']}." + (f" DOI: {r['doi']}." if r["doi"] else "") + f" https://pubmed.ncbi.nlm.nih.gov/{r['pmid']}/"
                    for i, r in enumerate(refs, 1))
    return "---\n" + "\n".join(meta) + f"\n---\n\n# {item['title']}\n\n{body}\n## Literatur\n\n{lit}\n"


def validate_file(path: Path) -> tuple[bool, str]:
    r = subprocess.run([sys.executable, str(VALIDATOR), str(path)], capture_output=True, text=True, timeout=120)
    return r.returncode == 0, (r.stdout + r.stderr).strip()[-600:]


# ---------------------------------------------------------------------------
# Arbeiter
# ---------------------------------------------------------------------------
def known_slugs(state_dir: Path) -> dict:
    try:
        return json.loads((state_dir / "known-articles.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"slugs": [], "titles": []}


def term_for(q: Queue, worker: str, item, kind: str) -> tuple[str, str]:
    """Englischer PubMed-Suchbegriff und (bei Erkrankungen) gebräuchlicher deutscher Artikeltitel; zwischengespeichert."""
    extra = json.loads(item["extra"] or "{}")
    if extra.get("term_en"):
        return extra["term_en"], extra.get("titel_de", item["title"])
    if kind == "drug":
        prompt = (f"Nenne den internationalen Freinamen (INN, englisch) für den folgenden Wirkstoff nach deutscher ATC-Bezeichnung. "
                  f"Antworte NUR mit JSON: {{\"term\":\"...\"}} (höchstens vier Wörter, keine Erklärung).\n\n{item['title']}")
    else:
        prompt = (f"Für die folgende Diagnose (ICD-10-GM) benötige ich 1. den gebräuchlichsten englischen PubMed-Suchbegriff (MeSH-Begriff, "
                  f"höchstens fünf Wörter) und 2. den gebräuchlichsten deutschen Artikeltitel, wie ihn ein Lehrbuch oder die Fachgesellschaften "
                  f"verwenden (ohne lateinische Fachsprache, wenn ein üblicher deutscher Begriff existiert; höchstens 70 Zeichen). "
                  f"Antworte NUR mit JSON: {{\"term\":\"...\",\"titel\":\"...\"}}\n\n{item['title']}")
    ans = parse_json_answer(ask_model(q, worker, prompt, MAX_TOKENS_SHORT))
    term = re.sub(r"[^A-Za-z0-9 ,'/-]", "", str(ans.get("term", ""))).strip()[:80]
    if len(term) < 3:
        raise RuntimeError("kein englischer Suchbegriff")
    titel = item["title"]
    if kind == "disease":
        cand = re.sub(r"\s+", " ", "".join(" " if c in "#<>[]|{}:" else c for c in str(ans.get("titel", "")))).strip()
        if 3 <= len(cand) <= 70:
            titel = cand
    q.merge_extra(item["id"], {"term_en": term, "titel_de": titel})
    return term, titel


LEKTORAT = ("Korrigiere in dem folgenden medizinischen Text ausschließlich Rechtschreibung, Grammatik, Wortwahl und Satzbau (Deutsch, sachlicher Stil). "
            "Verändere keine Inhalte, Zahlen, Gruppen oder Aussagen. Behalte jede Quellennummer [n] exakt an derselben Stelle, alle Überschriften "
            "(## ...) und die Zahl der Sätze. Gib NUR den korrigierten Text aus, ohne Einleitung.\n\n---\n")


def proofread(q: Queue, worker: str, body: str) -> tuple[str, bool]:
    """Sprachliche Korrektur; wird nur übernommen, wenn Struktur, Quellennummern und Zahlen unverändert sind."""
    try:
        fixed = ask_model(q, worker, LEKTORAT + body, MAX_TOKENS_DRAFT)
    except (Truncated, RuntimeError):
        return body, False
    fixed = fixed.strip() + "\n"
    def sig(t: str) -> list:
        return [(u["type"], u["text"] if u["type"] == "h" else tuple(cites(u["text"]))) for u in split_units(t)]
    nums = lambda t: sorted(re.findall(r"\d+(?:[.,]\d+)?", CITE_RE.sub("", t)))
    if sig(fixed) == sig(body) and nums(fixed) == nums(body) and not DOSE_RE.search(fixed.replace(body, "")):
        return fixed, fixed.strip() != body.strip()
    return body, False


def process(q: Queue, worker: str, item, out_dir: Path, review_dir: Path, state_dir: Path) -> None:
    kind = item["kind"]
    iid = item["id"]
    extra = json.loads(item["extra"] or "{}")
    known = known_slugs(state_dir)
    if item["slug"] in known["slugs"]:
        q.set_status(iid, "duplicate", "Artikel mit diesem Slug existiert bereits")
        q.event(iid, "duplicate", item["slug"])
        return
    term, titel = term_for(q, worker, item, kind)
    if kind == "disease" and titel != item["title"]:
        nt = norm_title(titel)
        if slugify(titel) in known["slugs"] or nt in known.get("titles", []):
            q.set_status(iid, "duplicate", f"Artikel '{titel}' existiert bereits")
            q.event(iid, "duplicate", titel)
            return
        item = {**dict(item), "title": titel}
        extra["icd_title"] = extra.get("icd_title") or ""
    recs = research.gather(term)
    if len(recs) < 4:  # zweiter Versuch mit allgemeinerem Begriff
        prompt = (f"Der PubMed-Suchbegriff '{term}' für das Thema '{item['title']}' liefert zu wenige Übersichtsarbeiten. "
                  "Nenne einen allgemeineren, gebräuchlichen englischen PubMed-Suchbegriff (MeSH). Antworte NUR mit JSON: {\"term\":\"...\"}")
        try:
            term2 = re.sub(r"[^A-Za-z0-9 ,'/-]", "", str(parse_json_answer(ask_model(q, worker, prompt, MAX_TOKENS_SHORT)).get("term", ""))).strip()[:80]
        except (ValueError, Truncated):
            term2 = ""
        if len(term2) >= 3 and term2.lower() != term.lower():
            recs2 = research.gather(term2)
            if len(recs2) > len(recs):
                recs, term = recs2, term2
    if len(recs) < 4:
        q.set_status(iid, "review", f"zu wenige Quellen mit Zusammenfassung ({len(recs)}) für '{term}'")
        q.event(iid, "review", "zu wenige Quellen")
        return
    t0 = time.time()
    draft = ask_model(q, worker, draft_prompt(item, kind, recs), MAX_TOKENS_DRAFT)
    units = split_units(draft)
    formal = formal_check(units, len(recs), kind)
    prompt, id_map = check_prompt(units, recs)
    if not id_map:
        q.set_status(iid, "review", "Entwurf ohne belegte Sätze")
        return
    verdict_raw = ask_model(q, worker, prompt, MAX_TOKENS_CHECK)
    arr = parse_json_answer(verdict_raw).get("urteile", [])
    verdicts = {int(a["id"]): (str(a.get("v", "u"))[:1].lower(), str(a.get("g", ""))) for a in arr if "id" in a}
    pos_by_sid = {sid + 1: pos for sid, pos in enumerate(id_map)}
    for sid, pos in pos_by_sid.items():
        v, why = verdicts.get(sid, ("u", "kein Urteil"))
        units[pos]["verdict"] = v
        if v == "u":
            units[pos]["drop"] = f"Faktenprüfung: {why or 'nicht belegt'}"
    body, st = rebuild_body(units)
    body, polished = proofread(q, worker, body)
    total = sum(1 for u in units if u["type"] != "h")
    kept = st["sentences"]
    partly = sum(1 for u in units if u.get("verdict") == "p" and not u.get("drop"))
    report = {"total": total, "kept": kept, "removed": total - kept, "partly": partly, "formal_removed": formal["removed"],
              "dropped": [{"text": u["text"][:160], "grund": u["drop"]} for u in units if u.get("drop")][:60],
              "sections": st["sections"], "sources_cited": st["sources"], "seconds": round(time.time() - t0), "term": term,
              "titel": titel, "lektorat": polished}
    reasons = []
    if kept < 10:
        reasons.append(f"nur {kept} bestätigte Sätze")
    if st["sections"] < 3:
        reasons.append(f"nur {st['sections']} Abschnitte")
    if st["sources"] < 3:
        reasons.append(f"nur {st['sources']} Quellen zitiert")
    if total and kept / total < 0.6:
        reasons.append(f"Bestätigungsquote {kept}/{total} unter 60 %")
    if partly and kept and partly / kept > 0.4:
        reasons.append(f"zu viele nur teilweise belegte Sätze ({partly}/{kept})")
    md = build_article(item, kind, body, recs, st["order"], extra, report)
    dest = (review_dir if reasons else out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / f"{item['slug']}.md"
    path.write_text(md, encoding="utf-8")
    (dest / f"{item['slug']}.json").write_text(json.dumps({"id": iid, "kind": kind, **report, "reasons": reasons}, ensure_ascii=False, indent=1), encoding="utf-8")
    if reasons:
        q.set_status(iid, "review", "; ".join(reasons), draft_path=str(path))
        q.event(iid, "review", "; ".join(reasons))
        return
    ok, msg = validate_file(path)
    if not ok:
        q.set_status(iid, "review", f"Metadatenprüfung: {msg[-300:]}", draft_path=str(path))
        q.event(iid, "review", "Metadatenprüfung fehlgeschlagen")
        return
    q.set_status(iid, "ready", None, draft_path=str(path))
    q.event(iid, "ready", f"{item['slug']}: {kept}/{total} Sätze, {st['sources']} Quellen, {report['seconds']} s")
    log(f"{iid} {item['slug']}: bereit ({kept}/{total} Sätze, {st['sources']} Quellen, {report['seconds']} s)")


def worker_loop(args) -> int:
    state = Path(args.state_dir)
    q = Queue(state)
    out_dir, review_dir = state / "outbox", state / "review"
    kinds = args.kinds.split(",")
    name = args.name
    log(f"Arbeiter {name} gestartet (Modell {MODEL}, Arten {kinds})")
    while True:
        if (state / "pipeline.stop").exists():
            log("pipeline.stop vorhanden, Arbeiter beendet")
            return 0
        if (state / "pipeline.pause").exists():
            time.sleep(60)
            continue
        ready_backlog = q.counts().get("ready", 0)
        if ready_backlog >= args.max_ready:  # Veröffentlichung hinkt hinterher: nicht weiter anhäufen
            time.sleep(120)
            continue
        item = q.claim(name, kinds)
        if item is None:
            log("Keine offenen Themen")
            if args.once:
                return 0
            time.sleep(300)
            continue
        try:
            process(q, name, item, out_dir, review_dir, state)
        except Truncated as exc:
            q.release(item["id"], f"Truncated: {exc}")
            q.event(item["id"], "error", f"Truncated: {exc}")
        except (RuntimeError, ValueError, OSError, urllib.error.URLError, KeyError, json.JSONDecodeError) as exc:
            q.release(item["id"], f"{type(exc).__name__}: {exc}")
            q.event(item["id"], "error", f"{type(exc).__name__}: {exc}")
            log(f"{item['id']}: Fehler {type(exc).__name__}: {exc}")
        except Exception:  # unerwartet: nicht den ganzen Dienst verlieren
            q.release(item["id"], "unerwartet: " + traceback.format_exc()[-300:])
            log(traceback.format_exc())
        if args.once:
            return 0
        time.sleep(2)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    ap.add_argument("--name", default="w1")
    ap.add_argument("--kinds", default="disease,drug")
    ap.add_argument("--max-ready", type=int, default=400, help="Pause, wenn so viele fertige Artikel auf Veröffentlichung warten")
    ap.add_argument("--once", action="store_true")
    return worker_loop(ap.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
