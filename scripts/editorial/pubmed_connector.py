#!/usr/bin/env python3
"""Sparsamer, nachvollziehbarer PubMed-Quellenabruf für WikiMedica.

Der Connector ruft nur bibliographische Metadaten über die offizielle NCBI
E-Utilities-Schnittstelle ab. Er erstellt keine medizinischen Aussagen und
stuft Quellen niemals automatisch als fachlich verifiziert ein. Ergebnisse
werden lokal gecacht, damit identische Anfragen keine unnötigen Fremdaufrufe
oder Modellkapazität verbrauchen.
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
MAX_REQUESTS_PER_SECOND = 2
DEFAULT_RETMAX = 20


class PubMedError(RuntimeError):
    """Ein kontrolliert behandelbarer Fehler des externen Quellenabrufs."""


def timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class PubMedConnector:
    def __init__(self, contact_email: str, tool_name: str = "wikimedica_editorial_agent") -> None:
        contact_email = contact_email.strip()
        if "@" not in contact_email:
            raise PubMedError("Eine dienstliche NCBI-Kontaktadresse ist erforderlich.")
        self.contact_email = contact_email
        self.tool_name = tool_name
        self._last_request = 0.0

    def _request(self, endpoint: str, params: dict[str, str]) -> dict[str, Any]:
        interval = 1 / MAX_REQUESTS_PER_SECOND
        remaining = interval - (time.monotonic() - self._last_request)
        if remaining > 0:
            time.sleep(remaining)
        query = {
            **params,
            "db": "pubmed",
            "retmode": "json",
            "tool": self.tool_name,
            "email": self.contact_email,
        }
        url = f"{BASE_URL}/{endpoint}?{urllib.parse.urlencode(query)}"
        request = urllib.request.Request(url, headers={"User-Agent": "WikiMedica-Editorial-Agent/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                if response.status != 200:
                    raise PubMedError(f"NCBI lieferte HTTP {response.status}.")
                raw = response.read()
        except (OSError, TimeoutError) as exc:
            raise PubMedError(f"NCBI ist derzeit nicht erreichbar: {exc}") from exc
        finally:
            self._last_request = time.monotonic()
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PubMedError("NCBI lieferte keine gültige JSON-Antwort.") from exc
        if isinstance(payload, dict) and payload.get("error"):
            raise PubMedError(f"NCBI-Fehler: {payload['error']}")
        return payload

    def search(self, query: str, retmax: int = DEFAULT_RETMAX) -> dict[str, Any]:
        """Liefert eine kleine zitierbare Kandidatenmenge samt Query-Provenienz."""
        query = query.strip()
        if not query:
            raise PubMedError("Die PubMed-Suchanfrage darf nicht leer sein.")
        if not 1 <= retmax <= 50:
            raise PubMedError("retmax muss zwischen 1 und 50 liegen.")
        found = self._request("esearch.fcgi", {"term": query, "retmax": str(retmax), "sort": "pub+date"})
        result = found.get("esearchresult", {})
        ids = [str(item) for item in result.get("idlist", [])]
        citations: list[dict[str, Any]] = []
        if ids:
            summary = self._request("esummary.fcgi", {"id": ",".join(ids)})
            records = summary.get("result", {})
            for pmid in ids:
                record = records.get(pmid, {})
                if not isinstance(record, dict):
                    continue
                citations.append({
                    "pmid": pmid,
                    "title": record.get("title"),
                    "source": record.get("source"),
                    "pubdate": record.get("pubdate"),
                    "authors": [a.get("name") for a in record.get("authors", []) if isinstance(a, dict) and a.get("name")],
                    "doi": next((x.get("value") for x in record.get("articleids", []) if isinstance(x, dict) and x.get("idtype") == "doi"), None),
                    "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                })
        return {
            "source": "NCBI PubMed E-Utilities",
            "retrieved_at": timestamp(),
            "query": query,
            "total_hits": int(result.get("count", 0)),
            "citations": citations,
            "limitations": [
                "Automatisch abgerufene bibliographische Metadaten sind keine fachliche Quellenprüfung.",
                "Therapieaussagen dürfen nicht allein auf Abstracts oder Metadaten gestützt werden.",
            ],
        }


def cached_search(connector: PubMedConnector, article_id: str, query: str, cache_dir: Path) -> Path:
    """Schreibt einen atomaren, artikelbezogenen Quellen-Snapshot."""
    cache_dir.mkdir(mode=0o750, parents=True, exist_ok=True)
    target = cache_dir / f"{article_id}.pubmed.json"
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(connector.search(query), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    return target
