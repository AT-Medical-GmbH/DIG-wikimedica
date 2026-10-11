# WikiMedica – Redaktions-Backlog für 100 Launch-Erkrankungsartikel

**Stand:** 2026-10-11 · **Status:** Fachredaktioneller Kandidatenpool (keine statistische Rangliste)  
**Ziel:** Je 100 eigenständige, vollständige Fachartikel mit deutschsprachigen Patientenabschnitten dort, wo dies sinnvoll ist.

Die Reihenfolge ist eine redaktionelle Arbeitsreihenfolge, **keine** empirisch geprüfte Rangfolge nach Prävalenz oder Verordnungszahlen. Vor finaler Priorisierung sind repräsentative deutsche Epidemiologiedaten (RKI, GBE, Destatis), die jeweilige Messdefinition, Altersgruppe, Zeitraum und Versorgungslast zu dokumentieren. Der PubMed-Korpus mit aktuell 1.664 PMIDs wird pro Thema als Quellenkandidat gemappt. Einzelpublikationen ersetzen nicht die Synthese aktueller Leitlinien und regulatorischer Informationen.

## Arbeitsablauf

1. Thema auf Dubletten und existierende Artikel prüfen.
2. Literature-to-Article-Agent: PMIDs, MeSH-Cluster, Studienart und Erscheinungsjahr zuordnen; nur thematisch passende Quellen in ein Quellenpaket übernehmen.
3. Ergänzende Quellen: AWMF/NVL, Fachgesellschaften, RKI/GBE/Destatis, WHO, IQWiG und ggf. EMA/BfArM.
4. Vollständigen Artikel im Schema `data/metadata/article-schema.yaml` schreiben. Referenzqualität und Datenstände dokumentieren.
5. Geschlechtsunterschiede explizit prüfen (`sex_gender_relevance`). Für mindestens die im Fokus gekennzeichneten Themen diesen Bereich ausbauen.
6. Menschlicher Hauptautor, unabhängiger Reviewer, ggf. Medical Advisor und abschließender freigegebener Release.
7. Jede Statusänderung und Publikation über GitHub-PR und kontrollierten MediaWiki-Import abwickeln.

## Themenkatalog

