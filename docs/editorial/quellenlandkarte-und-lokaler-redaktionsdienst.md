# Quellenlandkarte und lokaler Redaktionsdienst

## Quellen für langfristige Vollständigkeitsplanung

Die folgenden Quellen dienen der Themenpriorisierung, Epidemiologie und Aktualitätsüberwachung. Sie ersetzen nicht die Prüfung der Primärliteratur und dürfen nicht als pauschale Belege für therapeutische Aussagen verwendet werden.

| Quelle | Nutzen | Automatisierbarer Zugang | Lizenz-/Qualitätshinweis |
| --- | --- | --- | --- |
| WHO Global Health Observatory und Global Health Estimates | Globale Mortalität, Morbidität, Behinderung, Alter, Geschlecht und Ländertrends | GHO OData API und Daten-Downloads | Indikator, Jahr, Schätzmethode und Unsicherheit immer mitführen. |
| RKI Gesundheitsberichterstattung des Bundes | Deutschlandbezug: Krankheiten, Risikofaktoren, Versorgung und Monitoring | Veröffentlichungen und Datenbank; Schnittstelle je Datenangebot prüfen | Deutsche Prävalenz nicht unkritisch auf andere Länder übertragen. |
| Eurostat Ursachenstatistik | EU-Vergleiche zu Mortalität, Alter, Geschlecht und ICD-10-Gruppen | Eurostat-Disseminationsdatenbank/API | Todesursachen sind nicht gleich Prävalenz oder Versorgungsbedarf. |
| ICD-10-GM und OPS | Vollständiger strukturierter Backlog für Krankheiten bzw. Prozeduren | Amtliche Veröffentlichungen mit Versionsmanagement | Code ≠ eigenständiger Artikel; Synonyme und klinische Bündelung prüfen. |
| AWMF/NVL, RKI, STIKO, PEI, BfArM, EMA, WHO | Leitlinien, Sicherheitsmeldungen, regulatorische Änderungen | Je Quelle nur dokumentierte Downloads/Feeds/API | Für Therapie- oder Arzneimittelaussagen maßgeblich; Datum und Geltungsbereich erfassen. |
| PubMed/MEDLINE und Cochrane | Primärliteratur und systematische Reviews | Entrez-/E-utilities bzw. lizenzierte Volltexte | Abstract allein nicht als Basis komplexer Empfehlungen verwenden. |

