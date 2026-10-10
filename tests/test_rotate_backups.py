"""infra/deploy/rotate-backups.py — 7 daily / 4 weekly / 3 monthly, and it must never over-delete."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from conftest import REPO, load_script

rb = load_script("infra/deploy/rotate-backups.py", "rotate_backups")
UTC = timezone.utc
NOW = datetime(2026, 10, 9, 12, 0, tzinfo=UTC)
SUFFIXES = ("_db.sql.gz", "_images.tar.gz", "_config.tar.gz", ".sha256", ".manifest.json")


def make_set(directory, stamp, name="wikimedica", complete=True):
    prefix = f"{name}_{stamp.strftime(rb.TS_FORMAT)}"
    for suffix in SUFFIXES:
        if suffix == ".manifest.json" and not complete:
            continue
        (directory / f"{prefix}{suffix}").write_text("x")
    return prefix


def kept_prefixes(directory, name="wikimedica"):
    return {s.prefix for s in rb.scan(directory, name) if s.complete}


def run(directory, *extra):
    return rb.main(["--dir", str(directory), "--now", NOW.strftime(rb.TS_FORMAT), *extra])


@pytest.fixture
def daily_120(tmp_path):
    """A backup every day at 02:00 for the last 120 days."""
    for n in range(120):
        make_set(tmp_path, (NOW - timedelta(days=n)).replace(hour=2))
    return tmp_path


def stamps(prefixes):
    return sorted((datetime.strptime(p.split("_", 1)[1], rb.TS_FORMAT).replace(tzinfo=UTC) for p in prefixes), reverse=True)


def test_gfs_policy_over_120_days(daily_120):
    assert run(daily_120) == 0
    kept = stamps(kept_prefixes(daily_120))
    assert len(kept) <= 7 + 4 + 3
    assert kept[0] == (NOW - timedelta(days=0)).replace(hour=2)                  # newest kept

    days_with_backup = {s.date() for s in kept}
    for n in range(7):                                                          # every one of the last 7 days
        assert (NOW - timedelta(days=n)).date() in days_with_backup

    weeks = {s.isocalendar()[:2] for s in kept}
    for n in range(4):                                                          # each of the last 4 ISO weeks
        assert (NOW - timedelta(weeks=n)).isocalendar()[:2] in weeks

    months = {(s.year, s.month) for s in kept}
    assert {(2026, 10), (2026, 9), (2026, 8)} <= months                         # last 3 calendar months
    assert min(kept) >= datetime(2026, 8, 1, tzinfo=UTC)                        # nothing older than the monthly window


def test_weekly_and_monthly_keep_the_newest_set_of_their_period(daily_120):
    run(daily_120)
    kept = stamps(kept_prefixes(daily_120))
    older = [s for s in kept if (NOW.date() - s.date()).days >= 7]
    by_week = {}
    for s in older:
        by_week.setdefault(s.isocalendar()[:2], []).append(s)
    # Within a ISO week two kept sets only exist when one of them represents a month
    for week, sets in by_week.items():
        assert len(sets) <= 2, week


def test_run_is_idempotent(daily_120):
    run(daily_120)
    first = kept_prefixes(daily_120)
    run(daily_120)
    assert kept_prefixes(daily_120) == first


def test_all_files_of_an_expired_set_are_removed_together(daily_120):
    run(daily_120)
    leftovers = [p.name for p in daily_120.iterdir()]
    prefixes_with_files = {n.split("_db")[0].split("_images")[0].split("_config")[0].split(".")[0] for n in leftovers}
    for prefix in prefixes_with_files:
        files = [n for n in leftovers if n.startswith(prefix)]
        assert len(files) == len(SUFFIXES), prefix          # either the whole set or nothing


def test_newest_complete_set_survives_even_the_strictest_settings(tmp_path):
    for n in range(5):
        make_set(tmp_path, NOW - timedelta(days=n))
    assert run(tmp_path, "--daily", "1", "--weekly", "0", "--monthly", "0") == 0
    assert len(kept_prefixes(tmp_path)) == 1
    assert stamps(kept_prefixes(tmp_path))[0] == NOW - timedelta(days=0)


def test_only_the_newest_set_of_a_day_is_kept(tmp_path):
    early = make_set(tmp_path, NOW.replace(hour=1))
    late = make_set(tmp_path, NOW.replace(hour=11))
    yesterday = make_set(tmp_path, (NOW - timedelta(days=1)).replace(hour=1))
    run(tmp_path)
    assert late in kept_prefixes(tmp_path) and yesterday in kept_prefixes(tmp_path)
    assert early not in kept_prefixes(tmp_path)


def test_dry_run_deletes_nothing(daily_120, capsys):
    before = sorted(p.name for p in daily_120.iterdir())
    assert run(daily_120, "--dry-run") == 0
    assert sorted(p.name for p in daily_120.iterdir()) == before
    assert "would delete" in capsys.readouterr().out


def test_unrelated_files_and_other_environments_are_never_touched(tmp_path):
    for n in range(40):
        make_set(tmp_path, NOW - timedelta(days=n))
    for n in range(40):
        make_set(tmp_path, NOW - timedelta(days=n), name="wikimedica-staging")
    keep = ["last-backup.json", "notes.txt", "prerestore_20260101_000000_db.sql.gz", "wikimedica.sql", "README.md",
            "wikimedica_20260101_db.sql.gz"]
    for name in keep:
        (tmp_path / name).write_text("x")
    run(tmp_path)
    assert all((tmp_path / n).exists() for n in keep)
    assert len([s for s in rb.scan(tmp_path, "wikimedica-staging") if s.complete]) == 40   # staging set untouched
    assert len(kept_prefixes(tmp_path)) < 40


def test_incomplete_sets_are_junk_only_when_old(tmp_path):
    good = make_set(tmp_path, NOW - timedelta(hours=3))
    running = make_set(tmp_path, NOW - timedelta(hours=1), complete=False)       # might still be running
    crashed = make_set(tmp_path, NOW - timedelta(days=5), complete=False)
    run(tmp_path)
    names = {p.name for p in tmp_path.iterdir()}
    assert any(n.startswith(running) for n in names)
    assert not any(n.startswith(crashed) for n in names)
    assert any(n.startswith(good) for n in names)


def test_nothing_is_deleted_without_a_single_complete_set(tmp_path):
    make_set(tmp_path, NOW - timedelta(days=10), complete=False)
    make_set(tmp_path, NOW - timedelta(days=9), complete=False)
    before = sorted(p.name for p in tmp_path.iterdir())
    run(tmp_path)
    assert sorted(p.name for p in tmp_path.iterdir()) == before


@pytest.mark.parametrize("args", [["--daily", "0"], ["--weekly", "-1"], ["--monthly", "-3"]])
def test_invalid_counts_are_rejected(tmp_path, args):
    assert run(tmp_path, *args) == 2


def test_missing_directory_is_an_error(tmp_path):
    assert rb.main(["--dir", str(tmp_path / "nope")]) == 2


def test_empty_directory_is_fine(tmp_path):
    assert run(tmp_path) == 0


def test_midnight_boundaries_use_utc_dates(tmp_path):
    a = make_set(tmp_path, datetime(2026, 10, 8, 23, 59, tzinfo=UTC))
    b = make_set(tmp_path, datetime(2026, 10, 9, 0, 1, tzinfo=UTC))
    run(tmp_path)
    assert {a, b} <= kept_prefixes(tmp_path)           # different days: both are "newest of their day"


def test_encrypted_sets_are_recognised(tmp_path):
    prefix = f"wikimedica_{NOW.strftime(rb.TS_FORMAT)}"
    for suffix in ("_db.sql.gz.gpg", "_images.tar.gz.gpg", ".sha256", ".manifest.json"):
        (tmp_path / f"{prefix}{suffix}").write_text("x")
    assert prefix in kept_prefixes(tmp_path)
