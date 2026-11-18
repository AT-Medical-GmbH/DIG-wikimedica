#!/usr/bin/env python3
"""Neuimport aller Live-Artikel nach Einführung der automatischen Querverweise (#932, Andreas 10.11.2026, Option A).

Regeln:
* Es wird nur importiert, wenn der Seitentext OHNE Links (Wikilinks auf Anzeigetext reduziert, ohne „Siehe auch“, Kategorien,
  Hinweiskasten, BETA-Fußzeile) dem Live-Text entspricht. Weicht er ab, wird die Seite übersprungen und gemeldet.
* Seiten mit gültigem Prüfvermerk (geprueft.json: gespeicherter fach_hash == fach_hash der Live-Seite): nach dem Import werden
  fach_hash und revision in geprueft.json auf den neuen Stand nachgeführt; Reviewer und Datum bleiben.
* Seiten, bei denen der Vermerk schon vorher fehlte (gespeicherter Hash weicht von der Live-Seite ab), werden importiert, aber
  NICHT nachgeführt (der Vermerk bleibt weg).
* Etappen (--stage), Pause dazwischen (--pause), Abbruch bei Fehlern, fortsetzbar über --state.
Aufruf (auf dem Wiki-Server, Importer-Klon /opt/wikimedica-source muss den Stand mit Querverweisen haben):
    python3 reimport_autolink.py --dry-run
    python3 reimport_autolink.py --stage 100 --pause 60 --max-stages 1     # erste Etappe
Rückweg: Sicherung der Wikitexte (dumpBackup) und geprueft.json vor dem Lauf; Dump per importDump.php zurück, geprueft.json zurückkopieren.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

SRC = Path("/opt/wikimedica-source")
SEO = "/srv/atmed/coordination/vorbereitet/wikimedica-seo-dauerauftrag"
GEPRUEFT = Path("/srv/atmed/stacks/wikimedica-core-overlay/seo/extensions/WikiMedicaSEO/data/geprueft.json")
sys.path.insert(0, str(SRC / "scripts" / "publishing"))
sys.path.insert(0, SEO)


def nolinks(fach_text, t: str) -> str:
    t = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", fach_text(t))
    return re.sub(r"\s+", " ", t).strip()


def latest_revision(container: str, title: str) -> int | None:
    q = "select page_latest from page where page_namespace=0 and page_title='" + title.replace(" ", "_").replace("'", "\\'") + "'"
    out = subprocess.run(["docker", "exec", container, "php", "maintenance/run.php", "sql", "--query", q], capture_output=True, text=True, timeout=60).stdout
    m = re.search(r"\[page_latest\] => (\d+)", out)
    return int(m.group(1)) if m else None


def write_geprueft(data: dict) -> None:
    tmp = GEPRUEFT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, GEPRUEFT)  # gleiche Verzeichnis-Einbindung, atomar


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--stage", type=int, default=100)
    ap.add_argument("--pause", type=int, default=60)
    ap.add_argument("--max-stages", type=int, default=0, help="0 = alle")
    ap.add_argument("--state", default="/var/lib/wikimedica-publisher/reimport-autolink-state.json")
    ap.add_argument("--container", default="wikimedica_app")
    ap.add_argument("--list-out", help="Plan als JSON ablegen")
    a = ap.parse_args()
    from fachhash_seo import fach_hash, fach_text
    import import_merged_beta_local as L
    import import_merged_beta as B
    L.CONTAINER = a.container
    L.upload_figures = lambda f: None  # Abbildungen sind live, nicht erneut hochladen
    if "def autolinker" not in (SRC / "scripts/publishing/import_merged_beta.py").read_text(encoding="utf-8"):
        print("Importer-Klon enthält die Querverweise (PR #932) noch nicht", file=sys.stderr)
        return 2
    rev = L.git_revision()
    g = json.loads(GEPRUEFT.read_text(encoding="utf-8"))
    done = set(json.loads(Path(a.state).read_text()) if Path(a.state).exists() else [])
    plan, skipped, new = [], [], 0
    for folder in sorted(B.ALLOWED_FOLDERS):
        for f in sorted((B.ROOT / "content" / folder).rglob("*.md")):
            if f.name.lower() == "readme.md" or "templates" in f.parts:
                continue
            try:
                title, target, _ = L.build_page(f, rev)
            except Exception:
                continue
            live = L.read_page(title) if not a.dry_run else None
            if a.dry_run:  # Trockenlauf liest den Live-Text einzeln (langsam, aber ohne Schreiben)
                live = L.read_page(title)
            if live is None:
                new += 1
                continue
            if nolinks(fach_text, live) != nolinks(fach_text, target):
                skipped.append(title)
                continue
            ok = title in g and g[title].get("fach_hash") == fach_hash(live)
            plan.append({"title": title, "file": str(f), "nachfuehren": ok})
    todo = [p for p in plan if p["title"] not in done]
    print(json.dumps({"plan": len(plan), "nachzufuehren": sum(p["nachfuehren"] for p in plan), "uebersprungen_textabweichung": len(skipped),
                      "nicht_live": new, "noch_offen": len(todo)}, ensure_ascii=False))
    if a.list_out:
        Path(a.list_out).write_text(json.dumps({"plan": plan, "skipped": skipped}, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.dry_run:
        return 0
    stage_no = 0
    for i in range(0, len(todo), a.stage):
        chunk, errors, imported = todo[i:i + a.stage], 0, 0
        for p in chunk:
            try:
                res = L.import_article(Path(p["file"]), rev)
                if p["nachfuehren"] and res["result"] in ("updated", "unchanged"):
                    text = L.read_page(p["title"]) or ""
                    rid = latest_revision(a.container, p["title"])
                    if rid:
                        g[p["title"]] = {**g[p["title"]], "fach_hash": fach_hash(text), "revision": rid}
                imported += 1
                done.add(p["title"])
            except Exception as exc:  # noqa: BLE001
                errors += 1
                print(json.dumps({"title": p["title"], "fehler": str(exc)[:200]}, ensure_ascii=False))
        write_geprueft(g)
        Path(a.state).write_text(json.dumps(sorted(done)), encoding="utf-8")
        stage_no += 1
        print(json.dumps({"etappe": stage_no, "importiert": imported, "fehler": errors}, ensure_ascii=False), flush=True)
        if errors > max(3, len(chunk) // 20):
            print("Zu viele Fehler, Abbruch", file=sys.stderr)
            return 1
        if a.max_stages and stage_no >= a.max_stages:
            break
        time.sleep(a.pause)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
