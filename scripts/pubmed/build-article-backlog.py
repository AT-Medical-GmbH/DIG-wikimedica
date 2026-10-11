#!/usr/bin/env python3
"""Build a canonical PubMed literature index and a deterministic article backlog."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:
    raise SystemExit("ERROR: pyyaml is required: pip install pyyaml") from exc

PUBMED_DIR = Path("data/pubmed")
CONTENT_DIR = Path("content")
LITERATURE_DIR = Path("data/literature")
REPORT_PATH = Path("reports/generated/literature-article-backlog.md")
EXCLUDED_JSONL = {"pending-review.jsonl"}

GENERIC_MESH = {
    "Humans", "Male", "Female", "Adult", "Young Adult", "Middle Aged", "Aged",
    "Aged, 80 and over", "Child", "Child, Preschool", "Infant", "Infant, Newborn",
    "Adolescent", "Animals", "Prospective Studies", "Retrospective Studies",
    "Treatment Outcome", "Risk Factors", "Time Factors", "Prevalence", "Incidence",
    "Follow-Up Studies", "Cohort Studies", "Cross-Sectional Studies",
    "Randomized Controlled Trials as Topic",
}

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
CLASS_RANK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}


def normalise_text(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9äöüß]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def mesh_descriptor(raw: str) -> str:
    value = raw.strip().lstrip("*")
    return value.split("/", 1)[0].strip()


def iter_pubmed_records(pubmed_dir: Path):
    for path in sorted(pubmed_dir.glob("*.jsonl")):
        if path.name in EXCLUDED_JSONL:
            continue
        with path.open(encoding="utf-8") as fh:
            for line_number, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise SystemExit(f"Invalid JSON in {path}:{line_number}: {exc}") from exc
                pmid = str(record.get("pmid", "")).strip()
                if pmid:
                    yield path, record


def merge_record(existing: dict[str, Any] | None, incoming: dict[str, Any], source_file: str) -> dict[str, Any]:
    if existing is None:
        existing = {
            "pmid": str(incoming.get("pmid", "")),
            "title": incoming.get("title", ""),
            "authors": incoming.get("authors", []),
            "journal": incoming.get("journal", ""),
            "year": incoming.get("year"),
            "publication_date": incoming.get("publication_date", ""),
            "publication_types": [],
            "mesh_terms": [],
            "specialty_tags": [],
            "language": incoming.get("language", ""),
            "doi": incoming.get("doi"),
            "pubmed_url": incoming.get("pubmed_url", ""),
            "relevance_score": 0,
            "relevance_class": "LOW",
            "source": "pubmed",
            "source_files": [],
        }

    for key in ("title", "authors", "journal", "year", "publication_date", "language", "doi", "pubmed_url"):
        if not existing.get(key) and incoming.get(key):
            existing[key] = incoming[key]

    for key in ("publication_types", "mesh_terms", "specialty_tags"):
        merged = set(existing.get(key, []))
        merged.update(incoming.get(key, []) or [])
        existing[key] = sorted(merged)

    incoming_score = int(incoming.get("relevance_score") or 0)
    if incoming_score > int(existing.get("relevance_score") or 0):
        existing["relevance_score"] = incoming_score

    incoming_class = str(incoming.get("relevance_class") or "LOW").upper()
    if CLASS_RANK.get(incoming_class, 0) > CLASS_RANK.get(existing.get("relevance_class", "LOW"), 0):
        existing["relevance_class"] = incoming_class

    if source_file not in existing["source_files"]:
        existing["source_files"].append(source_file)
        existing["source_files"].sort()

    return existing


def load_canonical_index(pubmed_dir: Path) -> dict[str, dict[str, Any]]:
    by_pmid: dict[str, dict[str, Any]] = {}
    for path, record in iter_pubmed_records(pubmed_dir):
        pmid = str(record["pmid"]).strip()
        by_pmid[pmid] = merge_record(by_pmid.get(pmid), record, path.name)
    return by_pmid


def load_existing_articles(content_dir: Path) -> list[dict[str, str]]:
    articles: list[dict[str, str]] = []
    if not content_dir.exists():
        return articles
    for path in sorted(content_dir.rglob("*.md")):
        if path.name.lower() == "readme.md" or "templates" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        match = FRONTMATTER_RE.match(text)
        if not match:
            continue
        try:
            fm = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            continue
        title = str(fm.get("title") or "").strip()
        slug = str(fm.get("slug") or path.stem).strip()
        if title:
            articles.append({"title": title, "slug": slug, "path": str(path)})
    return articles


def possible_article_matches(topic: str, articles: list[dict[str, str]]) -> list[dict[str, str]]:
    norm_topic = normalise_text(topic)
    if len(norm_topic) < 5:
        return []
    matches: list[dict[str, str]] = []
    for article in articles:
        norm_title = normalise_text(article["title"])
        if norm_topic == norm_title or norm_topic in norm_title or norm_title in norm_topic:
            matches.append(article)
    return matches[:10]


def publication_design_counts(record: dict[str, Any]) -> Counter:
    types = {str(x) for x in record.get("publication_types", [])}
    result = Counter()
    if {"Practice Guideline", "Guideline"} & types:
        result["guideline"] += 1
    if {"Meta-Analysis", "Systematic Review"} & types:
        result["systematic"] += 1
    if "Randomized Controlled Trial" in types:
        result["rct"] += 1
    return result


def cluster_candidates(index: dict[str, dict[str, Any]], existing_articles: list[dict[str, str]]) -> list[dict[str, Any]]:
    clusters: dict[str, dict[str, Any]] = {}

    for pmid, record in index.items():
        descriptors = []
        for raw in record.get("mesh_terms", []) or []:
            descriptor = mesh_descriptor(str(raw))
            if descriptor and descriptor not in GENERIC_MESH:
                descriptors.append(descriptor)

        for topic in sorted(set(descriptors)):
            cluster = clusters.setdefault(topic, {
                "topic": topic,
                "pmids": [],
                "specialties": set(),
                "journals": set(),
                "years": [],
                "high_count": 0,
                "medium_count": 0,
                "design_counts": Counter(),
                "score": 0.0,
            })
            cluster["pmids"].append(pmid)
            cluster["specialties"].update(record.get("specialty_tags", []) or [])
            if record.get("journal"):
                cluster["journals"].add(record["journal"])
            if isinstance(record.get("year"), int):
                cluster["years"].append(record["year"])

            relevance_class = record.get("relevance_class", "LOW")
            if relevance_class == "HIGH":
                cluster["high_count"] += 1
                cluster["score"] += 4.0
            elif relevance_class == "MEDIUM":
                cluster["medium_count"] += 1
                cluster["score"] += 2.0
            else:
                cluster["score"] += 0.5

            designs = publication_design_counts(record)
            cluster["design_counts"].update(designs)
            cluster["score"] += 4.0 * designs["guideline"]
            cluster["score"] += 3.0 * designs["systematic"]
            cluster["score"] += 2.0 * designs["rct"]

    candidates = []
    for topic, cluster in clusters.items():
        paper_count = len(set(cluster["pmids"]))
        if paper_count == 0:
            continue

        cluster["score"] += 2.0 * math.log2(paper_count + 1)
        cluster["score"] += min(5.0, 0.5 * len(cluster["journals"]))
        matches = possible_article_matches(topic, existing_articles)

        candidates.append({
            "topic": topic,
            "specialties": sorted(cluster["specialties"]),
            "paper_count": paper_count,
            "high_count": cluster["high_count"],
            "medium_count": cluster["medium_count"],
            "guideline_count": cluster["design_counts"]["guideline"],
            "systematic_review_or_meta_analysis_count": cluster["design_counts"]["systematic"],
            "rct_count": cluster["design_counts"]["rct"],
            "journal_count": len(cluster["journals"]),
            "latest_year": max(cluster["years"]) if cluster["years"] else None,
            "priority_score": round(cluster["score"], 2),
            "action_hint": "review_existing_article" if matches else "new_article_candidate",
            "possible_article_matches": matches,
            "pmids": sorted(set(cluster["pmids"]), key=lambda x: int(x) if x.isdigit() else x),
        })

    return sorted(candidates, key=lambda x: (-x["priority_score"], -x["paper_count"], x["topic"].lower()))


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def build_report(index: dict[str, dict[str, Any]], candidates: list[dict[str, Any]], top_n: int, min_publications: int) -> str:
    filtered = [c for c in candidates if c["paper_count"] >= min_publications][:top_n]
    latest_year = max((r.get("year") or 0 for r in index.values()), default=0)
    lines = [
        "# WikiMedica Literature-to-Article Backlog",
        "",
        "> Deterministisch aus dem PubMed-Korpus erzeugt. Der Score ist ein Redaktionssignal, kein Evidenzgrad.",
        "",
        f"**Eindeutige PubMed-Datensätze:** {len(index)}  ",
        f"**Jüngstes Publikationsjahr im Korpus:** {latest_year or 'n/a'}  ",
        f"**Angezeigte Kandidaten:** {len(filtered)} (mindestens {min_publications} Publikationen pro Thema)",
        "",
        "| Rang | Thema (MeSH) | Papers | HIGH | Guidelines | Systematic/Meta | RCT | Latest | Score | Aktion |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for rank, c in enumerate(filtered, start=1):
        lines.append(
            f"| {rank} | {c['topic'].replace('|', '/')} | {c['paper_count']} | "
            f"{c['high_count']} | {c['guideline_count']} | "
            f"{c['systematic_review_or_meta_analysis_count']} | {c['rct_count']} | "
            f"{c['latest_year'] or ''} | {c['priority_score']:.2f} | {c['action_hint']} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "- Hoher Score bedeutet: im Korpus liegt ein relativ großer bzw. methodisch relevanter Quellencluster vor.",
        "- MeSH-Synonyme und Ober-/Unterbegriffe müssen redaktionell konsolidiert werden.",
        "- Vor einem Artikelentwurf sind aktuelle Leitlinien, regulatorische Quellen und deutsche Epidemiologie zu ergänzen.",
        "- Der Abgleich mit vorhandenen Artikeln ist heuristisch und muss manuell bestätigt werden.",
        "",
        "Siehe docs/pubmed/literature-to-article-agent.md.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pubmed-dir", type=Path, default=PUBMED_DIR)
    parser.add_argument("--content-dir", type=Path, default=CONTENT_DIR)
    parser.add_argument("--literature-dir", type=Path, default=LITERATURE_DIR)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    parser.add_argument("--top", type=int, default=100)
    parser.add_argument("--min-publications", type=int, default=2)
    args = parser.parse_args()

    index = load_canonical_index(args.pubmed_dir)
    articles = load_existing_articles(args.content_dir)
    candidates = cluster_candidates(index, articles)

    write_jsonl(args.literature_dir / "index.jsonl", list(index.values()))
    write_jsonl(args.literature_dir / "article-candidates.jsonl", candidates)

    report = build_report(index, candidates, args.top, args.min_publications)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8")

    print(f"Canonical literature records: {len(index)}")
    print(f"Article candidates: {len(candidates)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
