# WikiMedica – Grenzenlose medizinische Wissensenzyklopädie: Gesamtarchitektur

**Entwurfsstand: 11.10.2026 · Verbindliches Produktziel, kein bereits umgesetztes Skalierungsversprechen.**

## 1. Grundsatz

**WikiMedica erhält keine künstliche Obergrenze für Artikelanzahl, Wissensdisziplinen, Verknüpfungen oder Medientypen.** Die Grenze des redaktionellen Themenbereichs ist das jeweils verfügbare, belastbar belegbare medizinische Wissen einschließlich seiner Geschichte, Methodik, Ethik, gesellschaftlichen Auswirkungen und wissenschaftlichen Unsicherheiten. Selbst eine Million Artikel ist kein „Endausbau“, sondern nur ein hypothetischer Kapazitätsmeilenstein.

Die ersten **100 Erkrankungsartikel**, **100 eigenständigen Wirkstoffartikel** mit geprüften Handelsnamen-Referenzen und zusätzliche Artikel aus dem bestehenden PubMed-Korpus bilden nur die **erste große redaktionelle Etappe**. Veröffentlichungen erfolgen in prüfbaren **Zehner-PRs**, deren Merge der Betreiber selbst freigibt. Auf weitere Domänen und Artikelzahlen darf keine inhaltliche Obergrenze angewendet werden.

**Betriebsrealität:** Speicherplatz kann durch Erweiterung oder Auslagerung skaliert werden, ist aber nie technisch, finanziell oder betrieblich „unendlich“. Absehbare Engpässe sind präventiv zu messen und mit belastbarer Migrationsplanung abzufangen. Wachstum darf die Qualität der Quellen, Patienten- und Datensicherheit, Versionsverwaltung, Rechtekontrolle, Suchbarkeit oder Wiederherstellbarkeit nicht untergraben.

## 2. Vollständiges Wissensspektrum – kein abschließender Katalog

WikiMedica ist ein systematisch vernetztes medizinisches Nachschlagewerk **für Fachpersonal und Öffentlichkeit**. Gleichwertige Wissensdomänen:

| Domäne | Beispiele |
|---|---|
| Erkrankungen, Syndrome, Symptome | Häufige und seltene Erkrankungen, Differentialdiagnosen |
| Wirkstoffe und Arzneimittel | INN, ATC, Wirkmechanismus, Zulassung, Sicherheit; verifizierte Präparate-/Handelsnamenreferenzen |
| Operationen | Herz-, Thorax-, Allgemein-, Neuro-, Transplantationschirurgie |
| Interventionen | PCI, TAVI, elektrophysiologische Ablation, Endoskopie |
| Untersuchungsverfahren | Klinische Untersuchung, EKG, Spirometrie, Endoskopie, neurophysiologische Verfahren |
| Bildgebung | Ultraschall, Echo, TEE, Röntgen, CT, MRT, Nuklearmedizin |
| Anatomie, Physiologie, Histologie | Organe, Strukturen, Zell- und Organfunktionen, Pathophysiologie |
| Labor, Mikrobiologie, Pathologie | Biomarker, Proben, Untersuchungsgüte, Erreger, Klassifikationen |
| Behandlung, Prävention und Rehabilitation | Therapieoptionen, Präventionsmaßnahmen, Nachsorge |
| Transplantationsmedizin | Organspende, Empfänger, Allokation, Operation, Nachsorge, Ethik |
| Impfungen | Impfstoffe, STIKO-Empfehlungen, Schutz und Grenzen, Sicherheit |
| Patientenaufklärung | Erkrankungen, OP/Intervention, Diagnostik, Shared Decision Making |
| Medizinische Mythen und Faktenchecks | Populäre Behauptung, Evidenzbefund, Unsicherheiten und Revision |
| Geschichte der Medizin | Epochen, Entdeckungen, Biografien, historische Irrwege und Verfehlungen |
| Ethik, Recht, Gesellschaft | Patientenrechte, Gesundheitsrecht, Forschungsethik |
| Forschung und Evidenz | Studienformen, Statistik, Leitlinien, wissenschaftliche Kontroversen |
| Public Health | Epidemiologie, globale Gesundheit, Gesundheitssysteme |
| Medizinprodukte und Technik | Implantate, Assistenzsysteme, Robotik, KI, Digital Health |
| Gesundheitsberufe und Ausbildung | Rollen, Lehre, Qualitätsmanagement |

