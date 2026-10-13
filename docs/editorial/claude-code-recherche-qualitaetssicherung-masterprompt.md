# Arbeitsauftrag für Claude Code: WikiMedica-Redaktion, Recherche und Qualitätssicherung

## Auftrag und Ziel

Übernimm die Fortsetzung und die umfassende Qualitätsüberprüfung der WikiMedica-Artikel. Ziel der ersten Etappe sind **100 Erkrankungsartikel und 100 eigenständige Wirkstoffartikel**. Erst danach folgen die geplanten Serien zu 100 Untersuchungsmethoden und 100 Operationen/Interventionen. Eine Zahl in Git oder ein gemergter Pull Request ist kein Beleg für medizinische Freigabe oder Live-Veröffentlichung.

## Verbindliche Recherchemethodik

1. Prüfe vor jedem Artikel Bestand, Slug, stabile Artikel-ID, offene und gemergte PRs sowie den Livezustand. Keine Dubletten erzeugen.
2. Recherchiere primär in überprüfbaren Originalquellen: AWMF/NVL, RKI, STIKO, IQWiG, BfArM, PEI, EMA, europäische Fachgesellschaften, WHO, PubMed/MEDLINE, Cochrane und aktuelle Fachinformationen. Nutze Sekundärquellen nur zur Orientierung, nicht als Ersatz für zentrale Sicherheits- oder Therapieaussagen.
3. Für jede wesentliche klinische Aussage: Institution/Autor, Titel, Jahr bzw. Aktualisierungsdatum, Geltungsbereich, URL/DOI/PMID und genaue Relevanz nachvollziehbar dokumentieren. Keine DOI, PMID, Zulassung, Leitlinie, Studie oder quantitative Aussage erfinden.
4. Bei Wirkstoffen ist vor jeder Aussage zu Indikation, Kontraindikation, Wechselwirkung, Schwangerschaft/Stillzeit, Organfunktion oder Dosierung die aktuelle Fachinformation zu verifizieren. Ohne verifizierte Primärquelle keine Dosis, keine Grenzwerte und keine individualisierte Therapieanweisung schreiben.
5. Bei nicht belastbarer oder widersprüchlicher Evidenz die Unsicherheit transparent benennen und den jeweiligen Abschnitt blockieren oder als Reviewfrage markieren.
6. Verwende nur lizenzierte Medien. Für jedes Bild: Titel, Urheber, Ursprungsquelle, Lizenz/Version, Abrufdatum, Bearbeitungen und fachliche Prüfung dokumentieren. Keine klinischen Befunde synthetisch als echte Befunde ausgeben.

## Redaktionelle Umsetzung

- Arbeite in isolierten Git-Worktrees auf einem Branch pro Zehnerpaket. Vor jeder Änderung Rückweg sichern; keine fremden uncommitteten Änderungen übernehmen.
- Nutze die vorhandenen Markdown-Vorlagen, YAML-Metadaten, Fachgebietsstruktur und Validatoren. Arzneimittel erhalten immer `article_type: pharmaka`, `risk_level: high`, `safety_hold: true` und einen ausstehenden ärztlichen sowie pharmazeutischen Fachreview.
- Die Artikel müssen deutschsprachig, eigenständig lesbar, quellenbasiert und strukturiert sein. Erkrankungsartikel: Definition, Epidemiologie, Ursachen/Risiken, Pathophysiologie, Klinik, Diagnostik, Therapiegrundsätze, Prognose, Prävention, Gendermedizin, Patienteninformation, Literatur. Wirkstoffartikel: INN, ATC, Klasse, Mechanismus, Pharmakodynamik/-kinetik, zugelassene Indikationen, Kontraindikationen, Warnhinweise, Interaktionen, Nebenwirkungen, Nieren-/Leberfunktion, Schwangerschaft/Stillzeit, Altersgruppen, Monitoring, Pharmakovigilanz, Handelsnamen, Literatur.
- Quellen im Fließtext einheitlich wie in der deutschsprachigen Wikipedia als hochgestellte Zahlen in eckigen Klammern ausgeben, z. B. `.[1]` beziehungsweise mehrere Referenzen `.[1][2]`. Eine nummerierte Literaturliste am Ende ordnet jede Nummer eindeutig einer überprüfbaren Quelle zu.
- Entferne keine BETA-Kennzeichnung und erkläre Entwürfe nicht als fachlich geprüft. Ein KI-gestützter Entwurf bleibt als solcher intern dokumentiert; die öffentliche BETA-Kennzeichnung bleibt sichtbar.

