#!/usr/bin/env python3
"""GitHub -> MediaWiki: import one or more merged medical articles as marked BETA.

This owner-approved pilot treats a merge to main as the editorial release decision.
It does not forge or change clinical review metadata and does not touch the normal
release-tag importer. Authentication is a MediaWiki BotPassword (environment only).
Every write is verified by reading the saved page from the Action API.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "publishing"))
import md2wiki
from import_to_mediawiki import WikiClient, WikiError, GateError, wiki_credentials

FM_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n", re.S)
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKER_RE = re.compile(r'^<!-- wikimedica-beta-managed slug="([a-z0-9-]+)" sha256="([0-9a-f]{64})" -->')
ALLOWED_FOLDERS = {"specialties", "articles", "patient-info", "pharmaka", "therapies", "published"}
ALLOWED_TYPES = {"professional", "patient", "pharmaka", "therapy"}
BLOCKED_STATUSES = {"archived", "retracted"}
BETA_HEADER = (
    '<div class="mw-message-box mw-message-box-warning">'
    "'''WIKIMEDICA BETA – vorläufiger medizinischer Artikel.''' "
    "Dieser Inhalt wird im Rahmen der fortlaufenden WikiMedica-BETA veröffentlicht. "
    "Dieser Text ersetzt keine individuelle Diagnostik oder Behandlung. "
    "Bei einem medizinischen Notfall die 112 wählen."
    "</div>"
)
PUBLIC_BETA_INTERNAL_SECTIONS = {
    "Hinweise und Haftungsausschluss",
    "Review-Historie",
    "Änderungsverlauf",
    "Redaktionelle Prüfaufträge vor fachlicher Freigabe",
    "Offene redaktionelle Qualitätsprüfung",
}


def public_beta_body(body: str) -> str:
    """Hide duplicate internal drafting notices from the public BETA rendering.

    The source file remains unchanged and auditable in Git.  The mandatory
    site-wide BETA notice above the article remains the sole public preliminary
    status notice, while editorial/review history stays in repository metadata.
    """
    body = re.sub(
        r"(?m)^>[ \t]+\*\*(?:Redaktioneller Status|Medizinisch nicht freigegebener KI-Entwurf|"
        r"KI-gestützter Erstentwurf).*?(?:\n|\Z)",
        "",
        body,
    )
    pattern = re.compile(r"(?ms)^##[ \t]+(?P<title>[^\n#]+?)[ \t]*#*[ \t]*\n.*?(?=^##[ \t]+|\Z)")

    def keep_or_remove(match: re.Match) -> str:
        return "" if match.group("title").strip() in PUBLIC_BETA_INTERNAL_SECTIONS else match.group(0)

    return pattern.sub(keep_or_remove, body)


def git_revision() -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()


def eligible_path(path: Path) -> bool:
    try:
        relative = path.resolve().relative_to((ROOT / "content").resolve())
    except ValueError:
        return False
    return (
        len(relative.parts) >= 2
        and relative.parts[0] in ALLOWED_FOLDERS
        and path.suffix == ".md"
        and path.name.lower() != "readme.md"
        and "templates" not in relative.parts
    )


def build_page(path: Path, revision: str) -> tuple[str, str, str]:
    if not eligible_path(path):
        raise ValueError(f"not an allowed medical-article path: {path}")
    m = FM_RE.match(path.read_text(encoding="utf-8"))
    if not m:
        raise ValueError("missing YAML frontmatter")
    fm = yaml.safe_load(m.group(1))
    if not isinstance(fm, dict):
        raise ValueError("invalid YAML metadata")
    title = str(fm.get("title") or "").strip()
    slug = path.stem
    if not SLUG_RE.fullmatch(slug) or fm.get("slug") != slug:
        raise ValueError("invalid or mismatched article slug")
    if not title or any(c in title for c in "#<>[]|{}:"):
        raise ValueError("unsafe or empty MediaWiki page title")
    if fm.get("article_type") not in ALLOWED_TYPES:
        raise ValueError("unsupported article type")
    if fm.get("safety_hold") is True:
        raise ValueError("SAFETY HOLD: must not publish")
    if fm.get("status") in BLOCKED_STATUSES:
        raise ValueError("withdrawal/archive requires the supervised production withdrawal workflow")
    if len(m.group(0)) >= len(path.read_text(encoding="utf-8")):
        raise ValueError("empty body")
    body = path.read_text(encoding="utf-8")[m.end():]
    converted = md2wiki.convert_medical_article(public_beta_body(body), md2wiki.ConvertContext(title=title))
    note = (
        "\n\n----\n"
        "'''BETA-Hinweis:''' Veröffentlichung aus dem gemergten WikiMedica-GitHub-Hauptbranch. "
        f"Versionsstand: {md2wiki.esc(str(fm.get('version', '0.1.0')))}; "
        f"Stand: {md2wiki.esc(str(fm.get('updated', '')))}; "
        f"Commit: <code>{revision}</code>.\n"
    )
    content = BETA_HEADER + "\n\n" + converted.rstrip() + note
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    marker = f'<!-- wikimedica-beta-managed slug="{slug}" sha256="{digest}" -->'
    return title, marker + "\n" + content, digest


def import_file(client: WikiClient, file: Path, revision: str) -> dict:
    title, target, digest = build_page(file, revision)
    current = client.get_page(title)
    if current:
        m = MARKER_RE.match(current["text"])
        if not m or m.group(1) != file.stem:
            raise ValueError(f"MediaWiki page '{title}' already exists but is not beta-managed by this slug")
        existing_body = current["text"].split("\n", 1)[1] if "\n" in current["text"] else ""
        if hashlib.sha256(existing_body.encode("utf-8")).hexdigest() != m.group(2):
            raise ValueError(f"MediaWiki page '{title}' was edited outside the importer; refusing overwrite")
        if current["text"] == target:
            return {"title": title, "result": "unchanged", "revid": current["revid"]}
    client.edit(
        title, target, "WikiMedica BETA: sync from merged GitHub main",
        baserevid=current["revid"] if current else None, createonly=current is None,
    )
    readback = client.get_page(title)
    if not readback or readback["text"] != target:
        raise ValueError(f"read-back content mismatch for '{title}'")
    return {"title": title, "result": "updated" if current else "created", "revid": readback["revid"]}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--env", choices=["staging", "production"], default="production")
    p.add_argument("--file", action="append", default=[], help="content-relative filename (repeat)")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    if not args.file:
        print(json.dumps({"result": "no-changes"}))
        return 0
    revision = git_revision()
    files = [(ROOT / raw).resolve() for raw in args.file]
    if args.dry_run:
        for file in files:
            title, text, _ = build_page(file, revision)
            print(json.dumps({"title": title, "result": "dry-run", "wikitext_bytes": len(text)}, ensure_ascii=False))
        return 0
    api, user, password = wiki_credentials(args.env)
    client = WikiClient(api, user, password)
    client.login()
    failed = False
    for file in files:
        try:
            result = import_file(client, file, revision)
            print(json.dumps(result, ensure_ascii=False), flush=True)
        except Exception as exc:
            failed = True
            print(json.dumps({"path": str(file), "result": "failed", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
