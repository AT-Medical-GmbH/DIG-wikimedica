#!/usr/bin/env python3
"""Persistent, conservative dispatcher for the WikiMedica editorial queue.

This program deliberately does not invoke Codex, Claude or a browser.  It is a
small, restart-safe control plane for human-approved research and publication
work.  A separately authorised research executor can be integrated later;
until then, a missing executor is a visible blocked state rather than a hidden
model call or a fabricated article.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
import tempfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pubmed_connector import PubMedConnector, PubMedError, cached_search

STATUS = {
    "planned", "researching", "sources-verified", "drafted", "validated",
    "pr-created", "beta-publication-queued", "live-beta-verified",
    "review-pending", "reviewed", "approved", "published", "blocked",
}
TERMINAL = {"published"}
STATE_VERSION = 1


def now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Ungültiges JSON-Objekt: {path}")
    return raw


class Store:
    def __init__(self, state_dir: Path, plan_path: Path):
        self.state_dir = state_dir
        self.state_path = state_dir / "state.json"
        self.lock_path = state_dir / "agent.lock"
        self.plan_path = plan_path

    def lock(self):
        self.state_dir.mkdir(mode=0o750, parents=True, exist_ok=True)
        fh = self.lock_path.open("a+", encoding="utf-8")
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            fh.close()
            raise RuntimeError("Ein anderer Editorial-Agent-Lauf hält bereits die Sperre.")
        return fh

    def default_state(self) -> dict[str, Any]:
        return {
            "schema_version": STATE_VERSION,
            "paused": False,
            "stopped": False,
            "last_successful_run": None,
            "last_attempt": None,
            "runs": 0,
            "budget": {"max_items_per_run": 1, "max_retries": 3, "max_runtime_seconds": 900},
            "items": {},
            "events": [],
        }

    def read(self) -> dict[str, Any]:
        state = load_json(self.state_path, self.default_state())
        if state.get("schema_version") != STATE_VERSION:
            raise ValueError("Nicht unterstützte State-Version")
        state.setdefault("items", {})
        state.setdefault("events", [])
        state.setdefault("budget", self.default_state()["budget"])
        return state

    def write(self, state: dict[str, Any]) -> None:
        state["events"] = state.get("events", [])[-200:]
        atomic_write(self.state_path, state)

    def plan(self) -> list[dict[str, Any]]:
        data = load_json(self.plan_path, {})
        articles = data.get("articles")
        if not isinstance(articles, list):
            raise ValueError(f"Plan enthält keine Artikelliste: {self.plan_path}")
        seen: set[str] = set()
        for item in articles:
            if not isinstance(item, dict) or not item.get("article_id"):
                raise ValueError("Plan enthält einen Artikel ohne article_id")
            if item["article_id"] in seen:
                raise ValueError(f"Doppelte article_id: {item['article_id']}")
            seen.add(item["article_id"])
        return articles


def event(state: dict[str, Any], kind: str, message: str, article_id: str | None = None) -> None:
    state["events"].append({"at": now(), "kind": kind, "message": message, "article_id": article_id})


def ensure_items(state: dict[str, Any], plan: list[dict[str, Any]]) -> None:
    for article in plan:
        article_id = article["article_id"]
        record = state["items"].setdefault(article_id, {
            "article_id": article_id,
            "title": article.get("title"),
            "slug": article.get("slug"),
            "kind": article.get("kind"),
            "risk": article.get("risk", "medium"),
            "status": article.get("status", "planned"),
            "retries": 0,
            "last_successful_step": None,
            "error": None,
            "source_commit": None,
            "branch": None,
            "pr": None,
            "mediawiki_revision": None,
            "source_snapshot": None,
            "updated_at": now(),
        })
        if record["status"] not in STATUS:
            raise ValueError(f"Ungültiger Status in State: {article_id}")


def health(state: dict[str, Any], plan: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    problems: list[str] = []
    if state.get("stopped"):
        problems.append("Agent wurde gestoppt")
    if state.get("paused"):
        problems.append("Agent ist pausiert")
    planned_ids = {x["article_id"] for x in plan}
    extra = set(state["items"]) - planned_ids
    if extra:
        problems.append("State enthält nicht mehr im Plan vorhandene Artikel: " + ", ".join(sorted(extra)))
    for item in state["items"].values():
        if item.get("status") not in STATUS:
            problems.append(f"Ungültiger Status: {item.get('article_id')}")
    return not problems, problems


def command_run(store: Store, state: dict[str, Any], plan: list[dict[str, Any]], dry_run: bool, contact_email: str) -> int:
    if state.get("stopped") or state.get("paused"):
        print("Kein Lauf: Agent ist gestoppt oder pausiert.")
        return 0
    ready = [state["items"][x["article_id"]] for x in plan if state["items"][x["article_id"]]["status"] == "planned"]
    limit = int(state["budget"].get("max_items_per_run", 1))
    selected = ready[:max(0, limit)]
    if dry_run:
        print(json.dumps({"would_consider": [x["article_id"] for x in selected], "executor": "disabled"}, ensure_ascii=False))
        return 0
    state["last_attempt"] = now()
    state["runs"] = int(state.get("runs", 0)) + 1
    if not selected:
        state["last_successful_run"] = now()
        event(state, "idle", "Kein geplanter Artikel offen")
        print("Kein geplanter Artikel offen.")
        return 0
    if contact_email:
        # The autonomous part is deliberately limited to acquiring source
        # metadata. It never drafts, validates or publishes medical content.
        return command_research(store, state, plan, selected[0]["article_id"], contact_email, False)
    # No model process is started here.  This makes the operational limit
    # explicit and preserves a durable, auditable queue for a later authorised
    # research worker.  Items remain planned: an unavailable executor is an
    # infrastructure condition, not an article-specific editorial defect.
    message = "Kein dedizierter, autorisierter Recherche-Executor konfiguriert; keine automatische KI-Ausführung gestartet."
    event(state, "waiting-for-executor", message)
    print("Wartend auf autorisierten Recherche-Executor; Artikel bleiben geplant.")
    return 0


def command_research(store: Store, state: dict[str, Any], plan: list[dict[str, Any]], article_id: str, contact_email: str, dry_run: bool) -> int:
    if state.get("stopped") or state.get("paused"):
        print("Kein Quellenabruf: Agent ist gestoppt oder pausiert.")
        return 0
    item = state["items"].get(article_id)
    configured = next((candidate for candidate in plan if candidate["article_id"] == article_id), None)
    if item is None or configured is None:
        raise ValueError("research benötigt eine bekannte --article-id")
    query = str(configured.get("research_query") or "").strip()
    if not query:
        raise ValueError("Für diesen Artikel ist keine research_query hinterlegt")
    if dry_run:
        print(json.dumps({"article_id": article_id, "query": query, "connector": "PubMed", "would_fetch": True}, ensure_ascii=False))
        return 0
    cache = store.state_dir / "sources"
    try:
        snapshot = cached_search(PubMedConnector(contact_email), article_id, query, cache)
    except PubMedError as exc:
        item["error"] = str(exc)
        item["updated_at"] = now()
        event(state, "source-retrieval-failed", str(exc), article_id)
        print(f"Quellenabruf fehlgeschlagen: {exc}", file=sys.stderr)
        return 1
    item["status"] = "researching"
    item["source_snapshot"] = str(snapshot)
    item["last_successful_step"] = "pubmed-metadata-retrieved"
    item["error"] = None
    item["updated_at"] = now()
    event(state, "source-retrieved", "PubMed-Metadaten abgerufen; fachliche Prüfung weiterhin offen", article_id)
    print(json.dumps({"article_id": article_id, "source_snapshot": str(snapshot), "status": item["status"]}, ensure_ascii=False))
    return 0


def render_report(state: dict[str, Any], plan: list[dict[str, Any]]) -> str:
    counts = Counter(item["status"] for item in state["items"].values())
    lines = ["# WikiMedica Editorial-Agent – Status", "", f"Erstellt: {now()}", "",
             f"Plan: {len(plan)} Artikel", f"Pausiert: {bool(state.get('paused'))}", f"Gestoppt: {bool(state.get('stopped'))}",
             "", "## Status", ""]
    for status in sorted(STATUS):
        lines.append(f"- {status}: {counts.get(status, 0)}")
    lines.extend(["", "## Artikel", "", "| ID | Titel | Risiko | Status |", "|---|---|---|---|"])
    for item in state["items"].values():
        lines.append(f"| {item['article_id']} | {item.get('title','')} | {item.get('risk','')} | {item['status']} |")
    lines.extend(["", "## Betriebshinweis", "", "Dieser Dispatcher startet keine Coding-Agenten und keinen Modellaufruf. Geplante Artikel bleiben wartend, bis ein eigener, autorisierter Recherche-Executor und die redaktionellen Sicherheitsgates konfiguriert sind.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["init", "run", "status", "health", "pause", "resume", "stop", "dry-run", "research", "report", "retry", "verify-publication"])
    parser.add_argument("--state-dir", type=Path, default=Path("/var/lib/wikimedica-editorial-agent"))
    parser.add_argument("--plan", type=Path, default=Path("data/editorial/article-plan.json"))
    parser.add_argument("--article-id")
    parser.add_argument("--contact-email", default=os.environ.get("WIKIMEDICA_NCBI_CONTACT_EMAIL", ""))
    parser.add_argument("--report", type=Path, default=Path("docs/editorial/wikimedica-agent-status.md"))
    args = parser.parse_args()
    store = Store(args.state_dir, args.plan)
    try:
        with store.lock():
            state, plan = store.read(), store.plan()
            ensure_items(state, plan)
            if args.command == "init":
                event(state, "init", "Statusregister initialisiert")
                store.write(state); print(store.state_path); return 0
            if args.command == "pause":
                state["paused"] = True; event(state, "pause", "Agent pausiert")
            elif args.command == "resume":
                state["paused"] = False; state["stopped"] = False; event(state, "resume", "Agent fortgesetzt")
            elif args.command == "stop":
                state["stopped"] = True; event(state, "stop", "Agent gestoppt")
            elif args.command == "retry":
                if not args.article_id or args.article_id not in state["items"]:
                    raise ValueError("retry benötigt eine bekannte --article-id")
                item = state["items"][args.article_id]
                item["retries"] += 1; item["status"] = "planned"; item["error"] = None; item["updated_at"] = now()
                event(state, "retry", "Für kontrollierten erneuten Lauf eingeplant", args.article_id)
            elif args.command == "verify-publication":
                # Publication is intentionally not inferred from a plan or PR.
                if not args.article_id or args.article_id not in state["items"]:
                    raise ValueError("verify-publication benötigt eine bekannte --article-id")
                item = state["items"][args.article_id]
                if not item.get("mediawiki_revision"):
                    raise ValueError("Keine verifizierte MediaWiki-Revision im Statusregister")
                print(json.dumps({"article_id": args.article_id, "mediawiki_revision": item["mediawiki_revision"], "verified": True}))
            elif args.command == "research":
                if not args.article_id:
                    raise ValueError("research benötigt --article-id")
                if not args.contact_email:
                    raise ValueError("research benötigt eine dienstliche NCBI-Kontaktadresse über --contact-email oder WIKIMEDICA_NCBI_CONTACT_EMAIL")
                rc = command_research(store, state, plan, args.article_id, args.contact_email, False)
                store.write(state)
                return rc
            elif args.command in {"run", "dry-run"}:
                rc = command_run(store, state, plan, args.command == "dry-run", args.contact_email)
                store.write(state)
                return rc
            elif args.command == "health":
                ok, problems = health(state, plan)
                print(json.dumps({"ok": ok, "problems": problems}, ensure_ascii=False))
                store.write(state)
                return 0 if ok else 1
            elif args.command == "status":
                print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
                store.write(state)
                return 0
            elif args.command == "report":
                args.report.parent.mkdir(parents=True, exist_ok=True)
                args.report.write_text(render_report(state, plan), encoding="utf-8")
                print(args.report)
            store.write(state)
            return 0
    except (ValueError, RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