Der Katalog ist **erweiterbar**, nicht restriktiv. Fachgebiete wie Kardiologie, Anästhesie, Neurologie usw. sind orthogonale **Facetten** und dürfen nicht die einzige Navigation bestimmen.

## 3. Kanonische Inhalte und Beziehungen

Für jede Entität langfristig eine stabile ID, einen kanonischen Artikel, Synonyme/Aliase, Sprachen, fachliche Kategorien und typisierte Verknüpfungen. Beziehungen unter anderem `diagnosed_by`, `treated_with`, `affects_anatomy`, `mechanism`, `evidence_for`, `patient_explainer`, `historical_context`, `myth_about`, `trade_name_of`. Klinische Relationen sind Aussagen und benötigen Herkunft, Version und Validierung; keine erfundene Wissensgraph-Evidenz.

**Handelsnamen:** Ein eindeutiger, geprüfter Einzelwirkstoff-Handelsname kann auf einen INN-Artikel weiterleiten. Kombinationen, abweichende Länder-/Stärken-/Darreichungsformen und uneindeutige Bezeichnungen brauchen eigene geprüfte Produkt-/Begriffsklärungsseiten. Ein Redirect ist kein weiterer medizinischer Vollartikel.

Beispiel **Organtransplantation**: Patientenaufklärung ↔ Organspende ↔ nationale Rechtslage ↔ Operation ↔ Anatomie ↔ Immunsuppression ↔ Komplikationen ↔ Nachsorge ↔ Ethik ↔ Medizingeschichte.

## 4. Qualität pro Artikeltyp

- **Krankheitsbild:** Klassifikation, Epidemiologie mit Datenjahr/Population, Pathophysiologie, Symptomatik, Diagnostik/Differentialdiagnose, Therapieprinzipien, Prognose, Patientenabschnitt, Quellen, Gender-Aspekte.
- **Wirkstoff:** INN/ATC, Wirkmechanismus, geprüfte deutsche Zulassung, Indikation, Kontraindikationen, Interaktionen, Sicherheit, besondere Personengruppen, Fachinformation; Arzneimittelartikel `risk_level: high`.
- **Operation/Intervention:** Indikationen/Alternativen, Ablaufübersicht, mögliche Komplikationen, Nachsorge und Aufklärung; bei Zahlen belastbare Population, Zeitraum und Quelle.
- **Untersuchung/Bildgebung:** physikalisch-technisches Prinzip, Indikationen, Ablauf, Nutzen, diagnostische Genauigkeit und Grenzen, Risiken/Artefakte.
- **Transplantation:** medizinischer Ablauf und Ethik, Spender/Empfänger, Nachsorge, gültige nationale rechtliche und organisatorische Regeln.
- **Impfung:** Erkrankungsrisiko, Impfstoff, STIKO-/RKI-Stand, Schutz, Risiken und Grenzen, Unsicherheiten.
- **Medizinmythos:** präzise Behauptung, Urteil (widerlegt/nicht belegt/teilweise zutreffend/kontextabhängig/zutreffend), Belege, Grenzen, Prüfdatum.
- **Medizingeschichte:** chronologische und quellenkritische Darstellung, historische Sicht und heutiger Kenntnisstand ausdrücklich trennen.

AI-generierte Texte dürfen **keine unabhängigen Reviewer oder klinische Sign-offs fingieren**. Betreiber-Merge für den getrennten, deutlich markierten BETA-Kanal ist operative Freigabe, nicht automatisch Peer Review. Menschlicher Review und verifizierbare Quellen bleiben erforderlich.

## 5. Medien und Rechte

Vorzugsweise qualitativ geeignete **nachweislich kompatibel lizenzierte** Illustrationen/Fotos mit Autor, Quelle, Lizenz und Bearbeitungsvermerk. Bloße Nennung der Quelle ersetzt keine Lizenz. Falls kein verwendbares Bild gefunden wird, kann eine Illustration etwa über **Higgsfield** erzeugt werden; KI-Herkunft und medizinische Validierung sind zu dokumentieren. Bilder synthetischer Befunde sind keine echten diagnostischen Befunde. Historische Materialien gesondert auf Gemeinfreiheit/Rechte prüfen. Langfristig Asset-Metadaten und skalierbaren Medien-Storage trennen.