Offizielle Einstiege: [WHO GHE](https://www.who.int/data/global-health-estimates/), [WHO GHO OData API](https://www.who.int/data/gho/info/gho-odata-api), [RKI GBE](https://www.rki.de/DE/Themen/Gesundheit-und-Gesellschaft/Gesundheitsberichterstattung/gesundheitsberichterstattung-node.html), [Eurostat Health](https://ec.europa.eu/eurostat/web/health/information-data).

## Zielarchitektur: lokale Recherche- und Entwurfspipeline

Der Dienst trennt deterministische Datenbeschaffung, lokale Entwurfserstellung und externe Qualitätskontrolle.

```text
offizielle Datenquellen → lokaler Downloader/Normalizer → versionsgespeicherter Quellenkorpus
  → lokaler Retriever (Volltext/Metadaten, Zitierbelege) → lokales Modell → Entwurf mit Quellenanker
  → Schema-/Sicherheitsprüfer → Git-Entwurf/PR → externe KI-QK → menschliche Fachfreigabe
```

### Dienste

1. `wikimedica-source-sync`: systemd-Timer, nur dokumentierte APIs/Downloads; speichert Original, SHA-256, Abrufzeit, Lizenz, URL und Parser-Version.
2. `wikimedica-retriever`: lokale Volltextsuche (zunächst SQLite FTS5; später OpenSearch/Meilisearch nach Messwerten). Er liefert nur nachweisbare Textabschnitte samt Quellenanker.
3. `wikimedica-local-drafter`: unprivilegierter, vom Netz getrennt startbarer Modellprozess. Er darf ausschließlich Retriever-Kontext und Artikelvorlage erhalten; jede klinische Aussage braucht eine belegte Quelle oder wird als unsicher markiert.
4. `wikimedica-qc-gate`: deterministische Prüfungen (YAML, Links, Zitatauflösung, Duplikate, Risikoklasse, verbotene Dosierungs- oder Freigabeformulierungen) und danach optional externe KI für Konsistenz-, Vollständigkeits- und Sprachprüfung.

### Tatsächliche lokale Ausgangslage am 12.10.2026

ATMED-core verfügt über 12 CPU-Kerne, 22 GiB RAM, keine feststellbare GPU- oder lokale LLM-Runtime und rund 84 GiB freien Root-Speicher. Ein kleiner quantisierter CPU-Inferenzdienst wäre möglich, aber für hochwertige fortlaufende medizinische Langtexte voraussichtlich langsam. Deshalb wird **kein** Modell stillschweigend installiert oder gestartet.

## Sichere Umsetzungsstufen

1. Erst Quellen-Synchronisation und deterministischen Retriever bauen; dies benötigt keine KI-Kontingente.
2. CPU-Pilot in isoliertem Container mit einem lizenzrechtlich geeigneten, quantisierten Open-Weights-Modell; CPU-/RAM-/Laufzeitlimits, keine Produktionssecrets, keine Netzwerkverbindung während der Inferenz.
3. Qualität anhand eines kleinen goldenen Artikelsets messen: Quellenabdeckung, Zitatgenauigkeit, Halluzinationsrate, Laufzeit und Ressourcenverbrauch.
4. Erst nach positiver Abnahme eine lokale Generation als Entwurfsquelle zulassen. Medizinisch hochriskante Artikel bleiben `safety_hold: true` und erhalten externe KI-QK sowie menschliche medizinisch-pharmazeutische Freigabe.

Die lokale Verarbeitung reduziert externe Kontingente, ersetzt aber weder evidenzbasierte Recherche noch menschliche Verantwortung.

## Entscheidungsvorlage: eigener WikiMedica-Research-Server

### Ergebnis

Ein dedizierter Server ist **langfristig sinnvoll**, sobald der kontinuierliche Quellenabgleich und die Artikelproduktion über einen kleinen Pilotbestand hinausgehen. Er entkoppelt die daten- und rechenintensiven Aufgaben vom produktiven Wiki, hält Quellenkorpora lokal vor und vermeidet fortlaufenden Verbrauch externer KI-Kontingente für die Entwurfsphase. Er ersetzt jedoch keine lizenzpflichtigen Datenquellen, kein medizinisches Review und keine externe Qualitätssicherung bei Hochrisikoinhalten.

Auf ATMED-core sollte dieser Betrieb nicht stattfinden: kein GPU-Befund, nur 22 GiB RAM, bereits 81 % Root-Dateisystembelegung und produktive Dienste. Ein CPU-Modell dort wäre ein enger, störanfälliger Pilot und kein belastbarer Dauerbetrieb.

### Zielprofil des getrennten Servers

- Dedizierte GPU-Inferenz mit ausreichend VRAM für ein in der medizinischen Quellensynthese evaluiertes, quantisiertes Open-Weights-Modell; die konkrete Modell- und GPU-Auswahl erfolgt erst nach Benchmark und Lizenzprüfung.
- 64–128 GiB RAM, verschlüsselter NVMe-Speicher mit getrenntem Quellen- und Modellbereich, Netzsegmentierung und kein direkter Schreibzugriff auf MediaWiki-Produktion.
- Unprivilegierte Container: Downloader, Parser, Suchindex, Inferenz, Orchestrator und QK-Gate getrennt; nur der kontrollierte Git/PR-Worker darf Ergebnisse ausgeben.
- Stündliche/daily Feeds und Signatur-/Checksum-Checks für offizielle Quellen; gestaffelte Crawl-Raten, Quellenlizenzen und robots.txt strikt einhalten.
- Nachvollziehbare Evidence Cards: Original-URL, Abrufzeit, Hash, Textausschnitt, Katalogversion, Modellversion, Prompt-/Retriever-Version und Entwurfs-Commit.
- Read-only-Zugriff auf Produktionsdaten nur wenn erforderlich; Veröffentlichungen bleiben über den bestehenden Git- und Beta-Importprozess kontrolliert.

### Abnahme vor Dauerbetrieb

1. Isolierter Pilot mit einer repräsentativen, medizinisch reviewten Goldstandard-Stichprobe.
2. Messung von Quellenabdeckung, Zitatzutrefflichkeit, nicht belegten Aussagen, Laufzeit, Strom-/Hostingkosten und Wiederanlauf nach Fehlern.
3. Sicherheits- und Lizenzfreigabe der Modelle sowie jeder Datenquelle.
4. Erst danach Produktionsbetrieb mit Ressourcenlimits, Alerting, Backups und regelmäßigem menschlichem Stichprobenreview.
