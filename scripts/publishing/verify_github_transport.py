#!/usr/bin/env python3
"""Verify GitHub -> MediaWiki *write and read-back* with a non-medical test page.

Uses the same authenticated WikiClient as the production article importer, but
NEVER imports clinical content. The one allowed target is a dedicated project
namespace page. Run on the WikiMedica server after pulling this repository.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))

from import_to_mediawiki import WikiClient, WikiError, GateError, wiki_credentials  # noqa: E402

PAGE = "Wikimedica:GitHub-Transporttest"
MARKER = "<!-- wikimedica-github-transport-test -->"


def git_head() -> str:
    run = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--verify", "HEAD"],
        capture_output=True, text=True, check=True,
    )
    return run.stdout.strip()


def render_text(commit: str, payload: str) -> str:
    return (
        MARKER + "\n"
        "= GitHub–MediaWiki: technischer Transporttest =\n\n"
        "'''Dies ist kein medizinischer Fachartikel und keine redaktionelle Freigabe.'''\n\n"
        "Der folgende Text stammt aus einer Datei im GitHub-Repository und wurde "
        "durch den serverseitigen Pull-Prozess übertragen.\n\n"
        "<pre>" + payload.replace("<", "&lt;").replace(">", "&gt;") + "</pre>\n\n"
        f"Git-Commit: <code>{commit}</code>\n"
        "[[Category:Wikimedica-Systemtests]]\n"
    )


def run(env: str, dry_run: bool = False) -> int:
    source = ROOT / "data" / "publishing" / "transport-test-message.txt"
    payload = source.read_text(encoding="utf-8").strip()
    commit = git_head()
    target = render_text(commit, payload)
    if dry_run:
        print(json.dumps({"status": "dry-run", "page": PAGE, "commit": commit,
                          "bytes": len(target)}, ensure_ascii=False))
        return 0

    try:
        api, user, password = wiki_credentials(env)
        client = WikiClient(api, user, password)
        client.login()
        before = client.get_page(PAGE)
        if before and not before["text"].startswith(MARKER):
            raise GateError("The transport-test page already exists but is not managed "
                            "by the transport probe; refusing to overwrite it.")
        if before and before["text"] == target:
            state = "unchanged"
        else:
            client.edit(
                PAGE, target, "WikiMedica: GitHub -> MediaWiki transport probe",
                baserevid=before["revid"] if before else None,
                createonly=before is None,
            )
            state = "updated" if before else "created"

        after = client.get_page(PAGE)
        if not after or after["text"] != target:
            raise WikiError("Read-back verification failed: content does not match GitHub payload")
        print(json.dumps({
            "status": "verified", "action": state, "page": PAGE,
            "commit": commit, "revision_id": after["revid"], "api_url": api,
        }, ensure_ascii=False))
        return 0
    except (GateError, WikiError, OSError, KeyError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"status": "failed", "page": PAGE,
                          "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--env", required=True, choices=("staging", "production"))
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    return run(args.env, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