## 6. Skalierbare Zielarchitektur – von 100 bis über 1.000.000 Artikel

Der funktionierende **MediaWiki-1.43-Produktivbetrieb** darf nicht wegen eines theoretischen Skalierungsziels blind umgebaut werden. Frühzeitig **modulare, migrationsfähige Grenzen** definieren:

1. **GitHub als redaktionelle Quelle** mit PR-/Merge-Audit, stabilen Slugs und Inhaltsversionen. Bei wachsendem Korpus später Repo-/Monorepo-Kosten und alternative Quellpartitionierung anhand realer Messungen evaluieren.
2. **MediaWiki-Anwendung** als Präsentations-/Revisionsschicht, horizontale Web-Serving-Skalierung nach Lasttest, ohne Autorisierung oder Review zu lockern.
3. **Datenbank** mit Wachstums-, Index-, Replikations-, IOPS-, Backup-/Restore- und Migrationskonzept; keine vorzeitige riskante Umschaltung.
4. **Medien** ausgelagert auf S3-kompatiblen Objekt-Storage mit CDN, Lizenzprovenienz, Größenvarianten, unveränderlichen IDs und Backups.
5. **Suche** als gesondert skalierbarer Volltext-/Facettenindex mit Synonymen, Klassifikationen und Sprachvarianten.
6. **Wissensgraph** als überprüfbare abgeleitete Relationenschicht, nicht als unkontrollierte zweite Quelle klinischer Fakten.
7. **Importpipeline** entkoppelt, deterministisch, idempotent, delta-basiert, mit Checkpoints, Wiederanlauf, Queue/Batch-Verarbeitung und Audit. Release-/Sicherheitsgates müssen bei wachsender Frequenz wirksam bleiben.
8. **Evidenzüberwachung** als skalierbare PubMed-/Guideline-/Retraction-Surveillance mit Quellenstatus, Fristen, KI-Prüfaudit und menschlicher Eskalation.
9. **Observability/SRE** mit SLIs für Datenbanklatenz, Fehlerrate, Importdauer, Suchindex-Lag, Medienabrufe, Kapazität, Kostentrend, Wiederherstellungszeit, Lizenz-/Safety-Fehler und Publikationsrücknahmen.
10. **Disaster Recovery** inklusive wiederkehrender Restore-Tests und nachweisbarer RPO/RTO-Ziele.

### Wachstumsmeilensteine als Planung, nicht als faktische Zusage

- Erste **100–1.000** Artikel: Import, Schema, Renderer, Review- und Monitoringbasis absichern.
- **10.000+** Artikel: Suche, Medien/CDN, DB-Indizes und Backup-Performance messen und optimieren.
- **100.000+** Artikel: technische Entkopplung prüfen, Last-/Restore-/Migrationssimulationen.
- **1.000.000+** Artikel: horizontale Serving- und Storage-Kapazität nach tatsächlichen Metriken, Kostenprognose und getesteten Wiederherstellungswegen dimensionieren.

Der Artikelfluss soll **nicht** durch eine numerische Grenze gestoppt werden, sondern höchstens bei objektivem Sicherheits-/Qualitätsrisiko oder aktuell fehlender betrieblicher Kapazität pausieren, bis diese zuverlässig ausgebaut ist.

## 7. Migrationsverträglichkeit mit aktuellem WikiMedica

Aktuell gilt: `/opt/wikimedica-source` → systemd `wikimedica-beta-sync.timer` täglich **06:30 Europe/Berlin** → `--env production --mode beta-local` → `wikimedica_app`. Der Pilot **Arterielle Hypertonie** ist bestätigt live; der Importer erlaubt aktuell nur bestimmte `content/`-Ordner und Artikeltypen. Eine neue Domäne wird durch dieses Konzeptdokument **noch nicht automatisch importiert**.

Technische Folge-PRs müssen deshalb im Testbetrieb und mit Bestandsschutz behandeln:

