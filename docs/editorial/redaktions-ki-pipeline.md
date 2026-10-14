# Redaktions-KI-Pipeline für Massenerstellung (Stand 14.10.2026)

Dieses Dokument beschreibt die Dauerbetriebs-Pipeline, die aus freien amtlichen Katalogen Themen plant, mit dem lokalen Modell (Qwen über das AT-AI-Gateway, kein Claude-Kontingent) recherchierte Artikel erstellt, maschinell auf Belege prüft und als Sammel-Pull-Request veröffentlicht.

## Entscheidung und Grenzen

- Entscheidung Andreas Tremml vom 14.10.2026: Artikel dieses Stroms werden ohne sichtbaren Hinweis „KI-Entwurf“ veröffentlicht. Die Felder `ai_assisted` und `ai_assistance_description` bleiben wahrheitsgemäß in den Metadaten stehen.
- Was die Faktenprüfung nicht besteht, wird nicht veröffentlicht, sondern erscheint in der [Prüfliste](ki-pruefliste.md).
- Keine Kosten, keine kostenpflichtigen Schnittstellen. Kein Abruf der Roten Liste und kein Abruf von Inhalten oder Stichwortlisten des Pschyrembel.
- Der Importer-Klon `/opt/wikimedica-source` wird nicht verändert; der Live-Gang läuft über `wikimedica-beta-sync.service`.

## Komponenten

| Datei | Aufgabe |
| --- | --- |
| `scripts/editorial/wm_common.py` | SQLite-Warteschlange (atomares Beanspruchen), zentraler Gateway-Zähler, Hilfsfunktionen |
| `scripts/editorial/wm_catalog.py` | Themenbacklog aus ICD-10-GM, ATC-GM und EMA mit stabilen IDs, Dublettenprüfung, Priorisierung |
| `scripts/editorial/wm_research.py` | PubMed-Recherche, PMC-Open-Access-Auszüge, PMID-Verifikation |
| `scripts/editorial/wm_pipeline.py` | Arbeiter: Suchbegriff, Recherche, Entwurf, Faktenprüfung, Artikelaufbau, Validierung |
| `scripts/editorial/wm_publisher.py` | stündlicher Sammel-PR, Merge, Live-Gang, Prüfliste |
| `infra/editorial/wikimedica-pipeline@.service` | Dauerbetrieb der Arbeiter (Instanz 1, 2, 3) |
| `infra/editorial/wikimedica-publisher.*` | stündliche Veröffentlichung |
| `data/editorial/backlog/*.jsonl` | versionierter Themenbacklog (WM-DIS, WM-DRUG, WM-TRADE) |

## Themenquellen und Lizenzen

| Domäne | Quelle | Nutzung |
| --- | --- | --- |
| Diagnosen (WM-DIS-0101 ff.) | ICD-10-GM 2026, BfArM, Metadaten-Download | dreistellige Kategorien; Titel unverändert in `icd_title`; Kapitel 20 bis 22 (äußere Ursachen, Z-Codes, U-Codes außer U07) ausgeschlossen |
| Wirkstoffe (WM-DRUG-0101 ff.) | ATC-GM mit DDD 2026, BfArM (amtliche deutsche Fassung) | nur Code und Name von Einzelwirkstoffen; keine definierten Tagesdosen |
| Handelsnamen (WM-TRADE-0001 ff.) | EMA-Arzneimitteldatenbank (Bericht „Medicines“) | nur zentral zugelassene Humanarzneimittel, Zuordnung über ATC-Code; Seite verweist nur auf den Wirkstoffartikel |
| Häufigkeit für die Priorisierung | Eurostat `hlth_co_disch2`, Deutschland, Krankenhausentlassungen je 100 000 Einwohner | Näherung: Entlassungen der kleinsten umfassenden Eurostat-Gruppe geteilt durch die Zahl ihrer Dreisteller |

Pflichtangaben:

