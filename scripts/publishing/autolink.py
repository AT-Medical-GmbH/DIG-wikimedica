#!/usr/bin/env python3
"""Automatische Querverweise: Fachbegriffe mit vorhandenem Artikel werden beim ersten Vorkommen verlinkt.

Feste Regel der Veröffentlichungs-Pipeline (Auftrag Andreas 10.11.2026, Projekt 15, Auftragsbuch core #712).
Arbeitet auf dem fertig konvertierten Wikitext eines Artikels, vor Ergänzung von „Siehe auch“, Hinweis und Kategorien.

Regeln:
* Pro Artikel und Ziel höchstens ein Link (erstes Vorkommen). Ein im Text schon vorhandener Link auf das Ziel zählt als erstes Vorkommen.
* Keine Selbstlinks (auch nicht über Weiterleitungen auf den eigenen Artikel).
* Nie verlinkt wird in: Überschriften, Tabellenköpfen, Zitaten (``<blockquote>``), Vorlagen (``{{…}}``), Fußnoten (``<ref>``),
  Code/Mathematik/nowiki/pre, HTML-Kommentaren, Warnkasten (``<div>``), vorhandenen Links, Web-Adressen sowie den Abschnitten
  „Siehe auch“, „Einzelnachweise“, „Weblinks“, „Literatur“ und „Für Patientinnen und Patienten“.
* Weiterleitungen werden aufgelöst: ``[[Ziel|Anzeigetext]]``. Längste Übereinstimmung zuerst (Mehrwortbegriffe vor Einzelwörtern).
* Der erste Buchstabe darf in der Groß-/Kleinschreibung abweichen, der Rest muss exakt stimmen; Wortgrenzen werden geprüft.
* Mehrdeutige Oberflächenformen (zwei verschiedene Ziele) und zu kurze Formen werden nie verlinkt.

Aufruf zum Auffrischen der Weiterleitungsliste aus dem laufenden Wiki (nur lesend)::

    python3 scripts/publishing/autolink.py --refresh-aliases [--container wikimedica_app]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ALIAS_FILE = ROOT / "data" / "editorial" / "link-aliases.json"
MIN_SURFACE = 4          # kürzere Formen nie (Ausnahme: reine Großbuchstaben-Kürzel ab 3 Zeichen)
MAX_LINKS = 40           # Obergrenze je Artikel, damit der Text lesbar bleibt
SKIP_SECTIONS = {"Siehe auch", "Einzelnachweise", "Weblinks", "Literatur", "Für Patientinnen und Patienten"}
# Allgemeinwörter, die als Titel oder Weiterleitung vorkommen können, aber im Fließtext nicht verlinkt werden sollen
STOPWORDS = {"Alter", "Dosis", "Risiko", "Studie", "Studien", "Therapie", "Diagnose", "Wirkung", "Anwendung", "Übersicht"}

_WORD = re.compile(r"[A-Za-zÄÖÜäöüß0-9][A-Za-zÄÖÜäöüß0-9\-]*")
_PROTECTED = re.compile(
    r"""
      <!--.*?-->
    | <ref\b[^>]*/>
    | <ref\b[^>]*>.*?</ref>
    | <(?P<t>code|nowiki|pre|math|blockquote|gallery|syntaxhighlight|source|div|poem|references)\b[^>]*>.*?</(?P=t)>
    | <references\b[^>]*/>
    | \[\[.*?\]\]
    | \[(?:https?:)?//[^\]]*\]
    | https?://[^\s<>\]]+
    | \{\{.*?\}\}
    | \{\|[^\n]*                      # Tabellenanfang
    | ^[ \t]*!(?!\!)[^\n]*$           # Tabellenkopf-Zeile
    | ^[ \t]*=+[^\n]*=+[ \t]*$        # Überschrift
    """,
    re.S | re.M | re.X,
)
_HEADING = re.compile(r"^[ \t]*(=+)[ \t]*(.*?)[ \t]*=+[ \t]*$", re.M)
_LINK_TARGET = re.compile(r"\[\[([^\]|#]+)")


def _canon(title: str) -> str:
    return title.strip()


def build_targets(titles, redirects: dict[str, str] | None = None) -> dict[str, str]:
    """Oberflächenform -> Zielseitentitel. ``titles``: alle echten Artikel, ``redirects``: Weiterleitung -> Ziel."""
    titles = {_canon(t) for t in titles if t}
    redirects = {_canon(a): _canon(t) for a, t in (redirects or {}).items()}

    def resolve(t: str) -> str | None:
        seen = set()
        while t in redirects and t not in seen:
            seen.add(t)
            t = redirects[t]
        return t if t in titles else None

    cand: dict[str, set[str]] = {}

    def add(surface: str, target: str) -> None:
        surface = surface.strip()
        if surface in STOPWORDS or any(c in surface for c in "#<>[]|{}:"):
            return
        ok = len(surface) >= MIN_SURFACE or (len(surface) >= 3 and surface.isupper())
        if ok:
            cand.setdefault(surface, set()).add(target)

    for t in titles:
        add(t, t)
        short = re.sub(r"\s*\([^)]*\)\s*$", "", t).strip()
        if short != t:
            add(short, t)
    for alias in redirects:
        target = resolve(alias)
        if target and alias not in titles:
            add(alias, target)
            short = re.sub(r"\s*\([^)]*\)\s*$", "", alias).strip()
            if short != alias:
                add(short, target)
    return {s: next(iter(ts)) for s, ts in cand.items() if len(ts) == 1}


class Linker:
    def __init__(self, targets: dict[str, str]):
        self.targets = targets
        self.by_first: dict[str, list[str]] = {}
        for s in targets:
            first = _WORD.match(s)
            if first:
                self.by_first.setdefault(first.group(0).lower(), []).append(s)
        for lst in self.by_first.values():
            lst.sort(key=len, reverse=True)  # längste Übereinstimmung zuerst

    def _match_at(self, text: str, pos: int, first_lower: str, limit: int) -> str | None:
        for s in self.by_first.get(first_lower, ()):
            end = pos + len(s)
            if end > limit:
                continue
            if text[pos + 1:end] != s[1:] or text[pos].lower() != s[0].lower():
                continue
            if end < len(text) and (text[end].isalnum() or text[end] == "-" and end + 1 < len(text) and text[end + 1].isalnum()):
                continue
            return s
        return None

    def link(self, wikitext: str, own_title: str, max_links: int = MAX_LINKS) -> tuple[str, list[tuple[str, str]]]:
        """Gibt (neuer Wikitext, [(Anzeigetext, Ziel), …]) zurück."""
        spans = [(m.start(), m.end()) for m in _PROTECTED.finditer(wikitext)]
        spans += _skipped_sections(wikitext)
        spans.sort()
        merged: list[list[int]] = []
        for a, b in spans:
            if merged and a <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        linked = {_canon(own_title)}  # Selbstlinks ausschließen
        for m in _LINK_TARGET.finditer(wikitext):  # schon vorhandene Links zählen als erstes Vorkommen
            linked.add(_canon(m.group(1)))
        own_aliases = {s for s, t in self.targets.items() if t == _canon(own_title)}
        out: list[str] = []
        done: list[tuple[str, str]] = []
        cursor = 0

        def process(seg_start: int, seg_end: int) -> None:
            nonlocal cursor
            pos = seg_start
            while pos < seg_end and len(done) < max_links:
                m = _WORD.search(wikitext, pos, seg_end)
                if not m:
                    break
                start = m.start()
                if start > 0 and (wikitext[start - 1].isalnum() or wikitext[start - 1] == "-"):
                    pos = m.end()  # mitten in einem Wort (z. B. nach Bindestrich)
                    continue
                surf = self._match_at(wikitext, start, m.group(0).lower(), seg_end)
                if surf is None:
                    pos = m.end()
                    continue
                target = self.targets[surf]
                if target in linked or surf in own_aliases:
                    pos = start + len(surf)
                    continue
                shown = wikitext[start:start + len(surf)]
                out.append(wikitext[cursor:start])
                out.append(f"[[{target}]]" if shown == target else f"[[{target}|{shown}]]")
                cursor = start + len(surf)
                linked.add(target)
                done.append((shown, target))
                pos = cursor

        prev = 0
        for a, b in merged:
            process(prev, a)
            prev = b
        process(prev, len(wikitext))
        out.append(wikitext[cursor:])
        return "".join(out), done


def _skipped_sections(text: str) -> list[tuple[int, int]]:
    heads = [(m.start(), m.group(2).strip(), len(m.group(1))) for m in _HEADING.finditer(text)]
    spans = []
    for i, (start, name, level) in enumerate(heads):
        if name in SKIP_SECTIONS:
            end = len(text)
            for s2, _, l2 in heads[i + 1:]:
                if l2 <= level:
                    end = s2
                    break
            spans.append((start, end))
    # Abschlussblock nach der Trennlinie (BETA-Hinweis) nie verlinken
    sep = text.find("\n----\n")
    if sep >= 0:
        spans.append((sep, len(text)))
    return spans


# --- Weiterleitungsliste aus dem Wiki (nur lesend) -------------------------------------------------------------

def read_dump(xml_bytes: bytes) -> tuple[list[str], dict[str, str]]:
    """Titel (Hauptnamensraum, keine Weiterleitung) und Weiterleitungen aus einem dumpBackup-Auszug."""
    titles: list[str] = []
    redirects: dict[str, str] = {}
    root = ET.fromstring(xml_bytes)
    ns = root.tag.split("}")[0] + "}" if root.tag.startswith("{") else ""
    for page in root.iter(ns + "page"):
        if page.findtext(ns + "ns") != "0":
            continue
        title = page.findtext(ns + "title") or ""
        red = page.find(ns + "redirect")
        if red is not None:
            redirects[title] = red.get("title") or ""
        else:
            titles.append(title)
    return titles, redirects


def refresh_aliases(container: str, dest: Path = ALIAS_FILE) -> dict:
    out = subprocess.run(["docker", "exec", container, "php", "maintenance/run.php", "dumpBackup", "--current", "--quiet"],
                         capture_output=True, check=True, timeout=600).stdout
    titles, redirects = read_dump(out)
    data = {"titles": sorted(titles), "redirects": dict(sorted(redirects.items()))}
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    return {"titles": len(titles), "redirects": len(redirects), "file": str(dest)}


def load_alias_file(path: Path = ALIAS_FILE) -> tuple[list[str], dict[str, str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return list(data.get("titles") or []), dict(data.get("redirects") or {})
    except (OSError, ValueError):
        return [], {}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--refresh-aliases", action="store_true")
    p.add_argument("--container", default="wikimedica_app")
    args = p.parse_args()
    if args.refresh_aliases:
        print(json.dumps(refresh_aliases(args.container), ensure_ascii=False))
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
