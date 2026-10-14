#!/usr/bin/env python3
"""Gemeinsame Bausteine der WikiMedica-Redaktionspipeline.

Enthält: SQLite-Warteschlange mit atomarem Beanspruchen (mehrere Arbeiter ohne
Kollision), zentralen Anfragenzähler für das AT-AI-Gateway, Hilfsfunktionen für
Dateinamen, Fachgebiete und einfache HTTP-Aufrufe.

Keine externen Abhängigkeiten außer der Standardbibliothek (der Dienst läuft
mit ``python3 -I``).
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import time
import unicodedata
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_STATE_DIR = Path("/var/lib/wikimedica-editorial-agent")
DB_NAME = "pipeline.sqlite"
STALE_CLAIM_S = 45 * 60
STALE_INFLIGHT_S = 25 * 60

# Harte Gateway-Grenzen (Absprache mit claude-code-atinfra-control, siehe Atlas)
MAX_REQUESTS_PER_MIN = int(os.environ.get("WM_MAX_REQUESTS_PER_MIN", "4"))
MAX_CONCURRENT = int(os.environ.get("WM_MAX_CONCURRENT", "3"))


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def log(msg: str) -> None:
    print(f"[{now_iso()}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Dateinamen / Texte
# ---------------------------------------------------------------------------
_UMLAUTS = {"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "ae", "Ö": "oe", "Ü": "ue", "ß": "ss"}


def slugify(title: str) -> str:
    """Kleinbuchstaben-ASCII mit Bindestrichen, passend zum Schema (^[a-z0-9]+(-[a-z0-9]+)*$)."""
    text = "".join(_UMLAUTS.get(c, c) for c in title)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:90].strip("-")


def norm_title(title: str) -> str:
    """Vergleichsform für Dublettenprüfung."""
    t = title.lower()
    t = re.sub(r"\(.*?\)", " ", t)
    t = "".join(_UMLAUTS.get(c, c) for c in t)
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    stop = {"und", "oder", "bei", "des", "der", "die", "das", "sowie", "durch", "sonstige", "sonstiger", "sonstiges",
            "nicht", "naeher", "bezeichnet", "bezeichnete", "mit", "von", "im", "in", "an", "am", "auf"}
    return " ".join(w for w in t.split() if w not in stop)


# Fachgebiet (kanonische Namen aus data/metadata/article-schema.yaml) je ICD-10-GM-Kapitel/Gruppe
CHAPTER_SPECIALTY = {
    "01": "Infektiologie", "02": "Hämatologie/Onkologie", "03": "Hämatologie/Onkologie",
    "04": "Endokrinologie/Diabetologie", "05": "Psychiatrie", "06": "Neurologie", "07": "Augenheilkunde",
    "08": "Chirurgie", "09": "Kardiologie", "10": "Pneumologie", "11": "Gastroenterologie",
    "12": "Dermatologie", "13": "Rheumatologie", "14": "Nephrologie", "15": "Gynäkologie/Geburtshilfe",
    "16": "Pädiatrie", "17": "Pädiatrie", "18": "Innere Medizin", "19": "Orthopädie/Unfallchirurgie",
}
GROUP_SPECIALTY = [  # (erster, letzter Dreisteller, Fachgebiet) – überschreibt das Kapitel
    ("E10", "E14", "Endokrinologie/Diabetologie"), ("N17", "N19", "Nephrologie"), ("N20", "N23", "Urologie"),
    ("N30", "N39", "Urologie"), ("N40", "N53", "Urologie"), ("N60", "N98", "Gynäkologie/Geburtshilfe"),
    ("I60", "I69", "Neurologie"), ("K00", "K14", "Chirurgie"), ("J30", "J39", "Chirurgie"),
    ("H60", "H95", "Chirurgie"), ("C00", "C97", "Hämatologie/Onkologie"), ("D50", "D89", "Hämatologie/Onkologie"),
    ("F00", "F09", "Psychiatrie"), ("R00", "R99", "Innere Medizin"), ("K35", "K46", "Chirurgie"), ("K60", "K67", "Chirurgie"),
    ("K80", "K87", "Gastroenterologie"), ("M30", "M36", "Rheumatologie"), ("M00", "M25", "Rheumatologie"),
    ("M40", "M54", "Orthopädie/Unfallchirurgie"), ("M60", "M99", "Orthopädie/Unfallchirurgie"),
]


def code_specialty(code3: str, chapter: str) -> str:
    for lo, hi, spec in GROUP_SPECIALTY:
        if lo <= code3 <= hi:
            return spec
    return CHAPTER_SPECIALTY.get(chapter, "Innere Medizin")


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
UA = "wikimedica-editorial-pipeline/2.0 (+https://wikimedica.info; redaktion@at-medical.de)"


def http_get(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def http_get_json(url: str, timeout: int = 60) -> dict:
    return json.loads(http_get(url, timeout).decode("utf-8"))


# ---------------------------------------------------------------------------
# SQLite-Warteschlange
# ---------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
  id TEXT PRIMARY KEY, kind TEXT NOT NULL, title TEXT NOT NULL, slug TEXT NOT NULL,
  specialty TEXT, extra TEXT, priority REAL NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'planned',
  claimed_by TEXT, claimed_at REAL, attempts INTEGER NOT NULL DEFAULT 0,
  error TEXT, draft_path TEXT, pr TEXT, updated_at TEXT
);
CREATE INDEX IF NOT EXISTS items_status_prio ON items(status, priority DESC);
CREATE UNIQUE INDEX IF NOT EXISTS items_slug ON items(slug);
CREATE TABLE IF NOT EXISTS events (ts TEXT, item TEXT, kind TEXT, msg TEXT, t REAL);
CREATE TABLE IF NOT EXISTS calls (start REAL, end REAL, worker TEXT);
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);
"""
# Status: planned -> claimed -> drafted -> ready -> published
#         claimed -> review (Faktenprüfung nicht bestanden, Prüfliste) | duplicate | failed


