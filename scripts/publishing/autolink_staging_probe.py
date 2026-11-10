#!/usr/bin/env python3
"""Probelauf der automatischen Querverweise im STAGING-Wiki (nie Produktion).

Schreibt die mit Querverweisen und Rückverweisen neu gebauten Seiten über die MediaWiki-Wartungsskripte in den
Staging-Container, sichert vorher den alten Seitentext (Rückweg) und schreibt Vorher-/Nachher-Belege.

    python3 scripts/publishing/autolink_staging_probe.py --out DIR --slug furosemid --slug ...   # schreibt
    python3 scripts/publishing/autolink_staging_probe.py --out DIR --rollback                    # stellt Vorher-Stand wieder her
    python3 scripts/publishing/autolink_staging_probe.py --out DIR --slug … --dry-run             # nur Belege, kein Schreiben
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "publishing"))
import autolink
import import_merged_beta as imp

CONTAINER = "wikimedica_app_staging"
EDITOR = "Andreas.Tremml"
LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:\|[^\]]*)?\]\]")


def mw(*args: str, text: str | None = None) -> subprocess.CompletedProcess:
    cmd = ["docker", "exec", "-u", "www-data"] + (["-i"] if text is not None else []) + [CONTAINER, "php", "maintenance/run.php", *args]
    return subprocess.run(cmd, input=None if text is None else text.encode(), capture_output=True, timeout=120)


def get_text(title: str) -> str | None:
    r = mw("getText", title)
    return r.stdout.decode() if r.returncode == 0 and r.stdout else None


def staging_targets() -> tuple[set[str], dict[str, str]]:
    dump = subprocess.run(["docker", "exec", CONTAINER, "php", "maintenance/run.php", "dumpBackup", "--current", "--quiet"],
                          capture_output=True, check=True, timeout=300).stdout
    titles, redirects = autolink.read_dump(dump)
    return set(titles), redirects


def find_file(slug: str) -> Path:
    hits = [p for p in (ROOT / "content").rglob(f"{slug}.md") if imp.eligible_path(p)]
    if len(hits) != 1:
        raise SystemExit(f"{slug}: {len(hits)} Treffer im Repo")
    return hits[0]


def norm(t: str) -> str:
    return t.replace("\r\n", "\n").rstrip("\n") + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--slug", action="append", default=[])
    ap.add_argument("--rollback", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if CONTAINER == "wikimedica_app":
        raise SystemExit("nur Staging")
    out = Path(args.out)
    (out / "vorher").mkdir(parents=True, exist_ok=True)
    (out / "nachher").mkdir(exist_ok=True)

    if args.rollback:
        index = json.loads((out / "index.json").read_text(encoding="utf-8"))
        for item in index:
            before = (out / "vorher" / item["file"]).read_text(encoding="utf-8")
            r = mw("edit", "--user", EDITOR, "--summary", "Probelauf Querverweise: Rückweg", "--nocreate", item["title"], text=before)
            ok = norm(get_text(item["title"]) or "") == norm(before)
            print(json.dumps({"title": item["title"], "rollback": "ok" if r.returncode == 0 and ok else "FEHLER"}, ensure_ascii=False))
        return 0

    titles, redirects = staging_targets()
    # Ziele nur aus dem Staging-Wiki, damit im Probelauf keine roten Links entstehen
    imp._LINKER = autolink.Linker(autolink.build_targets(titles, redirects))
    imp._REVERSE_RELATED = None
    revision = imp.git_revision()
    index, total = [], 0
    for slug in args.slug:
        path = find_file(slug)
        title, target, _ = imp.build_page(path, revision)
        before = get_text(title)
        if before is None:
            print(json.dumps({"slug": slug, "result": "nicht im Staging"}, ensure_ascii=False))
            continue
        # Kontrolle: derselbe Artikel ohne Querverweise und ohne Rückverweise, um die reine Wirkung der Regel zu belegen
        saved_env, saved_rev = imp.os.environ.get("WIKIMEDICA_AUTOLINK"), imp.reverse_related
        imp.os.environ["WIKIMEDICA_AUTOLINK"], imp.reverse_related = "0", lambda: {}
        try:
            _, control, _ = imp.build_page(path, revision)
        finally:
            imp.reverse_related = saved_rev
            if saved_env is None:
                imp.os.environ.pop("WIKIMEDICA_AUTOLINK", None)
            else:
                imp.os.environ["WIKIMEDICA_AUTOLINK"] = saved_env
        wirkung = [l for l in difflib.unified_diff(control.splitlines(), target.splitlines(), "ohne_regel", "mit_regel", lineterm="", n=0)]
        (out / "nachher" / (slug + ".wirkung.diff")).write_text("\n".join(wirkung) + "\n", encoding="utf-8")
        fname = slug + ".wiki"
        (out / "vorher" / fname).write_text(before, encoding="utf-8")
        (out / "nachher" / fname).write_text(target, encoding="utf-8")
        # Rote Links prüfen: Ziele müssen im Staging existieren
        targets_new = {m.group(1).strip() for m in LINK_RE.finditer(target)} - {m.group(1).strip() for m in LINK_RE.finditer(before)}
        red = sorted(t for t in targets_new if t not in titles and t not in redirects and not t.startswith(("Kategorie:", "Datei:")))
        diff = list(difflib.unified_diff(before.splitlines(), target.splitlines(), "vorher", "nachher", lineterm="", n=0))
        (out / "nachher" / (slug + ".diff")).write_text("\n".join(diff) + "\n", encoding="utf-8")
        item = {"slug": slug, "title": title, "file": fname, "neue_links": len(targets_new), "rote_links": red}
        if not args.dry_run:
            r = mw("edit", "--user", EDITOR, "--summary", "Probelauf automatische Querverweise (Staging)", "--nocreate", title, text=target)
            saved = get_text(title)
            item["geschrieben"] = r.returncode == 0 and norm(saved or "") == norm(target)
        index.append(item)
        total += len(targets_new)
        print(json.dumps(item, ensure_ascii=False))
    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"artikel": len(index), "neue_links_gesamt": total}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
