# Literature-to-Article Agent — WikiMedica

**Document version:** 1.0  
**Owner:** Editorial Board / Engineering  
**Last updated:** 2026-10-11  
**Status:** Proposed implementation in review

## 1. Ziel

WikiMedica betreibt bereits eine tägliche PubMed-Surveillance. Der Literature-to-Article Agent ergänzt eine zweite, strikt getrennte Ebene:

PubMed → täglicher Import → data/pubmed/ → kanonischer Literaturindex → thematische Cluster → Artikelkandidat oder Update-Hinweis → qualifizierter Autor → Fachreview → Veröffentlichung.

Der Agent veröffentlicht niemals medizinische Inhalte selbst. Er identifiziert Evidenzcluster, verknüpft sie mit bestehenden Artikeln und bereitet nachvollziehbare Quellenpakete vor.

## 2. Seed-Korpus

Am 2026-10-11 enthält data/pubmed/processed_pmids.txt **1.664 eindeutige PMIDs**. Dieser Bestand ist der Startkorpus und wächst mit jedem erfolgreichen täglichen Lauf.

Grundsatz: Eine Publikation ist nicht automatisch ein WikiMedica-Artikel. Die redaktionelle Einheit ist ein medizinisches Thema, das aus mehreren Quellen, aktuellen Leitlinien, regulatorischen Informationen und – soweit relevant – deutschen Epidemiologiedaten synthetisiert wird.

## 3. Täglicher Ablauf

1. scripts/pubmed/pubmed-daily-search.py durchsucht PubMed anhand der fachspezifischen Suchstrategien.
2. Neue PMIDs werden gegen processed_pmids.txt dedupliziert.
3. Die vollständigen Quellmetadaten werden in data/pubmed/YYYY-MM-DD.jsonl gespeichert.
4. scripts/pubmed/build-article-backlog.py erzeugt aus dem gesamten Bestand einen deduplizierten Literaturindex.
5. Derselbe Schritt gruppiert Publikationen anhand nicht-generischer MeSH-Begriffe und erzeugt einen priorisierten Artikel-Backlog.
6. Vorhandene WikiMedica-Titel werden heuristisch abgeglichen. Das Ergebnis ist nur ein Hinweis „möglicher neuer Artikel“ oder „bestehenden Artikel prüfen“.
7. Die generierten Daten werden gemeinsam mit dem PubMed-Lauf versioniert. Der MediaWiki-Publishing-Pfad bleibt unverändert.

## 4. Kanonischer Literaturindex

data/literature/index.jsonl enthält genau einen Datensatz pro PMID. Der Index speichert nur bibliografische und redaktionelle Metadaten und dupliziert den Volltext des Abstracts nicht.

Kernfelder sind PMID, Titel, Autoren, Journal, Publikationsjahr, Publikationstypen, MeSH-Begriffe, Sprache, DOI, PubMed-Link, WikiMedica-Fachgebiete, Relevanzklasse und Provenienz.

PMID ist der primäre Deduplikationsschlüssel. DOI ist Zusatzmetadatum und darf nicht ungeprüft als eindeutiger Schlüssel behandelt werden.

## 5. Artikelkandidaten

Die erste Implementierung ist vollständig deterministisch und verwendet kein generatives Modell. Sie bewertet Themencluster anhand von:

- Anzahl unabhängiger Publikationen,
- HIGH- und MEDIUM-Relevanz,
- Leitlinien/Practice Guidelines,
- systematischen Reviews/Metaanalysen,
- randomisierten Studien,
- Journaldiversität,
- Aktualität der jüngsten Quelle.

Generische MeSH-Begriffe wie Humans, Male, Female oder Altersgruppen werden nicht als Artikeltitel verwendet.

Jeder Kandidat erhält ein Quellenpaket mit PMIDs, Fachgebieten, Publikationszahl, Evidenzdesign-Zählung, jüngstem Jahr, Priorisierungsscore und möglichen bestehenden Artikeln.

Der Score ist ausschließlich ein Workflow-Priorisierungsscore, kein Evidenzgrad und keine klinische Empfehlung.

## 6. Vom Quellenpaket zum Artikel

Ein Editor wählt einen Kandidaten aus. Danach:

