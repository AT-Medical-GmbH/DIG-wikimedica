#!/usr/bin/env python3
"""Prüfstatus der Begriffsartikel (#728): nach der Fachabnahme durch Andreas den verschärften Hinweis entfernen.

Setzt ``review_status`` im Frontmatter. Beim nächsten Import (``import_merged_beta``) entfallen dann Hinweis,
``__NOINDEX__`` und die Kategorie „Fachlich ungeprüft“. Schreibt nur Dateien im Arbeitsklon; Commit/PR/Merge folgen
wie bei jedem Inhalt (Freigabe durch Andreas).

    python3 scripts/editorial/concept_review.py --slug SLUG [--slug …]        # einzelne Artikel auf "geprueft"
    python3 scripts/editorial/concept_review.py --kind pharmakologie          # alle Artikel einer Art
    python3 scripts/editorial/concept_review.py --status ungeprueft --slug …  # zurücknehmen
    python3 scripts/editorial/concept_review.py --liste                       # Stand je Art
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FM_RE = re.compile(r"\A(---[ \t]*\r?\n)(.*?)(\r?\n---[ \t]*\r?\n)", re.S)


def concept_files(root: Path = ROOT):
    for f in sorted((root / "content").rglob("*.md")):
        if "templates" in f.parts or f.name.lower() == "readme.md":
            continue
        m = FM_RE.match(f.read_text(encoding="utf-8"))
        if m and re.search(r"(?m)^concept_kind:\s*\S", m.group(2)):
            yield f, m


def field(fm: str, key: str) -> str | None:
    m = re.search(rf'(?m)^{key}:\s*"?([^"\n]+)"?\s*$', fm)
    return m.group(1).strip() if m else None


def set_status(path: Path, status: str) -> bool:
    text = path.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    fm = m.group(2)
    new = f'review_status: "{status}"'
    fm2 = re.sub(r"(?m)^review_status:.*$", new, fm) if re.search(r"(?m)^review_status:", fm) else fm + "\n" + new
    if fm2 == fm:
        return False
    path.write_text(m.group(1) + fm2 + m.group(3) + text[m.end():], encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slug", action="append", default=[])
    ap.add_argument("--kind")
    ap.add_argument("--status", choices=("geprueft", "ungeprueft"), default="geprueft")
    ap.add_argument("--liste", action="store_true")
    ap.add_argument("--root", default=str(ROOT))
    a = ap.parse_args()
    files = list(concept_files(Path(a.root)))
    if a.liste or not (a.slug or a.kind):
        stand: dict[tuple[str, str], int] = {}
        for f, m in files:
            k = (field(m.group(2), "concept_kind") or "?", field(m.group(2), "review_status") or "ungeprueft")
            stand[k] = stand.get(k, 0) + 1
        for (kind, st), n in sorted(stand.items()):
            print(f"{kind:22} {st:11} {n}")
        return 0
    n = 0
    for f, m in files:
        if f.stem in a.slug or (a.kind and field(m.group(2), "concept_kind") == a.kind):
            if set_status(f, a.status):
                n += 1
                print(f"{f.stem}: review_status={a.status}")
    print(f"{n} Dateien geändert (noch nicht committet)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
