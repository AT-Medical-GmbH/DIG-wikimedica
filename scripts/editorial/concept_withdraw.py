#!/usr/bin/env python3
"""Rückzug von Begriffsartikeln (#728): zurück auf Entwurf, Wiki-Seite entfernen.

Je Artikel (``--slug``), je Art (``--kind``) oder alle (``--alle``):
1. Datei im Arbeitsklon von content/articles/begriffe/ nach content/drafts/begriffe/ verschieben (der Importer liest
   „drafts“ nicht; nichts wird gelöscht, die Datei bleibt im Verlauf),
2. Wiki-Seite per MediaWiki-Wartungsskript ``deleteBatch`` entfernen (wiederherstellbar über Spezial:Wiederherstellen),
3. optional Warteschlangen-Eintrag auf ``review`` (``--queue-db``).

Sicherheitsgitter: ``--container`` ist Pflicht; Produktion (wikimedica_app) nur mit zusätzlichem ``--live``.
Ohne ``--ausfuehren`` nur Probelauf (zeigt, was passieren würde).
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import concept_review as cr  # noqa: E402

ROOT = cr.ROOT


def title_of(fm: str) -> str:
    return (cr.field(fm, "title") or "").strip()


def wiki_delete(container: str, titles: list[str], reason: str) -> subprocess.CompletedProcess:
    listing = "\n".join(titles) + "\n"
    return subprocess.run(["docker", "exec", "-u", "www-data", "-i", container, "php", "maintenance/run.php", "deleteBatch",
                           "-u", "Andreas.Tremml", "-r", reason, "/dev/stdin"], input=listing.encode(), capture_output=True, timeout=300)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slug", action="append", default=[])
    ap.add_argument("--kind")
    ap.add_argument("--alle", action="store_true")
    ap.add_argument("--container", required=True)
    ap.add_argument("--live", action="store_true", help="erforderlich, wenn --container wikimedica_app (Produktion) ist")
    ap.add_argument("--ausfuehren", action="store_true")
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--queue-db", help="pipeline.sqlite: Einträge auf 'review' (Entwurf) setzen")
    ap.add_argument("--grund", default="Rückzug Begriffsartikel (#728)")
    a = ap.parse_args()
    if a.container == "wikimedica_app" and not a.live:
        print("Produktion nur mit --live", file=sys.stderr)
        return 2
    if not (a.slug or a.kind or a.alle):
        print("--slug, --kind oder --alle angeben", file=sys.stderr)
        return 2
    root = Path(a.root)
    sel = []
    for f, m in cr.concept_files(root):
        if a.alle or f.stem in a.slug or (a.kind and cr.field(m.group(2), "concept_kind") == a.kind):
            if "drafts" not in f.parts:
                sel.append((f, title_of(m.group(2))))
    print(f"{len(sel)} Artikel ausgewählt ({'AUSFÜHRUNG' if a.ausfuehren else 'Probelauf'})")
    for f, t in sel:
        print(f"  {f.relative_to(root)}  ->  drafts/begriffe/{f.name}   Seite: {t}")
    if not a.ausfuehren or not sel:
        return 0
    dest = root / "content" / "drafts" / "begriffe"
    dest.mkdir(parents=True, exist_ok=True)
    r = wiki_delete(a.container, [t for _, t in sel], a.grund)
    print(r.stdout.decode(errors="replace")[-600:])
    if r.returncode != 0:
        print(r.stderr.decode(errors="replace")[-400:], file=sys.stderr)
        return 1
    for f, _ in sel:
        f.rename(dest / f.name)
    if a.queue_db:
        db = sqlite3.connect(a.queue_db)
        for f, _ in sel:
            db.execute("UPDATE items SET status='review', error='Rückzug (Entwurf)' WHERE slug=?", (f.stem,))
        db.commit()
    print("Fertig. Verschobene Dateien noch nicht committet (PR nötig).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