- ICD-10-GM: Die Ausgabe beruht auf der vollständigen amtlichen Fassung der ICD-10 der WHO (© Weltgesundheitsorganisation 1992) und der australischen ICD-10-AM (© Commonwealth of Australia 1998). Herausgegeben vom Bundesinstitut für Arzneimittel und Medizinprodukte (BfArM) im Auftrag des Bundesministeriums für Gesundheit. Es gilt das Änderungsverbot (§ 62 UrhG); Klassentitel werden nicht verändert, Artikeltitel dürfen nur unzulässige Sonderzeichen verlieren.
- ATC-GM: Das Wissenschaftliche Institut der AOK (WIdO) ist Urheber der ATC-GM mit DDD, die auf dem vom WHO Collaborating Centre for Drug Statistics Methodology herausgegebenen Werk „ATC Index with DDDs and Guidelines for ATC Classification and DDD Assignment“ beruht. Die amtliche Veröffentlichung erfolgt durch das BfArM.
- Die Downloadbedingungen des BfArM (Quellenangabe, Änderungsverbot, keine kommerzielle Werbung in den Werken) wurden am 14.10.2026 beim Herunterladen akzeptiert; sie liegen in `data/catalogs/icd10-gm-2026/` bzw. im Download der Metadaten.

### Nicht verwendete Quellen

- **Rote Liste / Gelbe Liste:** nur nach Vertrag (RL DataHub). Kein Abruf, kein Scraping.
- **Pschyrembel:** Eine frei lizenzierte Stichwortliste ist nicht bekannt; das Stichwortverzeichnis gehört zum geschützten Werk des Verlags. Deshalb wird der Pschyrembel weder als Themenquelle noch inhaltlich verwendet. Sollte ein Lizenzvertrag oder eine ausdrückliche Freigabe der Stichwortliste vorliegen, kann sie als vierter Backlog (`WM-TERM-`) im Format der übrigen `*.jsonl`-Dateien ergänzt werden. Inhalte oder Formulierungen werden in keinem Fall übernommen.
- **AWMF-Leitlinienregister:** keine dokumentierte öffentliche Schnittstelle (Webanwendung). Verweise kommen nur aus der optionalen Datei `data/editorial/awmf-leitlinien.json` (Schlüssel: Artikel-Slug).

## Ablauf je Artikel

1. Beanspruchen: höchste Priorität zuerst, Sperre über SQLite (`BEGIN IMMEDIATE`), höchstens drei Versuche.
2. Dublettenprüfung gegen alle Artikel im Repo (Slug, normierter Titel, Alias-Tabelle bekannter ICD-Codes).
3. Englischen PubMed-Suchbegriff bestimmen (ein kurzer Modellaufruf; bei zu wenigen Treffern ein zweiter, allgemeinerer Begriff).
4. Recherche: Leitlinien der letzten 10 Jahre, Metaanalysen, systematische Übersichtsarbeiten und Übersichtsarbeiten der letzten 5 Jahre; zurückgezogene Arbeiten werden verworfen; bis zu drei PMC-Open-Access-Volltextauszüge (nur bei Creative-Commons-Lizenz).
5. Entwurf mit nummerierten Quellen; jeder Satz mit Sachaussage trägt eine Quellennummer.
6. Formale Prüfung: gültige Quellennummern, Belegpflicht je Satz, bei Wirkstoffartikeln keine Dosierungsangaben.
6a. Suchbegriff und deutscher Artikeltitel: ein kurzer Modellaufruf; ist der gebräuchliche deutsche Titel (z. B. „Leistenbruch“ statt „Hernia inguinalis“) bereits vergeben, gilt das Thema als Dublette.
7. Faktenprüfung: zweiter Modelldurchlauf je Satz gegen Zusammenfassungen und Volltextauszüge (`s` gedeckt, `p` teilweise, `u` nicht gedeckt). Nicht gedeckte Sätze entfallen, leere Abschnitte ebenfalls, Quellen werden neu nummeriert.
7a. Sprachkorrektur: dritter Durchlauf nur für Rechtschreibung und Stil; wird verworfen, wenn sich Satzstruktur, Quellennummern oder Zahlen ändern.
8. Bestehensgrenzen: mindestens 10 bestätigte Sätze, 3 Abschnitte, 3 zitierte Quellen, Bestätigungsquote mindestens 60 Prozent, höchstens 40 Prozent nur teilweise belegte Sätze. Sonst Prüfliste.
9. Artikelaufbau im Repo-Format; alle zitierten PMIDs stammen aus der abgerufenen und gegen PubMed aufgelösten Menge; DOI aus PubMed; Prüfung mit `validate-metadata.py`.
10. Stündlich: Sammel-PR (höchstens 60 Artikel plus 40 Handelsnamen-Seiten), Renderprobe des BETA-Importers, Merge, Start von `wikimedica-beta-sync.service`, Verifikation im Journal.