| ID | Thema | Bereich | Priorität | Gendermedizin-Fokus |
|---|---|---|---|---|
| WM-DIS-0001 | Arterielle Hypertonie | Kardiologie und Gefäßmedizin | A | Ja |
| WM-DIS-0002 | Fettstoffwechselstörungen (Dyslipidämie) | Kardiologie und Gefäßmedizin | A | Ja |
| WM-DIS-0003 | Koronare Herzkrankheit | Kardiologie und Gefäßmedizin | A | Prüfen |
| WM-DIS-0004 | Akutes Koronarsyndrom und Myokardinfarkt | Kardiologie und Gefäßmedizin | A | Ja |
| WM-DIS-0005 | Chronische Herzinsuffizienz | Kardiologie und Gefäßmedizin | A | Ja |
| WM-DIS-0006 | Vorhofflimmern | Kardiologie und Gefäßmedizin | A | Prüfen |
| WM-DIS-0007 | Schlaganfall | Kardiologie und Gefäßmedizin | A | Ja |
| WM-DIS-0008 | Periphere arterielle Verschlusskrankheit | Kardiologie und Gefäßmedizin | A | Prüfen |
| WM-DIS-0009 | Tiefe Venenthrombose | Kardiologie und Gefäßmedizin | A | Prüfen |
| WM-DIS-0010 | Lungenembolie | Kardiologie und Gefäßmedizin | A | Prüfen |
| WM-DIS-0011 | Aortenklappenstenose | Kardiologie und Gefäßmedizin | A | Prüfen |
| WM-DIS-0012 | Myokarditis | Kardiologie und Gefäßmedizin | A | Prüfen |
| WM-DIS-0013 | Infektiöse Endokarditis | Kardiologie und Gefäßmedizin | A | Prüfen |
| WM-DIS-0014 | Herzklappenerkrankungen | Kardiologie und Gefäßmedizin | A | Prüfen |
| WM-DIS-0015 | Orthostatische Hypotonie | Kardiologie und Gefäßmedizin | A | Prüfen |
| WM-DIS-0016 | Diabetes mellitus Typ 2 | Endokrinologie und Stoffwechsel | A | Ja |
| WM-DIS-0017 | Diabetes mellitus Typ 1 | Endokrinologie und Stoffwechsel | A | Prüfen |
| WM-DIS-0018 | Adipositas | Endokrinologie und Stoffwechsel | A | Ja |
| WM-DIS-0019 | Metabolisches Syndrom | Endokrinologie und Stoffwechsel | A | Prüfen |
| WM-DIS-0020 | Gicht | Endokrinologie und Stoffwechsel | A | Prüfen |
| WM-DIS-0021 | Hypothyreose | Endokrinologie und Stoffwechsel | A | Prüfen |
| WM-DIS-0022 | Hyperthyreose | Endokrinologie und Stoffwechsel | A | Prüfen |
| WM-DIS-0023 | Osteoporose | Endokrinologie und Stoffwechsel | A | Ja |
| WM-DIS-0024 | Vitamin-D-Mangel | Endokrinologie und Stoffwechsel | A | Prüfen |
| WM-DIS-0025 | Primärer Hyperparathyreoidismus | Endokrinologie und Stoffwechsel | A | Prüfen |
| WM-DIS-0026 | Polyzystisches Ovarialsyndrom | Endokrinologie und Stoffwechsel | A | Ja |
| WM-DIS-0027 | Metabolische dysfunktionsassoziierte steatotische Lebererkrankung (MASLD) | Endokrinologie und Stoffwechsel | A | Prüfen |
| WM-DIS-0028 | Schilddrüsenknoten | Endokrinologie und Stoffwechsel | A | Prüfen |
| WM-DIS-0029 | Hypoglykämie | Endokrinologie und Stoffwechsel | A | Prüfen |
| WM-DIS-0030 | Diabetische Polyneuropathie | Endokrinologie und Stoffwechsel | A | Prüfen |
| WM-DIS-0031 | Chronisch obstruktive Lungenerkrankung (COPD) | Pneumologie und HNO | A | Prüfen |
| WM-DIS-0032 | Asthma bronchiale | Pneumologie und HNO | A | Prüfen |
| WM-DIS-0033 | Pneumonie | Pneumologie und HNO | A | Prüfen |
| WM-DIS-0034 | Obstruktive Schlafapnoe | Pneumologie und HNO | A | Prüfen |
| WM-DIS-0035 | Allergische Rhinitis | Pneumologie und HNO | A | Prüfen |
| WM-DIS-0036 | Idiopathische Lungenfibrose | Pneumologie und HNO | A | Prüfen |
| WM-DIS-0037 | Respiratorische Insuffizienz | Pneumologie und HNO | A | Prüfen |
| WM-DIS-0038 | Akute Bronchitis | Pneumologie und HNO | A | Prüfen |
| WM-DIS-0039 | Bronchialkarzinom | Pneumologie und HNO | A | Ja |
| WM-DIS-0040 | Pulmonale Hypertonie | Pneumologie und HNO | A | Prüfen |
| WM-DIS-0041 | Depressive Störung | Neurologie und Psychiatrie | A | Ja |
| WM-DIS-0042 | Angststörungen | Neurologie und Psychiatrie | A | Ja |
| WM-DIS-0043 | Alzheimer-Demenz | Neurologie und Psychiatrie | A | Ja |
| WM-DIS-0044 | Morbus Parkinson | Neurologie und Psychiatrie | B | Prüfen |
| WM-DIS-0045 | Migräne | Neurologie und Psychiatrie | A | Ja |
| WM-DIS-0046 | Epilepsie | Neurologie und Psychiatrie | B | Prüfen |
| WM-DIS-0047 | Multiple Sklerose | Neurologie und Psychiatrie | A | Ja |
| WM-DIS-0048 | Transitorische ischämische Attacke | Neurologie und Psychiatrie | B | Prüfen |
| WM-DIS-0049 | Periphere Neuropathie | Neurologie und Psychiatrie | B | Prüfen |
| WM-DIS-0050 | Insomnie | Neurologie und Psychiatrie | B | Prüfen |
| WM-DIS-0051 | Aufmerksamkeitsdefizit-/Hyperaktivitätsstörung | Neurologie und Psychiatrie | B | Prüfen |
| WM-DIS-0052 | Bipolare Störung | Neurologie und Psychiatrie | B | Prüfen |
| WM-DIS-0053 | Alkoholkonsumstörung | Neurologie und Psychiatrie | B | Prüfen |
| WM-DIS-0054 | Schizophrenie | Neurologie und Psychiatrie | B | Prüfen |
| WM-DIS-0055 | Neuropathischer Schmerz | Neurologie und Psychiatrie | A | Ja |
| WM-DIS-0056 | Gastroösophageale Refluxkrankheit | Gastroenterologie | B | Prüfen |
| WM-DIS-0057 | Helicobacter-pylori-Gastritis | Gastroenterologie | B | Prüfen |
| WM-DIS-0058 | Ulkuskrankheit | Gastroenterologie | B | Prüfen |
| WM-DIS-0059 | Reizdarmsyndrom | Gastroenterologie | B | Prüfen |
| WM-DIS-0060 | Morbus Crohn | Gastroenterologie | B | Prüfen |
| WM-DIS-0061 | Colitis ulcerosa | Gastroenterologie | B | Prüfen |
| WM-DIS-0062 | Divertikelkrankheit | Gastroenterologie | B | Prüfen |
| WM-DIS-0063 | Cholezystolithiasis | Gastroenterologie | B | Prüfen |
| WM-DIS-0064 | Akute Pankreatitis | Gastroenterologie | B | Prüfen |
| WM-DIS-0065 | Leberzirrhose | Gastroenterologie | B | Prüfen |
| WM-DIS-0066 | Chronische Nierenkrankheit | Nephrologie und Urologie | B | Prüfen |
| WM-DIS-0067 | Akute Nierenschädigung | Nephrologie und Urologie | B | Prüfen |
| WM-DIS-0068 | Harnwegsinfektion | Nephrologie und Urologie | B | Prüfen |
| WM-DIS-0069 | Pyelonephritis | Nephrologie und Urologie | B | Prüfen |
| WM-DIS-0070 | Urolithiasis | Nephrologie und Urologie | B | Prüfen |
| WM-DIS-0071 | Benigne Prostatahyperplasie | Nephrologie und Urologie | B | Prüfen |
| WM-DIS-0072 | Harninkontinenz | Nephrologie und Urologie | B | Prüfen |
| WM-DIS-0073 | Prostatakarzinom | Nephrologie und Urologie | B | Prüfen |
| WM-DIS-0074 | Nierenzellkarzinom | Nephrologie und Urologie | B | Prüfen |
| WM-DIS-0075 | Nephrotisches Syndrom | Nephrologie und Urologie | B | Prüfen |
| WM-DIS-0076 | Unspezifischer Kreuzschmerz | Orthopädie, Rheumatologie und Dermatologie | B | Prüfen |
| WM-DIS-0077 | Gonarthrose | Orthopädie, Rheumatologie und Dermatologie | B | Prüfen |
| WM-DIS-0078 | Rheumatoide Arthritis | Orthopädie, Rheumatologie und Dermatologie | A | Ja |
| WM-DIS-0079 | Fibromyalgiesyndrom | Orthopädie, Rheumatologie und Dermatologie | B | Prüfen |
| WM-DIS-0080 | Atopisches Ekzem | Orthopädie, Rheumatologie und Dermatologie | B | Prüfen |
| WM-DIS-0081 | Psoriasis | Orthopädie, Rheumatologie und Dermatologie | B | Prüfen |
| WM-DIS-0082 | Akne vulgaris | Orthopädie, Rheumatologie und Dermatologie | B | Prüfen |
| WM-DIS-0083 | Axiale Spondyloarthritis | Orthopädie, Rheumatologie und Dermatologie | B | Prüfen |
| WM-DIS-0084 | Sarkopenie | Orthopädie, Rheumatologie und Dermatologie | B | Prüfen |
| WM-DIS-0085 | Karpaltunnelsyndrom | Orthopädie, Rheumatologie und Dermatologie | B | Prüfen |
| WM-DIS-0086 | Influenza | Infektiologie | B | Prüfen |
| WM-DIS-0087 | COVID-19 | Infektiologie | B | Prüfen |
| WM-DIS-0088 | Akute infektiöse Gastroenteritis | Infektiologie | B | Prüfen |
| WM-DIS-0089 | Sepsis | Infektiologie | B | Prüfen |
| WM-DIS-0090 | HIV-Infektion | Infektiologie | B | Prüfen |
| WM-DIS-0091 | Endometriose | Frauenheilkunde und Gendermedizin | A | Ja |
| WM-DIS-0092 | Hypertensive Schwangerschaftserkrankungen | Frauenheilkunde und Gendermedizin | A | Ja |
| WM-DIS-0093 | Gestationsdiabetes | Frauenheilkunde und Gendermedizin | A | Ja |
| WM-DIS-0094 | Wechseljahresassoziierte Beschwerden | Frauenheilkunde und Gendermedizin | A | Ja |
| WM-DIS-0095 | Mammakarzinom | Frauenheilkunde und Gendermedizin | A | Ja |
| WM-DIS-0096 | Kolorektales Karzinom | Weitere häufige oder versorgungsrelevante Themen | B | Prüfen |
| WM-DIS-0097 | Eisenmangelanämie | Weitere häufige oder versorgungsrelevante Themen | B | Prüfen |
| WM-DIS-0098 | Glaukom | Weitere häufige oder versorgungsrelevante Themen | B | Prüfen |
| WM-DIS-0099 | Altersabhängige Makuladegeneration | Weitere häufige oder versorgungsrelevante Themen | B | Prüfen |
| WM-DIS-0100 | Chronisches Schmerzsyndrom | Weitere häufige oder versorgungsrelevante Themen | B | Prüfen |

