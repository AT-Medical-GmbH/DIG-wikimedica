# WikiMedica KI-Umsetzung: Journal

## 14.10.2026

- 19:56 Beginn Teil A. Sieben Entwurfs-PRs #300 bis #306 (WM-OP-0011 bis 0080) geprüft: keine Dateiüberschneidung, 315 Dateien ohne Validierungsfehler, 437 Tests bestanden. Der Test `test_system_pages::test_no_unsafe_markup_in_generated_pages` schlägt unabhängig davon auf `main` fehl (Hauptseitenvorlage mit Monatsschwerpunkt).
- 20:03 Sicherung vor dem Live-Gang: `/root/.claude/rueckweg/20261014-wikimedica-veroeffentlichung/` (Datenbankabzug, Stand der Synchronisation).
- 20:04 Merge der sieben PRs, `systemctl start wikimedica-beta-sync.service`: 70 Seiten `created`, `verified`.
- 20:10 Die zehn Entwürfe der lokalen KI (Myokarditis bis Hypothyreose) werden nicht übernommen: alle zehn Themen bestehen bereits als Artikel (WM-DIS-0012 bis 0021), sechs Entwürfe sind abgeschnitten (Modellantwort an `max_tokens` gescheitert, weil die Denkphase mitzählt).
- Ab 20:13 Teil B: Pipeline `wm_*.py` (siehe [Pipeline-Beschreibung](../editorial/redaktions-ki-pipeline.md)). Messwerte Gateway: etwa 100 Token je Sekunde und Anfrage, Denkphase 3000 Token für 150 Wörter.
- 20:25 Katalogbacklog gebaut: 1588 ICD-10-GM-Kategorien (davon 110 bereits abgedeckt), 4343 Einzelwirkstoffe nach ATC-GM (101 vorhanden), 912 EMA-Handelsnamen. Rote Liste und Pschyrembel nicht verwendet.
- 20:34 Gateway-Befunde: `max_tokens` höchstens 8192; Denkphase mit `enable_thinking: false` abschaltbar (50 s je Artikel statt Minuten).
- 20:42 Dienst `wikimedica-pipeline@1` gestartet (Dauerbetrieb), alter 20-Minuten-Timer abgeschaltet. Erste Messung: etwa ein geprüfter Artikel je Minute bei einem Arbeiter.
- 20:50 Teil C begonnen: Generator `wm_op_figures.py`, 17 freigegebene Schemazeichnungen, Einbindung über `md2wiki.py` und Importer-Upload (siehe [Schemazeichnungen](../editorial/op-schemazeichnungen.md)); Konzept für geschützten Medienbereich unter `docs/architecture/geschuetzter-medienbereich.md`.