- Optionales `knowledge_domain` und Beziehungs-/Alias-Metadaten in `data/metadata/article-schema.yaml`, ohne bestehende Artikel zu brechen.
- Domänenspezifische Vorlagen, Validierungsregeln und Risikogates.
- Neue Content-Ordner in Git-Diff-Auswahl und Importer-Allowlist **gemeinsam** freischalten; sonst werden Artikel nach Merge nicht importiert.
- MediaWiki-Kategorien, interne Verlinkungen, Redirect-Handling und Patienten-/Fachansichten mit Integrationstests.
- Monitoring, Revision-Readback und verlässliche Sicherheits-Rücknahme.
- Keine Änderungen am produktiven Docker-/DB-Aufbau ohne eigene Migrationsfreigabe.

## 8. Verbindlicher Abschlussbericht nach der ersten großen Etappe

**Auslöser:** Nach Erstellung, Prüfung, Merge und technisch bestätigter Veröffentlichung der ersten großen redaktionellen Etappe (100 Erkrankungen und 100 Wirkstoffe inkl. geprüfter Handelsnamen-Verweise; soweit Freigaben vorliegen zusätzlich PubMed-basierte Artikel). **Nicht** vorzeitig einen abgeschlossenen Launch behaupten, wenn nur Entwürfe oder offene PRs existieren.

Der Abschlussbericht muss zwingend einen eigenständigen Abschnitt **„Frühzeitige infrastrukturelle Anpassung für unbegrenztes medizinisches Inhaltswachstum“** enthalten.

### Nachweispflichtiger Berichtsinhalt

1. Zahl und Qualitätsstatus aller **tatsächlich veröffentlichten** Seiten, Erkrankungen, Wirkstoffe, Handelsnamen-Redirects, sonstiger Domänen, Gesamtartikel und ausstehender PRs.
2. Quellen-/Evidence-Reife, Reviewrückstand, KI-Checks, Hochrisiko-Freigaben, BETA-Kennzeichnungen, Aktualitätsquoten.
3. **Gemessene** Ressourcen: Datenbankgröße und Wachstum, Medienvolumen, Suchindex, CPU/RAM/Swap, Storage/IOPS, Importdauer und Fehler, Seitenauslieferung, Restore-Zeit; bei nicht erhobenen Kennzahlen ausdrücklich `noch nicht gemessen`.
4. **Prognose und Szenarien** für 10.000, 100.000, 1.000.000 und mehr Artikel anhand nachvollziehbarer Annahmen; keine linear extrapolierten falschen Kosten- oder Leistungsversprechen.
5. **Priorisierte technische Maßnahmen** und Entscheidungen: modulare Inhalts-/Metadatenbasis, Objekt-Storage, Suchindex, DB-Strategie, verteilte Importjobs, Wissensgraph, CDN, Observability, Backups/Disaster Recovery, Secretmanagement und redaktionelle Überwachung.
6. **Roadmap mit Abhängigkeiten, Risiko, Betriebsunterbrechungsfreiheit soweit möglich, geschätztem Ressourcenaufwand und Abnahmekriterien**; Trennung `jetzt erforderlich`, `nach Messung`, `langfristige Option`.
7. Einen ausdrücklich hervorgehobenen Satz: **„WikiMedica kennt keine fest definierte Obergrenze des medizinischen Wissensbestands; Infrastruktur und Qualitätssicherung müssen frühzeitig so vorbereitet werden, dass weitere fachliche Domänen und Millionen von Artikeln möglich bleiben.“**

**Redaktionsverantwortung:** Abschlussbericht erst auf realen Commits, gemergten PRs, Logs und tatsächlichen Live-Seiten aufbauen. Codex/Claude Code sollen die Anforderungen in künftigen Handovern und Berichten weitertragen.

## 9. Kurzfassung für nachfolgende Agenten

**Nicht bei 100 oder 1.000.000 Artikeln stoppen.** WikiMedica soll nach Quellenlage in der gesamten Medizin weiterwachsen. Künstliche Themen-/Artikelgrenzen sind unerwünscht. Die Serverkapazität ist erweiterbar, aber nicht kostenlos oder ohne Migrationsrisiko. Entwickle möglichst früh eine nach und nach realisierbare modulare Architektur; sichere die aktuelle BETA-Veröffentlichung; dokumentiere die Skalierungsstrategie **verpflichtend im Abschlussbericht der ersten großen Etappe**.
