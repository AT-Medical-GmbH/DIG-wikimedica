#!/usr/bin/env python3
"""Recherchestufe der WikiMedica-Redaktionspipeline (nur lesende Abrufe, kostenfrei).

* PubMed E-Utilities: Leitlinien (letzte 10 Jahre), Metaanalysen und systematische Übersichtsarbeiten
  (letzte 5 Jahre), Übersichtsarbeiten (letzte 5 Jahre). Zurückgezogene Arbeiten werden verworfen.
* PubMed Central Open Access: Volltextauszüge, wenn die Lizenz „Creative Commons“ ausweist.
* Verifikation: jede PMID wird gegen PubMed aufgelöst; nur dort gefundene Quellen dürfen zitiert werden.
* AWMF-Leitlinienregister: bietet keine dokumentierte öffentliche Schnittstelle (Angular-Anwendung);
  Verweise kommen deshalb nur aus der gepflegten Datei data/editorial/awmf-leitlinien.json (optional).

NCBI-Nutzungsregeln: höchstens 3 Anfragen/s ohne Schlüssel (hier höchstens 2,5/s), Kennung ``tool``/``email``.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

from wm_common import UA, http_get, log

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TOOL = "wikimedica-editorial"
EMAIL = "redaktion@at-medical.de"
_last = 0.0
_MIN_GAP = 0.4 if not os.environ.get("NCBI_API_KEY") else 0.12
RETRACTED = {"Retracted Publication", "Retraction of Publication"}


def eutils(endpoint: str, **params) -> bytes:
    """Eine E-Utilities-Anfrage mit Abstandshaltung und Wiederholung bei 429/5xx."""
    global _last
    params.update({"tool": TOOL, "email": EMAIL})
    if os.environ.get("NCBI_API_KEY"):
        params["api_key"] = os.environ["NCBI_API_KEY"]
    url = f"{EUTILS}/{endpoint}?{urllib.parse.urlencode(params)}"
    for attempt in range(5):
        wait = _MIN_GAP - (time.time() - _last)
        if wait > 0:
            time.sleep(wait)
        _last = time.time()
        try:
            return http_get(url, timeout=90)
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < 4:
                time.sleep(3 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if attempt < 4:
                time.sleep(3 * (attempt + 1))
                continue
            raise
    raise RuntimeError("E-Utilities nicht erreichbar")


def esearch(term: str, retmax: int = 20, years: int | None = None) -> list[str]:
    params = {"db": "pubmed", "term": term, "retmax": retmax, "retmode": "json", "sort": "relevance"}
    if years:
        params.update({"datetype": "pdat", "mindate": str(date.today().year - years), "maxdate": "3000"})
    data = json.loads(eutils("esearch.fcgi", **params).decode("utf-8"))
    return data.get("esearchresult", {}).get("idlist", [])


def _text(el: ET.Element | None) -> str:
    return "".join(el.itertext()).strip() if el is not None else ""


def parse_pubmed_xml(xml: bytes) -> dict[str, dict]:
    root = ET.fromstring(xml)
    out: dict[str, dict] = {}
    for art in root.findall(".//PubmedArticle"):
        pmid = (art.findtext(".//MedlineCitation/PMID") or "").strip()
        title = _text(art.find(".//ArticleTitle"))
        parts = []
        for t in art.findall(".//Abstract/AbstractText"):
            label = t.get("Label")
            parts.append((f"{label}: " if label else "") + _text(t))
        abstract = " ".join(p for p in parts if p.strip())
        ptypes = {_text(p) for p in art.findall(".//PublicationTypeList/PublicationType")}
        year = (art.findtext(".//JournalIssue/PubDate/Year") or art.findtext(".//ArticleDate/Year")
                or (art.findtext(".//JournalIssue/PubDate/MedlineDate") or "")[:4]).strip()
        ids = {i.get("IdType"): _text(i) for i in art.findall(".//PubmedData/ArticleIdList/ArticleId")}
        authors = []
        for a in art.findall(".//AuthorList/Author")[:3]:
            ln, ini = a.findtext("LastName") or "", a.findtext("Initials") or ""
            if ln:
                authors.append(f"{ln} {ini}".strip())
        if not pmid or not title:
            continue
        out[pmid] = {
            "pmid": pmid, "title": title.rstrip("."), "abstract": abstract, "year": year,
            "journal": (art.findtext(".//Journal/ISOAbbreviation") or art.findtext(".//Journal/Title") or "").strip(),
            "volume": (art.findtext(".//JournalIssue/Volume") or "").strip(),
            "pages": (art.findtext(".//Pagination/MedlinePgn") or "").strip(),
            "doi": ids.get("doi", ""), "pmcid": ids.get("pmc", ""), "ptypes": sorted(ptypes),
            "authors": authors, "retracted": bool(ptypes & RETRACTED),
        }
    return out


def efetch_records(pmids: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for i in range(0, len(pmids), 40):
        chunk = pmids[i:i + 40]
        out.update(parse_pubmed_xml(eutils("efetch.fcgi", db="pubmed", id=",".join(chunk), retmode="xml")))
    return out


def verify_pmids(pmids: list[str]) -> set[str]:
    """Gibt die Teilmenge der PMIDs zurück, die PubMed tatsächlich kennt (und die nicht zurückgezogen sind)."""
    good: set[str] = set()
    for pmid, rec in efetch_records(sorted(set(pmids))).items():
        if not rec["retracted"]:
            good.add(pmid)
    return good


def pmc_fulltext(pmcid: str, limit: int = 6000) -> str | None:
    """Textauszug aus PMC, nur bei Creative-Commons-Lizenz (Open Access); sonst None."""
    if not pmcid:
        return None
    try:
        xml = eutils("efetch.fcgi", db="pmc", id=pmcid.replace("PMC", ""), retmode="xml")
        root = ET.fromstring(xml)
    except (urllib.error.URLError, ET.ParseError, TimeoutError):
        return None
    lic = " ".join(_text(x) + " " + " ".join(x.attrib.values()) for x in root.iter("license"))
    if "creativecommons" not in lic.lower() and "creative commons" not in lic.lower():
        return None
    body = root.find(".//body")
    if body is None:
        return None
    prio, rest = [], []
    for sec in body.findall("./sec"):
        title = _text(sec.find("title")).lower()
        txt = " ".join(_text(p) for p in sec.iter("p"))
        (prio if re.search(r"result|conclusion|discussion|recommend|summary|treatment|management", title) else rest).append(
            f"[{_text(sec.find('title'))}] {txt}")
    text = " ".join(prio + rest)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit] or None


def rank_key(rec: dict) -> tuple:
    pt = " ".join(rec["ptypes"]).lower()
    tier = 0 if "guideline" in pt else 1 if ("meta-analysis" in pt or "systematic review" in pt) else 2
    return (tier, -int(rec["year"] or 0))


def gather(term_en: str, term_de: str = "", max_refs: int = 16, fulltexts: int = 3) -> list[dict]:
    """Quellenpaket für ein Thema zusammenstellen."""
    t = term_en.strip()
    ids: list[str] = []

    def collect(field: str) -> None:
        for term, years, n in (
            (f'("{t}"[{field}]) AND (practice guideline[pt] OR guideline[pt])', 10, 8),
            (f'("{t}"[{field}]) AND (meta-analysis[pt] OR systematic review[pt])', 5, 8),
            (f'("{t}"[{field}]) AND (review[pt])', 5, 6),
        ):
            for pmid in esearch(term, retmax=n, years=years):
                if pmid not in ids:
                    ids.append(pmid)

    collect("Title")  # präzise: Begriff im Titel
    # klassische Kapitel (Epidemiologie, Ätiologie, Diagnostik) über MeSH-Unterüberschriften
    for pmid in esearch(f'("{t}/diagnosis"[MeSH Terms] OR "{t}/epidemiology"[MeSH Terms] OR "{t}/etiology"[MeSH Terms] '
                        f'OR "{t}/therapy"[MeSH Terms]) AND (review[pt] OR guideline[pt])', retmax=8, years=5):
        if pmid not in ids:
            ids.append(pmid)
    if len(ids) < 5:
        collect("Title/Abstract")  # breiter, nur wenn zu wenig gefunden
    recs = [r for r in efetch_records(ids).values() if r["abstract"] and not r["retracted"]]
    recs.sort(key=rank_key)
    recs = recs[:max_refs]
    n_ft = 0
    for r in recs:
        r["fulltext"] = None
        if r["pmcid"] and n_ft < fulltexts:
            ft = pmc_fulltext(r["pmcid"])
            if ft:
                r["fulltext"] = ft
                n_ft += 1
    log(f"Recherche '{t}': {len(recs)} Quellen, {n_ft} PMC-Volltextauszüge")
    return recs


_AWMF_FILE = Path(__file__).resolve().parents[2] / "data/editorial/awmf-leitlinien.json"


def awmf_guidelines(slug: str) -> list[dict]:
    """Gepflegte AWMF-Verweise je Artikel-Slug (optional)."""
    try:
        return json.loads(_AWMF_FILE.read_text(encoding="utf-8")).get(slug, [])
    except (OSError, json.JSONDecodeError):
        return []


def citation(rec: dict) -> str:
    authors = ", ".join(rec["authors"]) + (" et al." if len(rec["authors"]) >= 3 else "")
    bits = [f"{authors}. " if authors else "", f"{rec['title']}. ", f"{rec['journal']}. " if rec["journal"] else "",
            f"{rec['year']}" if rec["year"] else ""]
    if rec["volume"]:
        bits.append(f";{rec['volume']}")
    if rec["pages"]:
        bits.append(f":{rec['pages']}")
    return ("".join(bits)).strip().rstrip(".") + "."