1. Quellenpaket fachlich bereinigen und irrelevante Arbeiten entfernen.
2. Aktuelle Leitlinien, regulatorische Quellen und deutsche Epidemiologie ergänzen.
3. Definitionen und Klassifikationen unabhängig prüfen.
4. Enzyklopädischen Artikel als Synthese schreiben, nicht als Zusammenfassung eines einzelnen Papers.
5. Verwendete PMIDs im Artikel-Frontmatter dokumentieren.
6. KI-Unterstützung offenlegen, falls verwendet.
7. Den normalen Pull-Request- und Human-Review-Prozess durchlaufen.

Für Pharmaka, Therapieprotokolle, Notfallmedizin, Intensivmedizin und Onkologie gelten unverändert die Hochrisiko- und Medical-Advisor-Regeln.

## 7. Optionale spätere KI-Draft-Stufe

Ein eigener Drafting-Agent kann später aus einem bereits redaktionell geprüften Quellenpaket einen Artikelentwurf in einem separaten Branch erzeugen. Dafür gelten zwingend:

- niemals im MediaWiki-Publishing-Pfad ausführen,
- keine erfundenen Quellen, PMIDs, DOIs, Dosierungen oder Statistiken,
- nur freigegebene Quellenpakete plus explizit zugeführte Leitlinien/regulatorische Quellen verwenden,
- ai_assisted: true und Beschreibung der KI-Nutzung setzen,
- Reviewer- und Sign-off-Felder leer lassen,
- maximal den Status draft oder in-review verwenden,
- niemals selbst mergen oder veröffentlichen.

Vor Aktivierung ist ein ausdrücklicher Beschluss des Editorial Board gemäß AI Assistance Policy erforderlich.

## 8. Strategie für den vorhandenen Bestand

Priority A: Thema steht auf der Launch-Liste und besitzt mehrere hochwertige Quellen → sofort Quellenpaket erstellen.  
Priority B: hochwertiger Evidenzcluster außerhalb der Launch-Liste → redaktionellen Kandidaten anlegen.  
Priority C: neue Publikation betrifft einen geplanten oder vorhandenen Artikel → Update-Aufgabe statt Duplikat.  
Priority D: isolierte, niedrig priorisierte oder sehr experimentelle Publikation → nur im Literaturindex behalten.

Die 100 geplanten Erkrankungsartikel sollten dadurch nicht vom Zufall des PubMed-Korpus bestimmt werden. Stattdessen dient das Korpus als Evidenzbasis für die redaktionell definierte Launch-Liste.

## 9. Qualität und Recht

- PubMed-Metadaten sind Discovery-Daten und kein Beweis für die Richtigkeit einer Aussage.
- Abstract-only-Auswertung reicht für Hochrisikoempfehlungen nicht aus.
- Volltexte dürfen nur verwendet werden, wenn Zugriff und Urheberrecht dies erlauben.
- Der öffentliche Quellbestand enthält bereits Abstracts; eine weitere Vervielfältigung von Verlagstexten sollte rechtlich geprüft werden. Der kanonische Index speichert deshalb keine Abstracts.
- Retractions, Expressions of Concern und Korrekturen sollen in einer späteren Enrichment-Stufe geprüft werden.
- Deutscher regulatorischer und leitlinienbezogener Kontext bleibt auch bei internationalem Quellenkorpus verpflichtend.

## 10. Dateien

- scripts/pubmed/pubmed-daily-search.py — täglicher PubMed-Import
- scripts/pubmed/build-article-backlog.py — Literaturindex und Artikelkandidaten
- data/pubmed/ — täglicher Quell-Audit-Trail
- data/literature/index.jsonl — deduplizierter Metadatenindex
- data/literature/article-candidates.jsonl — priorisierte Themencluster
- reports/generated/literature-article-backlog.md — lesbarer Redaktionsreport
- .github/workflows/pubmed-daily.yml — tägliche Ausführung

## 11. Nächste Ausbaustufe

Nach Abnahme dieser deterministischen Ebene folgen Retraction-/Correction-Enrichment, Leitlinienverknüpfung, automatische Zuordnung eingehender PMIDs zu Artikelslugs, kontrollierte GitHub-Issues/Quellenpakete und erst danach ein optionaler KI-Entwurfsagent.
