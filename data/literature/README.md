# WikiMedica Literature Index

Dieses Verzeichnis enthält generierte, deduplizierte bibliografische Metadaten für die redaktionelle Triage.

## Dateien

- index.jsonl — genau ein kanonischer Datensatz pro PubMed-PMID.
- article-candidates.jsonl — thematische Evidenzcluster als Kandidaten für neue Artikel oder Updates.

Die Dateien werden durch scripts/pubmed/build-article-backlog.py erzeugt und nicht manuell gepflegt.

## Source of truth

Die datierten Dateien unter data/pubmed/ bleiben der source-spezifische Audit-Trail. Der Literaturindex ist eine abgeleitete Ansicht für Suche, Clustering, Priorisierung und spätere Artikelzuordnung.

Der kanonische Index enthält absichtlich keine Abstract-Volltexte. Autoren müssen die zugrunde liegende Publikation öffnen und verifizieren, bevor sie als Evidenz in einem WikiMedica-Artikel verwendet wird.

## Redaktionelle Bedeutung

Ein Datensatz in diesem Verzeichnis ist keine Empfehlung, kein Evidenzgrad und keine Publikationsfreigabe. Ein Eintrag in article-candidates.jsonl ist nur ein Priorisierungsvorschlag.

Die Artikelerstellung und Veröffentlichung folgt immer dem normalen WikiMedica-Workflow mit menschlichem Autor, unabhängigem Review und gegebenenfalls Medical-Advisor-Sign-off.

Siehe docs/pubmed/literature-to-article-agent.md.
