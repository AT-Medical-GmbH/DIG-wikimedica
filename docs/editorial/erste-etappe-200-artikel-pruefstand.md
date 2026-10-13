# Prüfliste: Erste Etappe mit 200 WikiMedica-Artikeln

Stand: 13. Oktober 2026

## Zweck und Begriffe

Diese Prüfliste trennt technische Erstellung, Zusammenführung, BETA-Import und medizinische Freigabe. Sie ist kein Nachweis eines Peer Reviews und keine medizinische Freigabe.

| Status | Bedeutung |
| --- | --- |
| technisch erstellt | Markdown, Metadaten und lokale technische Validierung liegen vor |
| in `main` | Der Quellstand ist in GitHub `main` zusammengeführt |
| BETA sichtbar | MediaWiki-Import und erneutes Auslesen der konkreten Seite wurden nachgewiesen |
| medizinisch freigegeben | Dokumentiertes fachärztliches und bei Arzneimitteln pharmazeutisches Review liegt vor |

## Kanonische Erkrankungsartikel

| IDs | Anzahl | Quellenstand | GitHub-PR | in `main` |
| --- | ---: | --- | --- | --- |
| WM-DIS-0001 | 1 | Pilotartikel | historischer Pilotimport | ja |
| WM-DIS-0002–0011 | 10 | KI-Erstentwürfe; medizinische Freigabe offen | [#271](https://github.com/AT-Medical-GmbH/DIG-wikimedica/pull/271) | ja |
| WM-DIS-0012–0021 | 10 | quellenbasierte BETA-Erstentwürfe; medizinische Freigabe offen | [#275](https://github.com/AT-Medical-GmbH/DIG-wikimedica/pull/275) | ja |
| WM-DIS-0022–0031 | 10 | quellenbasierte BETA-Erstentwürfe; medizinische Freigabe offen | [#276](https://github.com/AT-Medical-GmbH/DIG-wikimedica/pull/276) | ja |
| WM-DIS-0032–0041 | 10 | quellenbasierte BETA-Erstentwürfe; medizinische Freigabe offen | [#277](https://github.com/AT-Medical-GmbH/DIG-wikimedica/pull/277) | ja |
| WM-DIS-0042–0051 | 10 | quellenbasierte BETA-Erstentwürfe; medizinische Freigabe offen | [#278](https://github.com/AT-Medical-GmbH/DIG-wikimedica/pull/278) | ja |
| WM-DIS-0052–0061 | 10 | quellenbasierte BETA-Erstentwürfe; medizinische Freigabe offen | [#279](https://github.com/AT-Medical-GmbH/DIG-wikimedica/pull/279) | ja |
| WM-DIS-0062–0071 | 10 | quellenbasierte BETA-Erstentwürfe; medizinische Freigabe offen | [#280](https://github.com/AT-Medical-GmbH/DIG-wikimedica/pull/280) | ja |
| WM-DIS-0072–0081 | 10 | quellenbasierte BETA-Erstentwürfe; medizinische Freigabe offen | [#281](https://github.com/AT-Medical-GmbH/DIG-wikimedica/pull/281) | ja |
| WM-DIS-0082–0091 | 10 | quellenbasierte BETA-Erstentwürfe; medizinische Freigabe offen | [#282](https://github.com/AT-Medical-GmbH/DIG-wikimedica/pull/282) | ja |
| WM-DIS-0092–0100 | 9 | quellenbasierte BETA-Erstentwürfe; medizinische Freigabe offen | [#283](https://github.com/AT-Medical-GmbH/DIG-wikimedica/pull/283) | ja |

**Zwischensumme Erkrankungen: 100 technisch erstellte und in `main` zusammengeführte Artikel.**

## Kanonische Wirkstoffartikel

| IDs | Anzahl | Quellenstand | GitHub-PR | in `main` |
| --- | ---: | --- | --- | --- |
| WM-DRUG-0001–0010 | 10 | Hochrisiko-Entwürfe; fachärztliche und pharmazeutische Freigabe offen | [#284](https://github.com/AT-Medical-GmbH/DIG-wikimedica/pull/284) | ja |
| WM-DRUG-0011–0020 | 10 | Hochrisiko-Entwürfe; fachärztliche und pharmazeutische Freigabe offen | [#285](https://github.com/AT-Medical-GmbH/DIG-wikimedica/pull/285) | ja |
| WM-DRUG-0021–0030 | 10 | Hochrisiko-Entwürfe; fachärztliche und pharmazeutische Freigabe offen | [#286](https://github.com/AT-Medical-GmbH/DIG-wikimedica/pull/286) | ja |
| WM-DRUG-0031–0040 | 10 | Hochrisiko-Entwürfe; fachärztliche und pharmazeutische Freigabe offen | [#287](https://github.com/AT-Medical-GmbH/DIG-wikimedica/pull/287) | ja |
| WM-DRUG-0041–0050 | 10 | Hochrisiko-Entwürfe; fachärztliche und pharmazeutische Freigabe offen | [#288](https://github.com/AT-Medical-GmbH/DIG-wikimedica/pull/288) | ja |
| WM-DRUG-0051–0060 | 10 | technisch validierte Hochrisiko-Entwürfe; Freigabe offen | [#290](https://github.com/AT-Medical-GmbH/DIG-wikimedica/pull/290) | ja |
| WM-DRUG-0061–0070 | 10 | technisch validierte Hochrisiko-Entwürfe; Freigabe offen | [#291](https://github.com/AT-Medical-GmbH/DIG-wikimedica/pull/291) | ja |
| WM-DRUG-0071–0080 | 10 | technisch validierte Hochrisiko-Entwürfe; Freigabe offen | [#292](https://github.com/AT-Medical-GmbH/DIG-wikimedica/pull/292) | ja |
| WM-DRUG-0081–0090 | 10 | technisch validierte Hochrisiko-Entwürfe; Freigabe offen | [#293](https://github.com/AT-Medical-GmbH/DIG-wikimedica/pull/293) | ja |
| WM-DRUG-0091–0100 | 10 | technisch validierte Hochrisiko-Entwürfe; Freigabe offen | [#294](https://github.com/AT-Medical-GmbH/DIG-wikimedica/pull/294) | ja |

**Zwischensumme Wirkstoffe: 100 technisch erstellte und in `main` zusammengeführte Artikel.**

## Nachweise und noch erforderliche Schritte

1. Die lokale Metadatenprüfung der fünf Wirkstoffpakete ergab jeweils keine Fehler und keine Warnungen; `git diff --check` war ebenfalls erfolgreich.
2. GitHub Actions konnten für diese Pakete nicht ausgeführt werden: die zugehörigen Jobs endeten ohne gestartete Schritte. Dieser Plattformblocker ersetzt keine technische Freigabe; lokale Prüfprotokolle bleiben erhalten.
3. Vor einer BETA-Sichtbarkeitsbehauptung ist je Import die gespeicherte MediaWiki-Seite erneut zu lesen und der Importstatus mit dem konkreten Git-Commit abzugleichen.
4. Ein `safety_hold` oder Status `draft` darf nicht in eine medizinische beziehungsweise pharmazeutische Freigabe umgedeutet werden. Der vorhandene BETA-Importer blockiert Inhalte mit `safety_hold: true` technisch.

## Zählstand

| Kategorie | technisch erstellt | in `main` | BETA sichtbar nachgewiesen | medizinisch freigegeben |
| --- | ---: | ---: | ---: | ---: |
| Erkrankungen | 100 | 100 | separat je Seite zu prüfen | 0 nachgewiesen |
| Wirkstoffe | 100 | 100 | 0 nachgewiesen | 0 nachgewiesen |
| **Gesamt** | **200** | **200** | **nicht pauschal belegbar** | **0 nachgewiesen** |

Diese Tabelle wird erst nach einem aktuellen, seitenbezogenen MediaWiki-Readback angepasst.
