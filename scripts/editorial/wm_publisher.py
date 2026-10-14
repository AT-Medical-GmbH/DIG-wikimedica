#!/usr/bin/env python3
"""Veröffentlichung der Pipeline-Ergebnisse als Sammel-PR (stündlich, Root-Dienst).

Entscheidung Andreas 14.10.2026: Artikel dieses Stroms werden ohne Hinweis „KI-Entwurf“ veröffentlicht.
Voraussetzung ist die bestandene Faktenprüfung in wm_pipeline.py; Durchgefallenes liegt in der Prüfliste
(docs/editorial/ki-pruefliste.md) und wird NICHT veröffentlicht.

Ablauf: eigenes Repo-Klon aktualisieren -> fertige Artikel einordnen -> Handelsnamen-Verweisseiten erzeugen ->
validate-metadata + Renderprobe -> Branch/Commit/PR -> Merge nach main -> wikimedica-beta-sync.service starten
(der vorgesehene Weg, wie bei den übrigen Artikeln) -> Ergebnis aus dem Journal der Synchronisation prüfen.
Der Importer-Klon /opt/wikimedica-source wird NICHT angefasst.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import wm_catalog  # noqa: E402
from wm_common import DEFAULT_STATE_DIR, Queue, log, slugify  # noqa: E402

REPO_URL = "https://github.com/AT-Medical-GmbH/DIG-wikimedica.git"
DIR_OVERRIDE = {"Orthopädie/Unfallchirurgie": "orthopaedie", "Gynäkologie/Geburtshilfe": "gynaekologie",
                "Prävention/Public Health": "praevention-public-health"}
GIT_CRED = ["-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential"]


def sh(cmd: list[str], cwd: Path | None = None, check: bool = True, timeout: int = 900) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:4])}… rc={r.returncode}: {(r.stderr or r.stdout)[-500:]}")
    return r


def prepare_repo(work: Path) -> Path:
    repo = work / "repo"
    if not (repo / ".git").exists():
        work.mkdir(parents=True, exist_ok=True)
        sh(["git", "clone", "-q", REPO_URL, str(repo)])
        sh(["git", "config", "user.name", "WikiMedica-Redaktion"], repo)
        sh(["git", "config", "user.email", "redaktion@at-medical.de"], repo)
    sh(["git", "fetch", "-q", "--prune", "origin", "main"], repo)
    sh(["git", "checkout", "-q", "-B", "main", "origin/main"], repo)
    sh(["git", "clean", "-fdq"], repo)
    return repo


def specialty_dir(spec: str) -> str:
    return DIR_OVERRIDE.get(spec) or slugify(spec.replace("/", " "))


def refresh_known(repo: Path, state: Path) -> dict:
    ex = wm_catalog.scan_existing(repo)
    data = {"slugs": sorted(ex["slugs"]), "titles": sorted(ex["titles"])}
    tmp = state / "known-articles.json.tmp"
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    tmp.chmod(0o664)
    tmp.replace(state / "known-articles.json")
    return ex


TRADE_TEMPLATE = '''---
title: {title}
slug: {slug}
specialty: "Pharmakologie"
secondary_specialties: []
article_type: "pharmaka"
content_kind: "article"
status: "draft"
version: "0.1.0"
change_summary: "Handelsnamen-Verweisseite auf den Wirkstoffartikel; keine eigenen medizinischen Aussagen."
authors: [{{name: "WikiMedica-Redaktion"}}]
reviewers: []
created: "{today}"
updated: "{today}"
risk_level: "high"
target_audience: ["physicians", "pharmacists"]
sex_gender_relevance: "not_assessed"
sex_gender_notes: ""
safety_hold: false
language: "de"
language_level: "professional"
active_substances: [{target_title}]
atc_codes: ["{atc}"]
icd10: []
ops: []
pubmed_ids: []
guidelines: []
references: [{{citation: {citation}, url: "https://www.ema.europa.eu/en/medicines"}}]
source_notes: "Handelsname aus der EMA-Arzneimitteldatenbank (zentral zugelassene Arzneimittel, Wiederverwendung mit Quellenangabe); Zuordnung zum Wirkstoff über den ATC-Code (ATC-GM 2026, BfArM). Keine medizinischen Aussagen."
ai_assisted: false
ai_assistance_description: ""
wikimedica_credit: true
corrections: []
---

# {plain_title}

**{plain_title}** ist ein Handelsname eines in der Europäischen Union zentral zugelassenen Arzneimittels.[1] Der enthaltene Wirkstoff ist [{target_plain}]({target_slug}.md). Angaben zu Wirkung, Anwendung und Sicherheit stehen im Wirkstoffartikel.

## Literatur

1. {citation_plain}
'''


def make_trade_page(it, extra: dict) -> str:
    cit = f"Europäische Arzneimittel-Agentur (EMA): Arzneimitteldatenbank (Medicines), Eintrag {it['title']}, Produktnummer {extra.get('code') or extra.get('atc')}. Abruf 14.10.2026."
    return TRADE_TEMPLATE.format(
        title=json.dumps(it["title"], ensure_ascii=False), slug=json.dumps(it["slug"]), today=date.today().isoformat(),
        target_title=json.dumps(extra["target_title"], ensure_ascii=False), atc=extra["atc"],
        citation=json.dumps(cit, ensure_ascii=False), plain_title=it["title"], target_plain=extra["target_title"],
        target_slug=extra["target_slug"], citation_plain=cit)


def render_check(repo: Path, files: list[Path]) -> dict[str, str]:
    """Probelauf des BETA-Importers (ohne MediaWiki) für jede neue Datei. Gibt Fehler je Pfad zurück."""
    code = (
        "import sys, json\nfrom pathlib import Path\n"
        "sys.path.insert(0,'scripts/publishing')\nimport import_merged_beta as b\n"
        "errs={}\n"
        "for f in sys.argv[1:]:\n"
        "    try:\n        b.build_page(Path(f),'0'*40)\n"
        "    except Exception as e:\n        errs[f]=str(e)\n"
        "print(json.dumps(errs))\n")
    r = sh([sys.executable, "-I", "-c", code] + [str(f) for f in files], repo, check=False)
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        raise RuntimeError(f"Renderprobe fehlgeschlagen: {r.stderr[-300:]}")


def validate_files(repo: Path, files: list[Path]) -> dict[str, str]:
    errs = {}
    for f in files:
        r = sh([sys.executable, str(repo / "scripts/validation/validate-metadata.py"), str(f)], repo, check=False)
        if r.returncode != 0:
            errs[str(f)] = (r.stdout + r.stderr)[-300:]
    return errs


def write_pruefliste(repo: Path, q: Queue) -> None:
    rows = q.db.execute("SELECT id,title,slug,kind,status,error FROM items WHERE status IN ('review','failed') ORDER BY id").fetchall()
    c = q.counts()
    lines = ["# Prüfliste: nicht veröffentlichte KI-Entwürfe", "",
             "Automatisch erzeugt von `scripts/editorial/wm_publisher.py`. Einträge haben die maschinelle Faktenprüfung oder die formale Prüfung "
             "nicht bestanden und werden **nicht** veröffentlicht. Sie warten auf redaktionelle Entscheidung.", "",
             f"Stand: {datetime.now().strftime('%d.%m.%Y %H:%M')}. Warteschlange: " + ", ".join(f"{k} {v}" for k, v in sorted(c.items())) + ".", "",
             "| ID | Thema | Art | Grund |", "|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['id']} | {r['title'].replace('|', '/')} | {r['kind']} | {(r['error'] or '').replace('|', '/')[:200]} |")
    path = repo / "docs/editorial/ki-pruefliste.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def sync_and_verify(slugs_titles: dict[str, str]) -> set[str]:
    """Startet die vorgesehene Synchronisation und liest das Ergebnis aus dem Journal (Titel -> verifiziert)."""
    since = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    r = sh(["systemctl", "start", "wikimedica-beta-sync.service"], check=False, timeout=1900)
    log(f"Synchronisation rc={r.returncode} {r.stderr[-200:]}")
    j = sh(["journalctl", "-u", "wikimedica-beta-sync.service", "--no-pager", "--since", since, "-o", "cat"], check=False)
    ok = set()
    for line in j.stdout.splitlines():
        m = re.search(r"\{.*\"article\".*\}", line)
        if m:
            try:
                d = json.loads(m.group(0))
            except ValueError:
                continue
            if d.get("verified"):
                ok.add(d["article"])
    return ok


def run(args) -> int:
    state, work = Path(args.state_dir), Path(args.workdir)
    work.mkdir(parents=True, exist_ok=True)
    lock = open(work / "publisher.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        log("Veröffentlichung läuft bereits")
        return 0
    q = Queue(state)
    repo = prepare_repo(work)
    existing = refresh_known(repo, state)
    batch_id = datetime.now().strftime("%Y%m%d-%H%M")

    # 0. früher gemergte, noch nicht verifizierte Einträge erneut synchronisieren
    pending_merged = q.db.execute("SELECT id,title FROM items WHERE status='merged'").fetchall()

    # 1. fertige Artikel
    new_files: list[Path] = []
    meta: dict[str, dict] = {}
    for it in q.db.execute("SELECT * FROM items WHERE status='ready' ORDER BY priority DESC LIMIT ?", (args.max_batch,)).fetchall():
        src = Path(it["draft_path"] or "")
        if not src.exists():
            q.set_status(it["id"], "failed", "Entwurfsdatei fehlt")
            continue
        if it["slug"] in existing["slugs"]:
            q.set_status(it["id"], "duplicate", "Slug im Repo bereits vorhanden")
            continue
        sub = Path("content/pharmaka") if it["kind"] == "drug" else Path("content/specialties") / specialty_dir(it["specialty"] or "")
        dest = repo / sub / f"{it['slug']}.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        new_files.append(dest)
        meta[str(dest)] = {"id": it["id"], "title": it["title"], "src": src}

    # 2. Handelsnamen-Verweisseiten (nur wenn der Wirkstoffartikel im Repo existiert)
    ntrade = 0
    for it in q.db.execute("SELECT * FROM items WHERE kind='trade' AND status='planned' ORDER BY priority DESC, id").fetchall():
        if ntrade >= args.max_trade:
            break
        extra = json.loads(it["extra"] or "{}")
        if extra.get("target_slug") not in existing["slugs"] and not (repo / "content/pharmaka" / f"{extra.get('target_slug')}.md").exists():
            continue
        if it["slug"] in existing["slugs"]:
            q.set_status(it["id"], "duplicate", "Slug im Repo bereits vorhanden")
            continue
        dest = repo / "content/pharmaka" / f"{it['slug']}.md"
        dest.write_text(make_trade_page(it, extra), encoding="utf-8")
        new_files.append(dest)
        meta[str(dest)] = {"id": it["id"], "title": it["title"], "src": None}
        ntrade += 1

    # 3. Prüfungen
    bad = {**validate_files(repo, new_files)}
    if new_files:
        bad.update(render_check(repo, [f for f in new_files if str(f) not in bad]))
    for path, err in bad.items():
        m = meta.get(path)
        if m:
            q.set_status(m["id"], "review", f"Veröffentlichungsprüfung: {err[:250]}")
        Path(path).unlink(missing_ok=True)
        new_files = [f for f in new_files if str(f) != path]
        log(f"Verworfen: {path}: {err[:120]}")

    write_pruefliste(repo, q)
    sh(["git", "add", "-A"], repo)
    changed = sh(["git", "status", "--porcelain"], repo).stdout.strip()
    if not new_files and not changed:
        log("Nichts zu veröffentlichen")
        if pending_merged and not args.no_sync:
            sync_and_verify({})
        return 0
    if args.dry_run:
        log(f"Trockenlauf: {len(new_files)} Dateien würden veröffentlicht")
        return 0

    n = len(new_files)
    branch = f"content/ki-batch-{batch_id}"
    sh(["git", "checkout", "-q", "-b", branch], repo)
    titles = sorted(m["title"] for m in meta.values() if m)
    msg = (f"content: KI-Artikelstrom {batch_id} ({n} Artikel)\n\n" +
           "Quellenbasierte Entwürfe mit maschineller Faktenprüfung gegen PubMed-Quellen (Pipeline scripts/editorial/wm_pipeline.py).\n"
           "Veröffentlichung ohne Hinweis nach Entscheidung von Andreas Tremml (14.10.2026).\n\n" + "\n".join(f"- {t}" for t in titles[:80]))
    sh(["git", "commit", "-q", "-m", msg + "\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_016xRoJLoBh8p96XD8RQ4Ygq"], repo)
    sh(["git"] + GIT_CRED + ["push", "-q", "-u", "origin", branch], repo)
    body = (f"Automatischer Sammel-PR des KI-Artikelstroms ({n} Dateien).\n\nValidierung: validate-metadata und BETA-Renderprobe je Datei bestanden.\n"
            "Nicht bestandene Entwürfe stehen in docs/editorial/ki-pruefliste.md.\n\n"
            "🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nhttps://claude.ai/code/session_016xRoJLoBh8p96XD8RQ4Ygq")
    pr = sh(["gh", "pr", "create", "--title", f"content: KI-Artikelstrom {batch_id} ({n} Artikel)", "--body", body, "--base", "main", "--head", branch], repo).stdout.strip()
    sh(["gh", "pr", "merge", pr, "--merge", "--delete-branch"], repo)
    prn = pr.rsplit("/", 1)[-1]
    log(f"PR {pr} gemergt")
    for m in meta.values():
        if m:
            q.set_status(m["id"], "merged", None, pr=prn)
            q.event(m["id"], "merged", pr)
    sh(["git", "checkout", "-q", "main"], repo, check=False)

    # 4. Live-Gang über den vorgesehenen Weg
    if not args.no_sync:
        ok_titles = sync_and_verify({})
        rows = q.db.execute("SELECT id,title FROM items WHERE status='merged'").fetchall()
        done = 0
        for r in rows:
            if r["title"] in ok_titles:
                q.set_status(r["id"], "published", None)
                q.event(r["id"], "published", prn)
                done += 1
        log(f"Live verifiziert: {done} von {len(rows)} gemergten Einträgen")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    ap.add_argument("--workdir", default="/var/lib/wikimedica-publisher")
    ap.add_argument("--max-batch", type=int, default=60)
    ap.add_argument("--max-trade", type=int, default=40)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-sync", action="store_true")
    return run(ap.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
