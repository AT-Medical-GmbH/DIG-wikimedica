# WikiMedica KI-Umsetzung: Journal

## 14.10.2026

- 19:56 Beginn Teil A. Sieben Entwurfs-PRs #300 bis #306 (WM-OP-0011 bis 0080) geprüft: keine Dateiüberschneidung, 315 Dateien ohne Validierungsfehler, 437 Tests bestanden. Der Test `test_system_pages::test_no_unsafe_markup_in_generated_pages` schlägt unabhängig davon auf `main` fehl (Hauptseitenvorlage mit Monatsschwerpunkt).
- 20:03 Sicherung vor dem Live-Gang: `/root/.claude/rueckweg/20261014-wikimedica-veroeffentlichung/` (Datenbankabzug, Stand der Synchronisation).
- 20:04 Merge der sieben PRs, `systemctl start wikimedica-beta-sync.service`: 70 Seiten `created`, `verified`.
- 20:10 Die zehn Entwürfe der lokalen KI (Myokarditis bis Hypothyreose) werden nicht übernommen: alle zehn Themen bestehen bereits als Artikel (WM-DIS-0012 bis 0021), sechs Entwürfe sind abgeschnitten (Modellantwort an `max_tokens` gescheitert, weil die Denkphase mitzählt).
- Ab 20:13 Teil B: Pipeline `wm_*.py` (siehe [Pipeline-Beschreibung](../editorial/redaktions-ki-pipeline.md)). Messwerte Gateway: etwa 100 Token je Sekunde und Anfrage, Denkphase 3000 Token für 150 Wörter.
