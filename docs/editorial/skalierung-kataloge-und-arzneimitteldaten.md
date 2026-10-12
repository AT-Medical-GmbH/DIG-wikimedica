# Skalierung entlang medizinischer Referenzkataloge

## Verbindliche, langfristige Erweiterung

Nach Abschluss der ersten Grundpakete werden weitere Artikel nicht opportunistisch, sondern über dauerhaft versionierte Katalog-Backlogs geplant. Ein Katalogeintrag ist zunächst nur ein Kandidat; er ersetzt weder Quellenrecherche noch redaktionelle oder fachliche Freigabe.

| Domäne | Führender Planungsanker | Umsetzung |
| --- | --- | --- |
| Erkrankungen | ICD-10-GM, später die jeweils verbindliche deutsche Nachfolgeklassifikation | Stabile interne Identität, jährliche Katalogversion, Synonyme und Abgrenzungen; keine automatisierte Gleichsetzung von ICD-Code und Artikelqualität. |
| Untersuchungen und Interventionen | OPS, jeweils aktuelle deutsche Fassung | Trennung von Diagnostik, Prozedur und Therapie; Versionsdatum und Geltungsbereich werden im Artikelmetadatensatz gespeichert. |
| Fachbegriffe | Alphabetische, lizenzrechtlich zulässige Terminologie-Backlogs; Pschyrembel nur nach geklärter Lizenz | Begriffe werden nicht kopiert, sondern eigenständig quellenbasiert definiert. Lizenzierte Referenzdaten bleiben getrennt von frei publizierbaren Texten. |
| Wirkstoffe und Präparate | Rote Liste / Gelbe Liste nur mit Vertrags- und Nutzungsfreigabe; regulatorische Primärquellen ergänzend | Wirkstoff- und Präparateebene trennen; PZN, Handelsname, Stärke und Zulassung nie ohne aktuelle, nachweisbare Quelle übernehmen. |

## Prozess und Qualität

1. Pro Katalog eine versionierte Importliste mit Quelle, Version, Abrufdatum, Lizenzstatus und interner ID führen.
2. Neue Kandidaten deduplizieren, Synonyme zuordnen und dem passenden Artikeltyp zuweisen.
3. Inhalte immer aus aktuellen Primärquellen, Leitlinien und regulatorischen Fachinformationen erstellen; eine Katalogbezeichnung genügt nicht.
4. Arzneimittel- und Hochrisikoinhalte bleiben bis zum dokumentierten medizinisch-pharmazeutischen Review `safety_hold: true`.
5. Für jede Veröffentlichung Git-Commit, Quellenstand, Reviewstatus, MediaWiki-Revision und Katalogversion nachhalten.

## Rote Liste DataHub: geprüfter Befund vom 12.10.2026

Die Rote Liste beschreibt den **RL DataHub** als JSON-API für Softwareanbieter. Die offizielle FAQ verweist für Konditionen, Vertragsunterlagen, Testdaten und technische Dokumentation auf die Produktseite. Ein frei nutzbarer, anonymer Produktionszugang wurde nicht festgestellt. Daher darf weder ein Scraper noch ein nicht autorisierter Abruf implementiert werden.

Eine Integration in WikiMedica oder EduKlinik ist erst nach Vertrags-, Lizenz-, Zweckbindungs-, Rollen- und Datenschutzprüfung zulässig. Die API-Zugangsdaten gehören ausschließlich in den zentralen Secret-Manager; eine serverseitige Vermittlerschicht darf nur die jeweils lizenzierte Teilmenge ausliefern. Rezeptpflichtige Fachinformationen müssen zusätzlich nach Zugriffsberechtigung und Heilmittelwerberecht bewertet werden.

Offizielle Ausgangspunkte:

- [RL DataHub für Softwareanbieter](https://rote-liste.com/rote-liste-l%C3%B6sungen-f%C3%BCr-softwarehersteller)
- [Rote Liste FAQ](https://www.rote-liste.de/faq)
- [Wirkstoffverzeichnis](https://www.rote-liste.de/wirkstoffverzeichnis)

## Fallback ohne Rote-Liste-Vertrag

Bis zu einem autorisierten Zugang nutzt die Redaktion regulatorische Primärquellen, insbesondere EMA-Produktinformationen, BfArM/PharmNet.Bund sowie zugelassene Fachinformationen. Diese Quellen ersetzen keine lizenzierte deutsche Präparate- und PZN-Datenbank.