class Queue:
    def __init__(self, state_dir: Path = DEFAULT_STATE_DIR):
        self.dir = Path(state_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / DB_NAME
        self.db = sqlite3.connect(str(self.path), timeout=60, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA busy_timeout=60000")
        self.db.executescript(SCHEMA)

    @contextmanager
    def tx(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield self.db
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        else:
            self.db.execute("COMMIT")

    # -- Befüllen ----------------------------------------------------------
    def add_items(self, items: list[dict]) -> int:
        """Fügt neue Einträge hinzu; vorhandene IDs/Slugs bleiben unverändert. Gibt die Zahl neuer Einträge zurück."""
        added = 0
        with self.tx() as db:
            for it in items:
                cur = db.execute(
                    "INSERT OR IGNORE INTO items(id,kind,title,slug,specialty,extra,priority,status,updated_at) "
                    "VALUES(?,?,?,?,?,?,?,?,?)",
                    (it["id"], it["kind"], it["title"], it["slug"], it.get("specialty"),
                     json.dumps(it.get("extra", {}), ensure_ascii=False), float(it.get("priority", 0)),
                     it.get("status", "planned"), now_iso()))
                added += cur.rowcount
        return added

    # -- Beanspruchen ------------------------------------------------------
    def claim(self, worker: str, kinds: list[str] | None = None) -> sqlite3.Row | None:
        """Atomar den wichtigsten offenen Eintrag beanspruchen (BEGIN IMMEDIATE = Schreibsperre)."""
        t = time.time()
        with self.tx() as db:
            db.execute("UPDATE items SET status='planned', claimed_by=NULL WHERE status='claimed' AND claimed_at < ?",
                       (t - STALE_CLAIM_S,))
            where, args = "status='planned' AND attempts < 3", []
            if kinds:
                where += " AND kind IN (%s)" % ",".join("?" * len(kinds))
                args += kinds
            row = db.execute(f"SELECT id FROM items WHERE {where} ORDER BY priority DESC, id LIMIT 1", args).fetchone()
            if not row:
                return None
            db.execute("UPDATE items SET status='claimed', claimed_by=?, claimed_at=?, attempts=attempts+1, updated_at=? "
                       "WHERE id=?", (worker, t, now_iso(), row["id"]))
            return db.execute("SELECT * FROM items WHERE id=?", (row["id"],)).fetchone()

    def set_status(self, item_id: str, status: str, error: str | None = None, **cols) -> None:
        sets, args = ["status=?", "error=?", "updated_at=?"], [status, error, now_iso()]
        for k, v in cols.items():
            sets.append(f"{k}=?")
            args.append(v)
        args.append(item_id)
        with self.tx() as db:
            db.execute(f"UPDATE items SET {', '.join(sets)} WHERE id=?", args)

    def release(self, item_id: str, error: str) -> None:
        """Fehler: zurück auf planned (bis 3 Versuche), danach failed."""
        with self.tx() as db:
            row = db.execute("SELECT attempts FROM items WHERE id=?", (item_id,)).fetchone()
            status = "planned" if row and row["attempts"] < 3 else "failed"
            db.execute("UPDATE items SET status=?, error=?, claimed_by=NULL, updated_at=? WHERE id=?",
                       (status, error[:400], now_iso(), item_id))

    def merge_extra(self, item_id: str, data: dict) -> None:
        with self.tx() as db:
            row = db.execute("SELECT extra FROM items WHERE id=?", (item_id,)).fetchone()
            cur = json.loads(row["extra"] or "{}") if row else {}
            cur.update(data)
            db.execute("UPDATE items SET extra=? WHERE id=?", (json.dumps(cur, ensure_ascii=False), item_id))

    def event(self, item: str, kind: str, msg: str) -> None:
        with self.tx() as db:
            db.execute("INSERT INTO events VALUES(?,?,?,?,?)", (now_iso(), item, kind, msg[:500], time.time()))

    def counts(self) -> dict[str, int]:
        return {r["status"]: r["n"] for r in self.db.execute("SELECT status, COUNT(*) n FROM items GROUP BY status")}

    # -- Gateway-Zähler ----------------------------------------------------
    def acquire_call_slot(self, worker: str) -> float:
        """Wartet, bis höchstens MAX_REQUESTS_PER_MIN Anfragen/Minute und MAX_CONCURRENT gleichzeitig offen sind.

        Gibt den Startzeitpunkt zurück (Schlüssel für ``release_call_slot``).
        """
        while True:
            t = time.time()
            with self.tx() as db:
                db.execute("DELETE FROM calls WHERE end IS NULL AND start < ?", (t - STALE_INFLIGHT_S,))
                db.execute("DELETE FROM calls WHERE start < ?", (t - 3600,))
                inflight = db.execute("SELECT COUNT(*) FROM calls WHERE end IS NULL").fetchone()[0]
                last_min = db.execute("SELECT COUNT(*) FROM calls WHERE start > ?", (t - 60,)).fetchone()[0]
                slow = db.execute("SELECT v FROM meta WHERE k='slow_until'").fetchone()
                slowed = bool(slow and float(slow["v"]) > t)  # Drosselung: Vorgabe control 14.10. (Priorität Doc Blue und 3CX-Agent)
                max_conc = 1 if slowed else MAX_CONCURRENT
                max_rate = 1 if slowed else MAX_REQUESTS_PER_MIN
                if inflight < max_conc and last_min < max_rate:
                    db.execute("INSERT INTO calls(start,end,worker) VALUES(?,NULL,?)", (t, worker))
                    return t
            time.sleep(3)

    def slow_down(self, seconds: int = 600) -> None:
        """Gateway langsam oder überlastet (429/5xx, Antwortzeit über 90 s): für einige Minuten auf 1 Anfrage/Minute."""
        with self.tx() as db:
            db.execute("INSERT INTO meta(k,v) VALUES('slow_until',?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
                       (str(time.time() + seconds),))

    def release_call_slot(self, start: float, worker: str) -> None:
        with self.tx() as db:
            db.execute("UPDATE calls SET end=? WHERE start=? AND worker=?", (time.time(), start, worker))

    def throughput(self) -> dict:
        t = time.time()
        row = self.db.execute("SELECT COUNT(*) n FROM events WHERE kind='ready' AND t > ?", (t - 3600,)).fetchone()
        return {"ready_last_hour": row["n"]}
