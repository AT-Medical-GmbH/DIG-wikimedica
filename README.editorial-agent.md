# WikiMedica Editorial-Agent (Dispatcher)

Diese Komponente ist der langlebige, wiederaufnehmbare Dispatcher der
WikiMedica-Redaktionswarteschlange. Sie hält Artikelzustände atomar fest,
verhindert parallele Läufe mit einer Dateisperre und erzeugt prüfbare
Statusberichte.

Sie ist **kein** autonomer medizinischer Autor und startet weder Codex noch
Claude. Solange kein eigener, berechtigter Recherche-Executor mit
Kostenlimits, Quellenprüfung und den medizinischen Sicherheitsgates integriert
ist, behält sie offene Artikel im Status `planned` und vermerkt den Grund im
Auditprotokoll. Dadurch entstehen weder erfundene Quellen noch unbelegte
Veröffentlichungsbehauptungen.

Die geplante Betriebsinstallation liegt in `infra/editorial/`; die vollständige
Bedienungs- und Sicherheitsdokumentation in
`docs/operations/editorial-agent.md`.
