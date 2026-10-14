#!/usr/bin/env python3
"""Themenbacklog der WikiMedica-Redaktionspipeline aus freien amtlichen Katalogen.

Quellen (nur frei nutzbare, siehe docs/editorial/redaktions-ki-pipeline.md):
  * ICD-10-GM 2026 (BfArM, amtliches Werk nach § 5 UrhG; Quellenangabe, Änderungsverbot):
    dreistellige Kategorien -> WM-DIS-
  * ATC-GM mit DDD 2026 (BfArM, amtliche deutsche Fassung; Urheber WIdO): nur Code und Name
    von Einzelwirkstoffen, KEINE DDD/Dosisangaben -> WM-DRUG-
  * EMA-Arzneimitteldatenbank (Bericht „Medicines“, Wiederverwendung mit Quellenangabe):
    zentral zugelassene Handelsnamen -> WM-TRADE-
  * Eurostat hlth_co_disch2 (Krankenhausentlassungen Deutschland) als Häufigkeitsindikator.
Rote Liste / Gelbe Liste und Pschyrembel werden NICHT verwendet (keine Lizenz).

Aufruf:
  wm_catalog.py build   --repo <Repo> [--eurostat-json <Datei>] [--ema-xlsx <Datei>] [--atc-txt <Datei>]
  wm_catalog.py load-queue --repo <Repo> --state-dir <Verzeichnis>
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from wm_common import (Queue, code_specialty, http_get_json, log, norm_title, slugify)  # noqa: E402

ICD_DIR = "data/catalogs/icd10-gm-2026"
BACKLOG_DIR = "data/editorial/backlog"
CONTENT_DIRS = ("specialties", "articles", "patient-info", "pharmaka", "therapies", "published")
EUROSTAT_URL = ("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/hlth_co_disch2"
                "?format=JSON&geo=DE&age=TOTAL&sex=T&lang=EN")
FM_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n", re.S)

# Kapitel 20 (V-Y äußere Ursachen), 21 (Z Faktoren), 22 (U Schlüsselnummern für besondere Zwecke) sind keine Diagnosen
EXCLUDED_CHAPTERS = {"20", "21", "22"}
KEEP_U = {"U07"}  # COVID-19
RESIDUAL_RE = re.compile(r"\b(sonstige|nicht näher bezeichnet|nicht naeher bezeichnet|folgen|mangels)\b", re.I)
STAR_RE = re.compile(r"(anderenorts|andernorts) klassifiziert", re.I)
TITLE_BAD_CHARS = "#<>[]|{}:"

# ICD-10-GM-Kategorien, die bereits durch handgeschriebene Artikel abgedeckt sind (Code -> Slug).
# Wird beim Bau zusätzlich zur Titelähnlichkeit angewandt; fehlende Slugs werden ignoriert.
ALIASES = {
    "I10": "arterielle-hypertonie", "I11": "arterielle-hypertonie", "I12": "arterielle-hypertonie",
    "I13": "arterielle-hypertonie", "I25": "koronare-herzkrankheit", "I20": "koronare-herzkrankheit",
    "I21": "akutes-koronarsyndrom-und-myokardinfarkt", "I24": "akutes-koronarsyndrom-und-myokardinfarkt",
    "I50": "chronische-herzinsuffizienz", "I48": "vorhofflimmern", "I63": "schlaganfall",
    "I73": "periphere-arterielle-verschlusskrankheit", "I80": "tiefe-venenthrombose", "I82": "tiefe-venenthrombose",
    "I26": "lungenembolie", "I35": "aortenklappenstenose", "I40": "myokarditis", "I41": "myokarditis",
    "I33": "infektioese-endokarditis", "I34": "herzklappenerkrankungen", "I36": "herzklappenerkrankungen",
    "I37": "herzklappenerkrankungen", "I38": "herzklappenerkrankungen", "I95": "orthostatische-hypotonie",
    "E11": "diabetes-mellitus-typ-2", "E10": "diabetes-mellitus-typ-1", "E66": "adipositas",
    "E88": "metabolisches-syndrom", "M10": "gicht", "E03": "hypothyreose", "E02": "hypothyreose",
    "E05": "hyperthyreose", "M81": "osteoporose", "E55": "vitamin-d-mangel", "E21": "primaerer-hyperparathyreoidismus",
    "E28": "polyzystisches-ovarialsyndrom", "K76": "masld", "E04": "schilddruesenknoten", "E16": "hypoglykaemie",
    "J44": "chronisch-obstruktive-lungenerkrankung-copd", "J45": "asthma-bronchiale", "J18": "pneumonie",
    "G47": "obstruktive-schlafapnoe", "J30": "allergische-rhinitis", "J84": "idiopathische-lungenfibrose",
    "J96": "respiratorische-insuffizienz", "J20": "akute-bronchitis", "C34": "bronchialkarzinom",
    "I27": "pulmonale-hypertonie", "F32": "depressive-stoerung", "F41": "angststoerungen",
    "G30": "alzheimer-demenz", "G20": "morbus-parkinson", "G43": "migraene", "G40": "epilepsie",
    "G35": "multiple-sklerose", "G45": "transitorische-ischamische-attacke", "G62": "periphere-neuropathie",
    "F90": "aufmerksamkeitsdefizit-hyperaktivitaetsstoerung", "F31": "bipolare-stoerung",
    "F10": "alkoholkonsumstoerung", "F20": "schizophrenie", "K21": "gastrooesophageale-refluxkrankheit",
    "K29": "helicobacter-pylori-gastritis", "K25": "ulkuskrankheit", "K26": "ulkuskrankheit",
    "K58": "reizdarmsyndrom", "K50": "morbus-crohn", "K51": "colitis-ulcerosa", "K57": "divertikelkrankheit",
    "K80": "cholezystolithiasis", "K85": "akute-pankreatitis", "K74": "leberzirrhose", "N18": "chronische-nierenkrankheit",
    "N17": "akute-nierenschaedigung", "N39": "harnwegsinfektion", "N10": "pyelonephritis", "N20": "urolithiasis",
    "N40": "benigne-prostatahyperplasie", "C61": "prostatakarzinom", "C64": "nierenzellkarzinom",
    "N04": "nephrotisches-syndrom", "M54": "unspezifischer-kreuzschmerz", "M17": "gonarthrose",
    "M06": "rheumatoide-arthritis", "M05": "rheumatoide-arthritis", "M32": "systemischer-lupus-erythematodes", "M79": "fibromyalgiesyndrom", "L20": "atopisches-ekzem", "L40": "psoriasis",
    "L70": "akne-vulgaris", "M45": "axiale-spondyloarthritis", "G56": "karpaltunnelsyndrom", "J10": "influenza",
    "J11": "influenza", "U07": "covid-19", "A09": "akute-infektioese-gastroenteritis", "A41": "sepsis",
    "B20": "hiv-infektion", "N80": "endometriose", "O14": "hypertensive-schwangerschaftserkrankungen",
    "O24": "gestationsdiabetes", "N95": "wechseljahresassoziierte-beschwerden", "C50": "mammakarzinom",
    "C18": "kolorektales-karzinom", "C20": "kolorektales-karzinom", "D50": "eisenmangelanaemie",
    "H40": "glaukom", "H35": "altersabhaengige-makuladegeneration",
}


# ---------------------------------------------------------------------------
# Vorhandene Artikel
# ---------------------------------------------------------------------------
def scan_existing(repo: Path) -> dict:
    """Index vorhandener Artikel: slug, normierter Titel, ICD-Codes, ATC-Codes."""
    import yaml
    out = {"slugs": {}, "titles": {}, "icd": {}, "atc": {}}
    for d in CONTENT_DIRS:
        for p in (repo / "content" / d).rglob("*.md"):
            if p.name.lower() == "readme.md":
                continue
            m = FM_RE.match(p.read_text(encoding="utf-8"))
            if not m:
                continue
            try:
                fm = yaml.safe_load(m.group(1)) or {}
            except yaml.YAMLError:
                continue
            slug = p.stem
            out["slugs"][slug] = fm.get("title", slug)
            out["titles"][norm_title(str(fm.get("title", slug)))] = slug
            for c in fm.get("icd10") or []:
                out["icd"][str(c).split(".")[0].upper()] = slug
            for c in fm.get("atc_codes") or []:
                out["atc"][str(c).upper()] = slug
    return out


def find_duplicate(title: str, slug: str, existing: dict, code: str | None = None,
                   planned_slugs: set | None = None) -> str | None:
    if slug in existing["slugs"]:
        return slug
    if code and code in ALIASES and (ALIASES[code] in existing["slugs"] or ALIASES[code] in (planned_slugs or set())):
        return ALIASES[code]
    nt = norm_title(title)
    if nt in existing["titles"]:
        return existing["titles"][nt]
    if len(nt) >= 6:
        for et, es in existing["titles"].items():
            if SequenceMatcher(None, nt, et).ratio() >= 0.9:
                return es
    return None


# ---------------------------------------------------------------------------
# ICD-10-GM + Eurostat
# ---------------------------------------------------------------------------
def load_icd(repo: Path):
    d = repo / ICD_DIR
    chapters = {}
    for line in (d / "icd10gm2026syst_kapitel.txt").read_text(encoding="utf-8").splitlines():
        a = line.split(";")
        if len(a) >= 2:
            chapters[a[0]] = a[1]
    cats, subcount = {}, defaultdict(int)
    for line in (d / "icd10gm2026syst_kodes.txt").read_text(encoding="utf-8").splitlines():
        f = line.split(";")
        if len(f) < 9:
            continue
        level, chap = f[0], f[3]
        if level == "3":
            cats[f[7][:3]] = {"code": f[7][:3], "title": f[8].strip(), "chapter": chap}
        elif level in ("4", "5"):
            subcount[f[7][:3]] += 1
    return chapters, cats, subcount


def _expand(spec: str) -> list[tuple[str, str]]:
    ranges = []
    for part in spec.split("_"):
        if re.fullmatch(r"[A-Z]\d{2}-[A-Z]\d{2}", part):
            ranges.append((part[:3], part[4:]))
        elif re.fullmatch(r"[A-Z]\d{2}", part):
            ranges.append((part, part))
    return ranges


def eurostat_groups(raw: dict) -> list[dict]:
    """Aus der JSON-stat-Antwort Gruppen mit Entlassungszahl (jüngstes Jahr) bauen."""
    idx = raw["dimension"]["icd10"]["category"]["index"]
    labels = raw["dimension"]["icd10"]["category"]["label"]
    sizes, ids = raw["size"], raw["id"]
    time_dim = raw["dimension"]["time"]["category"]["index"]
    stride, acc = {}, 1
    for dim, size in reversed(list(zip(ids, sizes))):
        stride[dim] = acc
        acc *= size
    def filled(year: str) -> int:
        return sum(1 for pos in idx.values() if str(pos * stride["icd10"] + time_dim[year] * stride["time"]) in raw["value"])

    latest = next(y for y in sorted(time_dim, reverse=True) if filled(y) >= len(idx) // 2)
    out = []
    for key, pos in idx.items():
        flat = pos * stride["icd10"] + time_dim[latest] * stride["time"]
        val = raw["value"].get(str(flat))
        if val is None:
            continue
        out.append({"key": key, "label": labels[key], "value": val, "year": latest})
    return out


PARENT_KEYS = {"C00-D48", "D00-D48", "D50-D89", "H00-H59", "H60-H95"}


def eurostat_scores(groups: list[dict], codes: list[str]) -> dict[str, float]:
    """Je ICD3-Code: Entlassungen der kleinsten umfassenden Eurostat-Gruppe / Zahl ihrer Dreisteller.

    Bevorzugt werden spezifische Gruppen, danach Restgruppen (*_OTH), zuletzt Kapitel-/Elterngruppen.
    """
    specs = []
    for g in groups:
        k = g["key"]
        if k.startswith("A-T") or "XNB" in k:
            continue
        oth = k.endswith("_OTH")
        base = k[:-4] if oth else k
        if re.fullmatch(r"[A-Z](_[A-Z])*", base):  # Kapitelbuchstaben (E, A_B, ...)
            ranges = [(f"{c}00", f"{c}99") for c in base.split("_")]
            tier = 2
        else:
            ranges = _expand(base)
            tier = 2 if base in PARENT_KEYS else (1 if oth else 0)
        if not ranges:
            continue
        members = {c for c in codes if any(lo <= c <= hi for lo, hi in ranges)}
        if members:
            specs.append({"value": g["value"], "members": members, "tier": tier, "n": len(members)})
    score = {}
    for c in codes:
        cand = [s for s in specs if c in s["members"]]
        if not cand:
            continue
        best_tier = min(s["tier"] for s in cand)
        best = min((s for s in cand if s["tier"] == best_tier), key=lambda s: s["n"])
        score[c] = best["value"] / best["n"]
    return score


def build_diseases(repo: Path, existing: dict, groups: list[dict], planned_slugs: set | None = None) -> list[dict]:
    chapters, cats, subcount = load_icd(repo)
    codes = sorted(cats)
    fscore = eurostat_scores(groups, codes) if groups else {}
    vals = sorted(fscore.values())

    def pct(v: float) -> float:
        if not vals:
            return 0.0
        return sum(1 for x in vals if x <= v) / len(vals)

    items = []
    for code in codes:
        c = cats[code]
        chap = c["chapter"]
        title = c["title"]
        if chap in EXCLUDED_CHAPTERS and code not in KEEP_U:
            continue
        clean = "".join(" " if ch in TITLE_BAD_CHARS else ch for ch in title)
        clean = re.sub(r"\s+", " ", clean).strip()
        slug = slugify(clean)
        base = 60 * pct(fscore.get(code, 0.0)) + min(8.0, 2.0 * math.log1p(subcount.get(code, 0)))
        if RESIDUAL_RE.search(title):
            base -= 20
        if STAR_RE.search(title):
            base -= 35  # Sternschlüsselnummern (Manifestationen): keine eigenständigen Artikel
        if chap in ("19", "18"):
            base -= 10
        dup = find_duplicate(clean, slug, existing, code, planned_slugs)
        items.append({"code": code, "title": clean, "icd_title": title, "slug": slug,
                      "specialty": code_specialty(code, chap), "chapter": chap,
                      "priority": round(base, 2), "covered_by": dup})
    return items


# ---------------------------------------------------------------------------
# ATC (nur Code + Name) und EMA
# ---------------------------------------------------------------------------
ATC_LINE = re.compile(r"^\s*([A-Z]\d{2}[A-Z]{2}\d{2})\s{2,}(\S.*?)(?:\s{3,}.*)?$")
COMBO_RE = re.compile(r"( und |,|kombination|andere| mit |\bzur\b|\bin\b|impfstoff|haemophilus|diphtherie|tetanus|pertussis|poliomyelitis|antigen|virus|toxoid|vakzin|allergen)", re.I)
COMMON_ATC = ("C02", "C03", "C07", "C08", "C09", "C10", "A02", "A10", "B01", "N02", "N03", "N05", "N06", "J01", "R03", "H02", "M01", "L04", "G03")


def parse_atc_text(text: str) -> dict[str, dict]:
    subs: dict[str, dict] = {}
    for line in text.splitlines():
        m = ATC_LINE.match(line)
        if not m:
            continue
        code, name = m.group(1), m.group(2).strip().rstrip("*").strip()
        if COMBO_RE.search(name) or len(name) < 3 or name.isupper():
            continue
        e = subs.setdefault(name, {"name": name, "codes": []})
        e["codes"].append(code)
    return subs


def load_ema(path: Path) -> list[dict]:
    import openpyxl
    ws = openpyxl.load_workbook(str(path), read_only=True).active
    rows = list(ws.iter_rows(values_only=True))
    hdr = None
    for i, r in enumerate(rows):
        if r and r[0] == "Category":
            hdr = i
            break
    if hdr is None:
        raise RuntimeError("EMA-Tabelle: Kopfzeile nicht gefunden")
    heads = {str(n).split("\n")[0].strip(): j for j, n in enumerate(rows[hdr]) if n}

    def col(prefix: str) -> int:
        return next(j for h, j in heads.items() if h.startswith(prefix))

    cols = {"Category": col("Category"), "Medicine status": col("Medicine status"), "Name of medicine": col("Name of medicine"),
            "ATC code (human)": col("ATC code (human)"), "INN": col("International non-proprietary name"),
            "EMA product number": col("EMA product number")}
    out = []
    for r in rows[hdr + 1:]:
        if not r or r[cols["Category"]] != "Human":
            continue
        status = str(r[cols["Medicine status"]] or "")
        if status != "Authorised":
            continue
        name = str(r[cols["Name of medicine"]] or "")
        name = re.sub(r"\s*\(previously.*?\)", "", name).strip()
        out.append({"name": name, "atc": str(r[cols["ATC code (human)"]] or "").strip(),
                    "inn": str(r[cols["INN"]] or "").strip().lower(),
                    "product": str(r[cols["EMA product number"]] or "")})
    return out


def build_drugs(existing: dict, atc: dict[str, dict], ema: list[dict]) -> list[dict]:
    by_atc = defaultdict(list)
    for p in ema:
        by_atc[p["atc"]].append(p)
    items = []
    by_slug: dict[str, dict] = {}
    for name, e in atc.items():  # gleiche Slugs (Schreibvarianten) zusammenführen
        slug = slugify(re.sub(r"\s+", " ", name))
        if not slug:
            continue
        if slug in by_slug:
            by_slug[slug]["codes"] += e["codes"]
        else:
            by_slug[slug] = {"name": re.sub(r"\s+", " ", name), "codes": list(e["codes"])}
    for slug, e in by_slug.items():
        title = e["name"]
        nprod = sum(len(by_atc.get(c, [])) for c in e["codes"])
        group_w = {"C": 8, "N": 8, "A": 7, "J": 8, "L": 7, "M": 6, "R": 6, "B": 7, "G": 5, "H": 6, "S": 4, "D": 4, "P": 3, "V": 1}
        prio = 30 * min(1.0, math.log1p(nprod) / math.log(40)) + group_w.get(e["codes"][0][0], 3) * 3
        if any(c.startswith(COMMON_ATC) for c in e["codes"]):
            prio += 18
        dup = find_duplicate(title, slug, existing) or next((existing["atc"][c] for c in e["codes"] if c in existing["atc"]), None)
        items.append({"code": e["codes"][0], "codes": e["codes"], "title": title, "slug": slug, "specialty": "Pharmakologie",
                      "priority": round(prio, 2), "covered_by": dup, "ema_products": nprod})
    return items


def build_trade(drugs: list[dict], ema: list[dict], existing: dict) -> list[dict]:
    drug_by_atc = {}
    for d in drugs:
        if d["covered_by"]:
            target = d["covered_by"]
        else:
            target = d["slug"]
        for c in d["codes"]:
            drug_by_atc[c] = (d["title"], target)
    items, seen = [], set()
    for p in ema:
        tgt = drug_by_atc.get(p["atc"])
        if not tgt:
            continue
        name = re.sub(r"[#<>\[\]|{}:/]", " ", p["name"]).strip()
        slug = slugify(name)
        if not slug or slug in seen or slug in existing["slugs"] or slug == tgt[1]:
            continue
        inn = re.split(r"[,/]", p["inn"])[0].strip().lower()
        if inn and name.lower().startswith(inn.split()[0]):
            continue  # Generikum mit Wirkstoffnamen im Produktnamen: kein eigenständiger Handelsname
        seen.add(slug)
        items.append({"code": p["product"], "title": name, "slug": slug, "specialty": "Pharmakologie", "priority": 1.0,
                      "target_title": tgt[0], "target_slug": tgt[1], "atc": p["atc"], "covered_by": None})
    return items


# ---------------------------------------------------------------------------
# Backlog-Dateien mit stabilen IDs
# ---------------------------------------------------------------------------
def assign_ids(path: Path, prefix: str, start: int, items: list[dict], key: str = "code") -> list[dict]:
    old = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                old[r[key] + "|" + r["slug"]] = r["id"]
    nums = [int(v.rsplit("-", 1)[1]) for v in old.values()] or [start - 1]
    nxt = max(nums) + 1
    for it in sorted(items, key=lambda x: -x["priority"]):
        k = it[key] + "|" + it["slug"]
        if k in old:
            it["id"] = old[k]
        else:
            it["id"] = f"{prefix}-{nxt:04d}"
            nxt += 1
    return sorted(items, key=lambda x: x["id"])


def write_jsonl(path: Path, items: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(i, ensure_ascii=False, sort_keys=True) + "\n" for i in items), encoding="utf-8")



LAUNCH_ROW = re.compile(r"^\|\s*(WM-DIS-\d{4})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([AB])\s*\|")
AREA_SPECIALTY = {
    "Kardiologie und Gefäßmedizin": "Kardiologie", "Endokrinologie und Stoffwechsel": "Endokrinologie/Diabetologie",
    "Pneumologie und HNO": "Pneumologie", "Neurologie und Psychiatrie": "Neurologie", "Gastroenterologie": "Gastroenterologie",
    "Nephrologie und Urologie": "Nephrologie", "Orthopädie, Rheumatologie und Dermatologie": "Rheumatologie",
    "Infektiologie": "Infektiologie", "Frauenheilkunde und Gendermedizin": "Gynäkologie/Geburtshilfe",
    "Weitere häufige oder versorgungsrelevante Themen": "Innere Medizin",
}
SPECIALTY_HINTS = [("depress", "Psychiatrie"), ("angst", "Psychiatrie"), ("bipolar", "Psychiatrie"), ("schizophren", "Psychiatrie"),
                   ("alkohol", "Psychiatrie"), ("aufmerksamkeit", "Psychiatrie"), ("insomnie", "Psychiatrie"),
                   ("ekzem", "Dermatologie"), ("psoriasis", "Dermatologie"), ("akne", "Dermatologie"), ("glaukom", "Augenheilkunde"),
                   ("makula", "Augenheilkunde"), ("karzinom", "Hämatologie/Onkologie"), ("anämie", "Hämatologie/Onkologie"),
                   ("harnweg", "Urologie"), ("prostata", "Urologie"), ("inkontinenz", "Urologie"), ("urolith", "Urologie"),
                   ("sepsis", "Intensivmedizin"), ("schlaganfall", "Neurologie"), ("hypertonie", "Kardiologie")]


def build_launch(repo: Path, existing: dict) -> list[dict]:
    """Noch nicht vorhandene Themen aus docs/editorial/launch-100-erkrankungen.md (feste IDs WM-DIS-0001 bis 0100)."""
    doc = repo / "docs/editorial/launch-100-erkrankungen.md"
    items = []
    if not doc.exists():
        return items
    for i, line in enumerate(doc.read_text(encoding="utf-8").splitlines()):
        m = LAUNCH_ROW.match(line)
        if not m:
            continue
        wid, title, area, prio = m.groups()
        slug = slugify(title)
        if find_duplicate(title, slug, existing):
            continue
        spec = AREA_SPECIALTY.get(area, "Innere Medizin")
        for key, sp in SPECIALTY_HINTS:
            if key in title.lower():
                spec = sp
                break
        items.append({"id": wid, "code": wid, "title": title, "slug": slug, "specialty": spec,
                      "priority": 300 + (30 if prio == "A" else 0) - i * 0.01, "covered_by": None})
    return items


def cmd_build(a) -> int:
    repo = Path(a.repo)
    existing = scan_existing(repo)
    log(f"Vorhandene Artikel: {len(existing['slugs'])}")
    # Eurostat
    es_path = repo / "data/catalogs/eurostat-hlth_co_disch2-DE.json"
    if a.eurostat_json:
        raw = json.loads(Path(a.eurostat_json).read_text(encoding="utf-8"))
    elif es_path.exists() and not a.refresh:
        raw = json.loads(es_path.read_text(encoding="utf-8"))
    else:
        raw = http_get_json(EUROSTAT_URL)
        es_path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    groups = eurostat_groups(raw)
    launch = build_launch(repo, existing)
    write_jsonl(repo / BACKLOG_DIR / "diseases-launch100.jsonl", launch)
    log(f"Launch-Liste: {len(launch)} Themen noch ohne Artikel")
    dis = build_diseases(repo, existing, groups, {x["slug"] for x in launch})
    dis = assign_ids(repo / BACKLOG_DIR / "diseases-icd10gm2026.jsonl", "WM-DIS", 101, dis)
    write_jsonl(repo / BACKLOG_DIR / "diseases-icd10gm2026.jsonl", dis)
    log(f"Erkrankungen: {len(dis)} Kategorien, davon vorhanden {sum(1 for d in dis if d['covered_by'])}")
    if a.atc_txt and a.ema_xlsx:
        atc = parse_atc_text(Path(a.atc_txt).read_text(encoding="utf-8"))
        ema = load_ema(Path(a.ema_xlsx))
        drugs = build_drugs(existing, atc, ema)
        drugs = assign_ids(repo / BACKLOG_DIR / "wirkstoffe-atc-gm2026.jsonl", "WM-DRUG", 101, drugs)
        write_jsonl(repo / BACKLOG_DIR / "wirkstoffe-atc-gm2026.jsonl", drugs)
        trade = build_trade(drugs, ema, existing)
        trade = assign_ids(repo / BACKLOG_DIR / "handelsnamen-ema.jsonl", "WM-TRADE", 1, trade)
        write_jsonl(repo / BACKLOG_DIR / "handelsnamen-ema.jsonl", trade)
        log(f"Wirkstoffe: {len(drugs)} (vorhanden {sum(1 for d in drugs if d['covered_by'])}); Handelsnamen: {len(trade)}")
    return 0


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def cmd_load_queue(a) -> int:
    repo = Path(a.repo)
    q = Queue(Path(a.state_dir))
    existing = scan_existing(repo)
    total = 0
    for fname, kind in (("diseases-launch100.jsonl", "disease"), ("diseases-icd10gm2026.jsonl", "disease"), ("wirkstoffe-atc-gm2026.jsonl", "drug"),
                        ("handelsnamen-ema.jsonl", "trade")):
        batch = []
        for r in read_jsonl(repo / BACKLOG_DIR / fname):
            dup = r["slug"] in existing["slugs"] or r.get("covered_by")
            extra = {k: r[k] for k in ("code", "codes", "icd_title", "chapter", "target_title", "target_slug", "atc") if k in r}
            batch.append({"id": r["id"], "kind": kind, "title": r["title"], "slug": r["slug"], "specialty": r["specialty"],
                          "priority": r["priority"], "extra": extra, "status": "duplicate" if dup else "planned"})
        n = q.add_items(batch)
        total += n
        log(f"{kind}: {n} neu in der Warteschlange")
    log(f"Warteschlange: {q.counts()}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--repo", required=True)
    b.add_argument("--eurostat-json")
    b.add_argument("--refresh", action="store_true")
    b.add_argument("--ema-xlsx")
    b.add_argument("--atc-txt")
    b.set_defaults(fn=cmd_build)
    l = sub.add_parser("load-queue")
    l.add_argument("--repo", required=True)
    l.add_argument("--state-dir", required=True)
    l.set_defaults(fn=cmd_load_queue)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
