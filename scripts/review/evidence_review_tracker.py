#!/usr/bin/env python3
"""Audit-friendly article evidence-check scheduling.

scan: determine due dates from content + append-only evidence review ledger.
record: accept a validated, externally produced structured AI assessment.
This script does not run AI; it NEVER renews checks merely due to no PubMed hits.

Usage:
    python scripts/review/evidence_review_tracker.py scan \
       --ledger /var/lib/wikimedica-pull/evidence-reviews.jsonl \
       --out /var/lib/wikimedica-pull/evidence-review-queue.json
    python scripts/review/evidence_review_tracker.py record --result-json /secure/result.json \
       --ledger /var/lib/wikimedica-pull/evidence-reviews.jsonl
"""
from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "content"
DEFAULT_LEDGER = Path("/var/lib/wikimedica-pull/evidence-reviews.jsonl")
ACTIVE = {"draft", "in-review", "advisor-review", "approved", "published"}
FOLDERS = {"specialties", "articles", "patient-info", "pharmaka", "therapies", "published"}
FM_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n", re.S)


def next_year(day: date) -> date:
    year = day.year + 1
    max_day = calendar.monthrange(year, day.month)[1]
    return day.replace(year=year, day=min(day.day, max_day))


def source_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def articles() -> list[dict]:
    items = []
    for path in sorted(CONTENT.rglob("*.md")):
        rel = path.relative_to(CONTENT)
        if len(rel.parts) < 2 or rel.parts[0] not in FOLDERS:
            continue
        raw = path.read_text(encoding="utf-8")
        match = FM_RE.match(raw)
        if not match:
            continue
        fm = yaml.safe_load(match.group(1))
        if not isinstance(fm, dict) or fm.get("status") not in ACTIVE:
            continue
        slug = str(fm.get("slug") or "").strip()
        if slug != path.stem or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            continue
        items.append({
            "slug": slug, "title": str(fm.get("title", "")),
            "path": str(rel), "status": fm["status"], "sha256": source_sha(path),
            "baseline": str(fm.get("updated") or fm.get("created") or date.today()),
        })
    return items


def load_ledger(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            if not isinstance(data, dict):
                raise ValueError("JSON must be object")
            out.append(data)
        except (ValueError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid evidence ledger at {path}:{n}: {exc}") from exc
    return out


def scan(ledger: Path, out: Path, day: date) -> int:
    recent = {}
    for event in load_ledger(ledger):
        slug = event.get("slug")
        if slug and event.get("checked_at"):
            recent[slug] = event
    queue = []
    for item in articles():
        last = recent.get(item["slug"])
        try:
            baseline = date.fromisoformat(item["baseline"])
        except ValueError:
            baseline = day - timedelta(days=366)
        if last and last.get("decision") == "no_change" and last.get("sha256") == item["sha256"]:
            try:
                reviewed = date.fromisoformat(last["checked_at"])
                due = next_year(reviewed)
            except (KeyError, ValueError):
                due = day
        else:
            due = next_year(baseline)
            if last and last.get("decision") in ("update_required", "uncertain", "safety_alert"):
                due = day
            elif last and last.get("sha256") != item["sha256"]:
                # Content changed since the last check -> new evidence baseline required.
                due = day
        if due <= day:
            queue.append({
                "slug": item["slug"], "title": item["title"], "path": "content/" + item["path"],
                "status": item["status"], "due": due.isoformat(), "sha256": item["sha256"],
                "reason": "evidence_recheck_due",
            })
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "generated_at": day.isoformat(),
        "due_count": len(queue), "note": "Queue only; no AI assessment was performed.",
        "due": queue,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"due_count": len(queue), "queue": str(out)}, ensure_ascii=False))
    return 0


def record(ledger: Path, path: Path, day: date) -> int:
    """Record externally generated AI review, never manufacture a pass."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("assessment must be a JSON object")
    slug = data.get("slug")
    current = next((a for a in articles() if a["slug"] == slug), None)
    if not current:
        raise ValueError("unknown/invalid article slug")
    if data.get("sha256") != current["sha256"]:
        raise ValueError("assessment did not evaluate the current article hash")
    decision = data.get("decision")
    if decision not in ("no_change", "update_required", "uncertain", "safety_alert"):
        raise ValueError("invalid assessment decision")
    if data.get("method") not in ("ai", "human"):
        raise ValueError("method must be ai or human")
    if not str(data.get("model_or_reviewer", "")).strip():
        raise ValueError("model/version or reviewer identity is required")
    try:
        checked = date.fromisoformat(str(data["checked_at"]))
    except (KeyError, ValueError) as exc:
        raise ValueError("valid checked_at is required") from exc
    if checked > day or (day - checked).days > 7:
        raise ValueError("assessment must be from the last seven days")
    if not str(data.get("summary") or "").strip():
        raise ValueError("assessment rationale is required")
    if decision == "no_change":
        # Neither an absent PubMed feed nor an unverified guideline collection
        # may silently extend the revision date.
        if data.get("source_monitor_healthy") is not True:
            raise ValueError("source_monitor_healthy must be true to extend due date")
        if data.get("guideline_monitor_healthy") is not True:
            raise ValueError("guideline_monitor_healthy must be true")
        if data.get("confidence") != "high":
            raise ValueError("high confidence is required for automatic no-change")
        if not (data.get("sources_checked") or data.get("source_search_audit_url")):
            raise ValueError("sources_checked or source_search_audit_url is required")
        if data.get("safety_concern") is not False:
            raise ValueError("explicit safety_concern: false is required")
    result = {
        "slug": slug, "sha256": current["sha256"],
        "decision": decision, "method": data["method"],
        "model_or_reviewer": data["model_or_reviewer"],
        "checked_at": checked.isoformat(),
        "next_evidence_check": next_year(checked).isoformat() if decision == "no_change" else None,
        "summary": data["summary"],
        "sources_checked": data.get("sources_checked", []),
        "source_search_audit_url": data.get("source_search_audit_url"),
        "source_monitor_healthy": data.get("source_monitor_healthy"),
        "guideline_monitor_healthy": data.get("guideline_monitor_healthy"),
        "confidence": data.get("confidence"),
        "safety_concern": data.get("safety_concern"),
    }
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.chmod(ledger, 0o600)
    print(json.dumps({"result": "recorded", "slug": slug,
                      "decision": decision,
                      "next_evidence_check": result["next_evidence_check"]}, ensure_ascii=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["scan", "record"])
    p.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    p.add_argument("--out", type=Path, default=Path("/var/lib/wikimedica-pull/evidence-review-queue.json"))
    p.add_argument("--result-json", type=Path)
    p.add_argument("--as-of", help="Only for repeatable tests: YYYY-MM-DD")
    args = p.parse_args()
    day = date.fromisoformat(args.as_of) if args.as_of else date.today()
    try:
        if args.action == "scan":
            return scan(args.ledger, args.out, day)
        if args.result_json is None:
            p.error("record requires --result-json")
        return record(args.ledger, args.result_json, day)
    except (ValueError, OSError, yaml.YAMLError, json.JSONDecodeError) as exc:
        print(f"Evidence review error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
