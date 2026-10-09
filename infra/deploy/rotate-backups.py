#!/usr/bin/env python3
"""
rotate-backups.py — grandfather-father-son rotation for Wikimedica backup sets.

Keeps (relative to "now", UTC):
  * the newest backup of each of the last 7 days             (daily)
  * the newest backup of each of the last 4 ISO weeks        (weekly)
  * the newest backup of each of the last 3 calendar months  (monthly)
A set that is selected by any rule is kept. Counts are configurable.

A *set* is every file that shares the prefix  <name>_YYYYmmdd_HHMMSS  (database dump,
images archive, config archive, checksums, manifest; plain or .gpg-encrypted).

Safety rules - this script deletes backups, so it is deliberately conservative:
  * only files that match the naming scheme are ever touched
  * only COMPLETE sets (those with a "<prefix>.manifest.json" written as the LAST step of
    a successful backup) count as backups. The newest complete set is never deleted.
  * incomplete sets (a backup that crashed) are removed only once they are older than
    --junk-age-hours (default 48), so a backup that is still running is never touched
  * --dry-run shows what would happen
  * with zero complete sets nothing is deleted at all

Usage:
    rotate-backups.py --dir /opt/wikimedica/backups [--name wikimedica] [--dry-run]
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

SET_RE = re.compile(r"^(?P<name>[a-z0-9-]+)_(?P<ts>\d{8}_\d{6})(?:_|\.)")
TS_FORMAT = "%Y%m%d_%H%M%S"


@dataclass
class BackupSet:
    name: str
    stamp: datetime
    files: list[Path] = field(default_factory=list)
    complete: bool = False

    @property
    def prefix(self) -> str:
        return f"{self.name}_{self.stamp.strftime(TS_FORMAT)}"


def scan(directory: Path, name: str) -> list[BackupSet]:
    sets: dict[str, BackupSet] = {}
    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue
        m = SET_RE.match(path.name)
        if not m or m.group("name") != name:
            continue
        stamp = datetime.strptime(m.group("ts"), TS_FORMAT).replace(tzinfo=timezone.utc)
        entry = sets.setdefault(m.group("ts"), BackupSet(name=name, stamp=stamp))
        entry.files.append(path)
        if path.name == f"{entry.prefix}.manifest.json":
            entry.complete = True
    return sorted(sets.values(), key=lambda s: s.stamp, reverse=True)


def choose_keep(sets: list[BackupSet], now: datetime, daily: int, weekly: int, monthly: int) -> set[str]:
    """Return the prefixes to keep. `sets` must be complete sets, newest first."""
    keep: set[str] = set()
    if not sets:
        return keep
    keep.add(sets[0].prefix)  # the newest complete set is never deleted

    today = now.date()
    seen: set[tuple] = set()
    for s in sets:  # newest first => the first one seen per period is the newest of that period
        d = s.stamp.date()
        if (today - d).days < daily and ("d", d) not in seen:
            seen.add(("d", d)); keep.add(s.prefix)

        iso = d.isocalendar()
        week_start = d - timedelta(days=d.weekday())
        now_week_start = today - timedelta(days=today.weekday())
        if (now_week_start - week_start).days < weekly * 7 and ("w", iso[0], iso[1]) not in seen:
            seen.add(("w", iso[0], iso[1])); keep.add(s.prefix)

        months_ago = (today.year - d.year) * 12 + (today.month - d.month)
        if 0 <= months_ago < monthly and ("m", d.year, d.month) not in seen:
            seen.add(("m", d.year, d.month)); keep.add(s.prefix)
    return keep


def plan(directory: Path, name: str, now: datetime, daily: int, weekly: int, monthly: int,
         junk_age_hours: float) -> tuple[list[BackupSet], list[BackupSet], list[BackupSet]]:
    """Return (kept, deleted_complete, deleted_junk)."""
    all_sets = scan(directory, name)
    complete = [s for s in all_sets if s.complete]
    incomplete = [s for s in all_sets if not s.complete]
    keep_prefixes = choose_keep(complete, now, daily, weekly, monthly)
    kept = [s for s in complete if s.prefix in keep_prefixes]
    deleted = [s for s in complete if s.prefix not in keep_prefixes] if complete else []
    junk_cutoff = now - timedelta(hours=junk_age_hours)
    junk = [s for s in incomplete if s.stamp < junk_cutoff] if complete else []
    return kept, deleted, junk


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Rotate Wikimedica backup sets (daily/weekly/monthly).")
    p.add_argument("--dir", required=True, type=Path)
    p.add_argument("--name", default="wikimedica", help="set name prefix (wikimedica or wikimedica-staging)")
    p.add_argument("--daily", type=int, default=7)
    p.add_argument("--weekly", type=int, default=4)
    p.add_argument("--monthly", type=int, default=3)
    p.add_argument("--junk-age-hours", type=float, default=48)
    p.add_argument("--now", help="override the current time (UTC, YYYYmmdd_HHMMSS); for tests")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    if not args.dir.is_dir():
        print(f"ERROR: not a directory: {args.dir}", file=sys.stderr)
        return 2
    if min(args.daily, args.weekly, args.monthly) < 0 or args.daily < 1:
        print("ERROR: --daily must be >= 1 and the others >= 0", file=sys.stderr)
        return 2
    now = (datetime.strptime(args.now, TS_FORMAT).replace(tzinfo=timezone.utc)
           if args.now else datetime.now(timezone.utc))

    kept, deleted, junk = plan(args.dir, args.name, now, args.daily, args.weekly, args.monthly, args.junk_age_hours)
    verb = "would delete" if args.dry_run else "deleting"
    for group, label in ((deleted, "expired"), (junk, "incomplete")):
        for s in group:
            print(f"{verb} {label} set {s.prefix} ({len(s.files)} files)")
            if not args.dry_run:
                for f in s.files:
                    f.unlink()
    print(f"kept {len(kept)} complete sets; removed {len(deleted)} expired and {len(junk)} incomplete"
          + (" (dry run)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
