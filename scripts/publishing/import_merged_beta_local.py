#!/usr/bin/env python3
"""Import merged GitHub BETA articles directly through local MediaWiki CLI.

No public HTTP API and no BotPassword required. Intended to run ONLY on the
actual WikiMedica host with access to the production MediaWiki Docker container.
Reads back the committed wiki text through maintenance/getText after every edit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "publishing"))
from import_merged_beta import build_page, git_revision, MARKER_RE
import md2wiki

CONTAINER = "wikimedica_app"
EDITOR = "Andreas.Tremml"
MAINTENANCE = ("php", "maintenance/run.php")
TITLE_MAX = 255


def execute(script: str, *args: str, input_text: str | None = None) -> subprocess.CompletedProcess:
    command = ["docker", "exec"]
    if input_text is not None:
        command.append("-i")
    command.extend([CONTAINER, *MAINTENANCE, script, *args])
    result = subprocess.run(
        command,
        input=None if input_text is None else input_text.encode("utf-8"),
        capture_output=True,
        timeout=90,
    )
    return result


FIGURE_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")


def figure_files(path: Path) -> list[Path]:
    """Eigene Zeichnungen (media/**/*.svg), die der Artikel einbindet und die ins Wiki hochgeladen werden müssen."""
    out: list[Path] = []
    for url in FIGURE_RE.findall(path.read_text(encoding="utf-8")):
        if md2wiki.media_file_name(url):
            f = (path.parent / url).resolve()
            if f.is_file() and (ROOT / "media").resolve() in f.parents and f not in out:
                out.append(f)
    return out


def upload_figures(files: list[Path]) -> None:
    """Lädt SVG-Zeichnungen über maintenance/importImages hoch (idempotent: --skip-dupes, --overwrite bei geändertem Inhalt)."""
    if not files:
        return
    tmp = f"/tmp/wm-figs-{os.getpid()}"
    subprocess.run(["docker", "exec", CONTAINER, "mkdir", "-p", tmp], check=True, capture_output=True, timeout=30)
    try:
        for f in files:
            subprocess.run(["docker", "cp", str(f), f"{CONTAINER}:{tmp}/{f.name}"], check=True, capture_output=True, timeout=60)
        result = execute("importImages", "--extensions", "svg", "--overwrite", "--skip-dupes", "--user", EDITOR,
                         "--comment", "WikiMedica: Schemazeichnung aus GitHub main (selbst erzeugt)", tmp)
        output = decode(result.stdout) + decode(result.stderr)
        if result.returncode != 0 or "Found:" not in output:
            raise RuntimeError(f"MediaWiki importImages failed ({result.returncode}): {output[:400]}")
    finally:
        subprocess.run(["docker", "exec", CONTAINER, "rm", "-r", "--", tmp], capture_output=True, timeout=30)


def decode(blob: bytes) -> str:
    return blob.decode("utf-8", errors="replace")


def normalize(text: str) -> str:
    """Only normalize the final line break added by some MediaWiki CLI versions."""
    return text.replace("\r\n", "\n").rstrip("\n") + "\n"


def read_page(title: str) -> str | None:
    result = execute("getText", title)
    if result.returncode == 0:
        content = decode(result.stdout)
        # A truly empty page is not considered ours. The --createonly option
        # ensures a pre-existing blank page is never overwritten.
        return content or None
    output = decode(result.stdout) + " " + decode(result.stderr)
    if re.search(r"does not exist|not found|no such page|not available|missing", output, re.I):
        return None
    raise RuntimeError(f"MediaWiki getText failed ({result.returncode}): {output[:400]}")


def import_article(path: Path, revision: str) -> dict:
    title, target, _ = build_page(path, revision)
    if len(title) > TITLE_MAX:
        raise ValueError("Wiki title too long")
    previous = read_page(title)
    if previous is not None:
        marker = MARKER_RE.match(previous)
        if not marker or marker.group(1) != path.stem:
            raise ValueError("existing page is not owned by this BETA article; refusing overwrite")
        content = previous.split("\n", 1)[1] if "\n" in previous else ""
        if hashlib.sha256(normalize(content).encode("utf-8")).hexdigest() != marker.group(2):
            raise ValueError("manual page changes detected; refusing overwrite")
        if normalize(previous) == normalize(target):
            return {"article": title, "result": "unchanged", "verified": True}

    figures = figure_files(path)
    upload_figures(figures)
    options = ["--user", EDITOR, "--summary", "WikiMedica BETA: sync from merged GitHub main"]
    options.append("--nocreate" if previous is not None else "--createonly")
    response = execute("edit", *options, title, input_text=target)
    if response.returncode != 0:
        output = (decode(response.stderr) + " " + decode(response.stdout)).strip()
        raise RuntimeError(f"MediaWiki edit failed ({response.returncode}): {output[:500]}")
    saved = read_page(title)
    if saved is None or normalize(saved) != normalize(target):
        raise RuntimeError("MediaWiki read-back verification failed: saved page differs from GitHub")
    return {
        "article": title,
        "result": "updated" if previous is not None else "created",
        "verified": True,
        "wiki": "production",
        "commit": revision,
        **({"figures": [f.name for f in figures]} if figures else {}),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", action="append", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if os.geteuid() != 0:
        print("ERROR: this Docker maintenance importer requires root on the wiki server", file=sys.stderr)
        return 2
    try:
        revision = git_revision()
        items = [(ROOT / f).resolve() for f in args.file]
        if args.dry_run:
            for file in items:
                title, target, _ = build_page(file, revision)
                print(json.dumps({"result": "dry-run", "title": title, "bytes": len(target)}, ensure_ascii=False))
            return 0
        # Confirm this is the production container, never staging.
        inspected = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Running}}", CONTAINER],
            capture_output=True, text=True, timeout=20,
        )
        if inspected.returncode != 0 or inspected.stdout.strip() != "true":
            raise RuntimeError("production container wikimedica_app is not running")
        errors = 0
        for file in items:
            try:
                print(json.dumps(import_article(file, revision), ensure_ascii=False), flush=True)
            except Exception as error:
                errors += 1
                print(json.dumps({"file": str(file), "result": "failed",
                                  "reason": str(error)}, ensure_ascii=False), file=sys.stderr, flush=True)
        return 1 if errors else 0
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