Der Status der Artikel bleibt `draft` wie bei allen bisherigen BETA-Artikeln; die Seite trägt den seitenweiten BETA-Kasten des Importers.

## Befunde zum Gateway (Messung 14.10.2026)

- Das Gateway begrenzt `max_tokens` auf höchstens 8192 (HTTP 422 darüber). Das Modell Qwen3.6-35B-A3B „denkt“ standardmäßig; die Denkphase zählt zu den Ausgabetoken (bis zu 4000 Token schon für 150 Wörter). Das erklärt die abgeschnittenen Entwürfe des alten Dienstes.
- Mit dem Top-Level-Feld `enable_thinking: false` entfällt die Denkphase (`chat_template_kwargs` und `reasoning_effort` wirken nicht). Dadurch dauert ein vollständiger Artikel (Suchbegriff, Entwurf, Faktenprüfung, Sprachkorrektur) etwa 50 Sekunden statt mehrerer Minuten, etwa 100 Token je Sekunde und Anfrage.
- Je Artikel entstehen drei bis vier Modellanfragen (Suchbegriff und Titel, Entwurf, Faktenprüfung, Sprachkorrektur). Bei 300 bis 500 Artikeln je Tag sind das im Mittel etwa 1 Anfrage je Minute.

## Betrieb

- Zustand: `/var/lib/wikimedica-editorial-agent/pipeline.sqlite`; fertige Artikel in `outbox/`, Prüfliste-Kandidaten in `review/`.
- Pausieren: Datei `pipeline.pause` im Zustandsverzeichnis anlegen; Beenden: `pipeline.stop`.
- Gateway-Grenzen: höchstens 4 Anfragen je Minute und 3 gleichzeitig (Umgebungsvariablen `WM_MAX_REQUESTS_PER_MIN`, `WM_MAX_CONCURRENT`), zentral gezählt. Bei HTTP 429/5xx, Zeitüberschreitung oder Antwortzeit über 90 Sekunden drosselt die Pipeline zehn Minuten lang auf 1 Anfrage je Minute (Vorrang laut claude-code-atinfra-control: Doc Blue, dann 3CX-KI-Agent, dann Dokumenten-Pipeline, dann WikiMedica).
- Tagesgrenze: höchstens 500 fertige Artikel je 24 Stunden (`--max-per-day`), alle Arbeiter zusammen.
- Rückweg: `systemctl disable --now 'wikimedica-pipeline@*' wikimedica-publisher.timer`; der frühere Timer `wikimedica-editorial-llm.timer` bleibt als Rückfall bestehen.
- Neue Backlogs: `python3 scripts/editorial/wm_catalog.py build --repo . --ema-xlsx … --atc-txt …`, danach `load-queue`. Bestehende IDs bleiben stabil.

## Offene Punkte

- Priorisierung nach Häufigkeit ist eine Näherung (Eurostat-Gruppen); amtliche Diagnosestatistik des Statistischen Bundesamtes würde sie verfeinern.
- Rote-Liste-Vertrag für deutsche Präparatenamen und PZN steht aus (Hauptsitzung).
- Fachärztliche Prüfung der veröffentlichten Artikel bleibt offen (Verantwortung Andreas Tremml).