## Mindestbelege pro Artikel

- Mindestens eine einschlägige **aktuelle und gültige Leitlinie** (falls verfügbar), mit Stand und Geltungsgebiet.
- Aktuelle deutsche epidemiologische Quelle, sofern vorhanden; Angaben zum Datenjahr und Nenner.
- Klinische Aussagen mit überprüfbaren Originalquellen oder systematischen Übersichten.
- Bei Therapien: aktuelle Zulassung/Fachinformationen und kontrollierte Hochrisiko-Freigaben.
- Ausgewiesene Ausnahmen, Unsicherheit, Schwangerschaft/Stillzeit, geriatrische und renale Aspekte bei Relevanz.
- Jede wesentliche Behauptung mit fortlaufend nummeriertem Literaturhinweis.

## Meilensteine

- **Pilot:** Arterielle Hypertonie – PR #261; explizit noch im Zustand `draft`.
- **Thematischer Schwerpunkt Oktober/November 2026:** Gendermedizin – PR #262; nach medizinischer und technischer Freigabe auf der Startseite.
- **Quellenindex und Priorisierung:** PR #260; der PubMed-Korpus umfasst 1.664 PMIDs.
- **Batch 1:** WM-DIS-0001 bis 0020, danach 0021 bis 0040, schließlich 0041 bis 0100.

## Offene Entscheidungen

Die volle Publikationsfähigkeit hängt von Reviewer-Verfügbarkeit, tatsächlicher GitHub-Teamkonfiguration, juristischer Freigabe der Disclaimers und der erfolgreichen Staging-Abnahme ab. Keine der 100 Artikelfreigaben darf aus einem automatischen Test allein abgeleitet werden.
