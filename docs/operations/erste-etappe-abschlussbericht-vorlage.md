# WikiMedica – Abschlussbericht zur ersten großen Ausbaustufe (Vorlage)

**Status:** Vorlage, **kein Abschlussbericht über bereits fertiggestellte Arbeiten**. Nur nach belegter Fertigstellung und Veröffentlichung ausfüllen.

**Übergeordnetes Architekturziel:** [WikiMedica als medizinische Enzyklopädie ohne künstliches Artikelmaximum](../editorial/wiki-medizin-gesamtarchitektur.md).

## 1. Umfang und Abnahme

- Geplante erste Etappe: 100 Erkrankungsartikel; 100 Wirkstoffartikel; verifizierte Handelsnamen-Weiterleitungen; deduplizierte zusätzliche Artikel aus dem vorhandenen PubMed-Korpus.
- Tatsächlich erstellte Entwürfe: **[Zahl mit GitHub-Beleg]**
- Fachlich kontrollierte und gemergte Artikel: **[Zahl mit PR-Belegen]**
- Tatsächlich per MediaWiki-Revision veröffentlicht: **[Zahl mit Nachweis]**
- Weiterleitungen: **[Zahl, eindeutige Wirkstoffzuordnung und verifiziertes Redirect-Verhalten]**
- Nicht freigegebene / zurückgehaltene Inhalte: **[Auflistung]**
- Medizinische Evidenzprüfungen, Sicherheits-/Reviewerstatus und relevante Einschränkungen: **[Belege]**
- Produktivtests des täglich geplanten Imports um 06:30 Europe/Berlin: **[Journal/Revisionen]**

**Wichtig:** Die Existenz einer Markdown-Datei, ein PR, ein KI-Entwurf oder eine `draft`-Markierung sind **kein Beweis für die fachliche Freigabe und Veröffentlichung**. Die ersten 100/100 sind Meilensteine, keine Inhaltsgrenze.

## 2. Qualitäts- und Quellenlage

Leitlinien mit Geltungsgebiet/Stand; strukturierte PubMed- und Evidenzzuordnung; Retractions und Quellenkonflikte; Hochrisiko- und Medikamentenprüfungen; personell geklärte fachliche Verantwortung. Fehlende Werte ausdrücklich als `nicht erhoben` oder `noch offen` kennzeichnen.

## 3. Verpflichtendes Infrastrukturkapitel: Frühzeitige Anpassung für unbegrenztes Wissenswachstum

> **WikiMedica kennt keine fest definierte Obergrenze des medizinischen Wissensbestands; Infrastruktur und Qualitätssicherung müssen frühzeitig so vorbereitet werden, dass weitere fachliche Domänen und Millionen von Artikeln möglich bleiben.**

### 3.1 Ist-Messwerte (mit Zeitstempel und Quelle)

| Messgröße | Aktueller Wert | Trend | Quelle / Messzeit | Limit / Warnschwelle |
|---|---|---|---|---|
| Gesamtzahl Seiten / Revisionen | Nicht erhoben | — | — | — |
| Datenbankgröße / IOPS / Abfragelatenz | Nicht erhoben | — | — | — |
| Medienobjekte / Speichergröße | Nicht erhoben | — | — | — |
| Freier Speicher / Wachstum | Nicht erhoben | — | — | — |
| CPU / RAM / Swap / Prozesszahl | Nicht erhoben | — | — | — |
| Seitenlatenz und Fehlerquote | Nicht erhoben | — | — | — |
| Indexgröße / Suche / Index-Lag | Nicht erhoben | — | — | — |
| Importlaufzeit und Fehlerrate | Nicht erhoben | — | — | — |
| Backupgröße und getestete Restore-Zeit | Nicht erhoben | — | — | — |
| Laufende Kosten / Kapazitätsbudget | Nicht erhoben | — | — | — |

### 3.2 Szenarien und Annahmen

Für **10.000**, **100.000**, **1.000.000** und **mehr als 1.000.000** medizinische Artikel: Annahmen pro Textgröße, Revisionen, Quellen und Verknüpfungen, Anzahl Medienobjekte, Monatswachstum, Lese-/Schreibrate, Backup-Retention; Bandbreiten statt präzise erfundener Hochrechnungen.

### 3.3 Maßnahmen-Roadmap

Trenne `jetzt erforderlich`, `nach Messung` und `langfristige Option`:

- Inhalts-IDs, Schema-Facetten, Wissensgraph, Synonyme und Redirects
- DB-Kapazität, Replikation, Query-Tuning und migrierbare Persistenz
- Objekt-Storage / Medienrechte / CDN
- Skalierbarer Volltext- und Facettensuchindex
- Idempotente inkrementelle Batch-Importer / Queue / Wiederholungen / Audit
- Monitoring und SLOs
- Evidenz- und Qualitätskontrollen auch bei großem Artikelbestand
- Backups, belastbare Recovery-Tests, Datenintegrität und Ausfallsicherheit
- Hosting-/Storage-Kosten, Schwellenwerte, Ressourcen- und Sicherheitsbudget

Für jede priorisierte Maßnahme: **Abhängigkeit, Risiko, Aufwandsspanne, verantwortliche Rolle, Abnahmekriterium und Migrations-/Rollbackstrategie**. Produktiven WikiMedica-Betrieb nicht ohne Test-/Freigabepfad umbauen.

## 4. Redaktionelle nächste Etappen

Die Erweiterung über den Launch hinaus **nicht zahlenmäßig begrenzen**. Medizinische Operationen, Interventionen, Diagnostik, Bildgebung, Anatomie, Physiologie, Labor, Impfungen, Transplantation, Patientenaufklärung, medizinhistorische und medizinkritische Themen sowie weitere nachweisbare Wissensdomänen fortlaufend nach Quellenlage erschließen.

## 5. Offene Risiken und Entscheidungen

**[Mit Verantwortlichkeiten und Zeitfenstern ausfüllen.]**

## 6. Abnahme

**[Datum, Betreiberfreigabe, PR-/Release-/Live-Nachweise, ausstehende Prüfungen.]**