## Technische Validierung und Pull Requests

1. Führe vor jedem Commit mindestens YAML-/Schema-/Metadatenvalidierung, Dublettenprüfung, Quellen- und Linkprüfung, Wikitext-Konvertierungsprüfung, Injektionsprüfung und die verfügbaren Tests aus.
2. Lege einen Draft-PR mit genau dem Zehnerpaket, Quellenübersicht, Prüfprotokoll, offenen Reviewfragen und BETA-Status an. PRs nicht als medizinisch freigegeben bezeichnen.
3. Dokumentiere Branch, Commit, PR-URL, Artikelliste, Validatorergebnisse und bekannte Einschränkungen im Statusregister.
4. GitHub `main` bleibt die redaktionelle Quelle. Ein Merge kann im derzeit autorisierten BETA-Prozess eine technische BETA-Einspielung erlauben, ist aber niemals ein Ersatz für ein unabhängiges medizinisches Peer Review.

## Veröffentlichung und Verifikation

1. Nutze ausschließlich die vorhandene, getestete lokale Pipeline: GitHub `main` → `/opt/wikimedica-source` → `wikimedica-beta-sync.service` → lokaler Docker-/MediaWiki-CLI-Importer. Nicht auf die öffentliche Action API ausweichen (bekannter HTTP-403-Fall).
2. Vor produktiven Änderungen Rückweg und Snapshot nach lokaler Betriebsregel erstellen. Produktion und Staging strikt trennen.
3. Für jede technisch erlaubte BETA-Publikation: MediaWiki-Seite zurücklesen, Inhalt/Commit/Marker vergleichen, Revision und öffentliche Erreichbarkeit dokumentieren. Bei Konflikt, fehlendem Marker, manueller Fremdänderung, fehlender Quelle oder Importfehler nicht überschreiben.
4. Fachlich freigegeben wird ein Artikel erst nach nachweisbarer unabhängiger fachärztlicher bzw. bei Pharmaka zusätzlich pharmazeutischer Prüfung und Medical-Advisor-Sign-off. Diese Freigaben niemals simulieren.

## Umfassende Qualitätsprüfung bestehender Artikel

Prüfe alle vorhandenen Artikel systematisch auf Vollständigkeit, Aktualität, Quellenqualität, Datenkonsistenz, deutsche Rechtschreibung, einheitliche Referenznotation, interne Links, nachvollziehbare Unsicherheiten, Sicherheitswarnungen, Lizenzmetadaten und Patientenverständlichkeit. Priorisiere Hochrisikothemen, Arzneimittel, Notfallmedizin, Intensivmedizin, Onkologie, Schwangerschaft und invasive Verfahren. Lege Korrekturen nachvollziehbar in thematisch kleinen PRs vor und halte Reviewfragen separat fest.

## Unzulässige Abkürzungen

- Keine Quellen, Prüfungsergebnisse, Zulassungen, Live-Seiten, PRs oder Backups erfinden.
- Keine patientenbezogenen Daten, Secrets oder vollständigen Zugangsdaten in Repository, Logs oder Berichte schreiben.
- Keine automatischen medizinischen Freigaben, keine Umgehung von Review-Gates und keine unkontrollierten Massenimporte.
- Kein Überschreiben manuell bearbeiteter MediaWiki-Seiten ohne Eigentums- und Konfliktprüfung.

## Abschlussnachweis

Erst bei tatsächlichem Nachweis aller 200 Artikel einen Abschlussbericht erstellen. Er muss pro Artikel zwischen erstellt, technisch validiert, im PR, gemergt, BETA-live, fachlich geprüft und regulär veröffentlicht unterscheiden sowie die Qualitäts- und Skalierungsgrenzen offenlegen.
