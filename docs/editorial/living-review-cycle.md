# WikiMedica: Living Review Cycle (jährlich + neue Evidenz)

**Stand:** 2026-10-11 · **Beschlossenes Zielmodell für die Beta-Phase**  
**Geltungsbereich:** alle öffentlich sichtbaren WikiMedica-Artikel, einschließlich Beta-Artikel.

## Grundregel

Jeder Artikel wird **spätestens nach zwölf Monaten** einer dokumentierten Aktualitätsprüfung unterzogen. Zusätzlich wird eine neue Prüfung angestoßen, wenn ein neuer relevanter PubMed-Eintrag, eine aktualisierte Leitlinie, eine Korrektur/Retraction oder eine relevante Arzneimittelsicherheitsmeldung erkannt wird.

Eine aktuelle Publikation ist **zunächst ein Prüfhinweis** und nicht automatisch ein Beweis, dass der Artikel geändert werden muss.

## Vier Ergebnisse eines Aktualitätschecks

| Ergebnis | Handlung | Muss ein Mensch fachlich prüfen? |
| --- | --- | --- |
| NO_CHANGE | Aktuelle Evidenz und Leitlinien ausreichend geprüft, keine relevante Änderung nötig. Aktualitätsprüfdatum dokumentieren; nächster Check spätestens +12 Monate. | Nein, wenn der vollständige Quellenabgleich nachweislich erfolgt ist. |
| UPDATE_REQUIRED | Änderungen in Empfehlungen, Klassifikationen, Studienlage, Sicherheitsdaten oder belastbaren Angaben nötig. PR mit neuem Entwurf und konkreter Änderungsliste anlegen. | **Ja**, vor dem nächsten produktiven Text-Update. |
| UNCERTAIN | Evidenz oder Quellenabdeckung unklar bzw. widersprüchlich; die KI kann die Unverändertheit nicht sicher beurteilen. | **Ja**. Termin wird nicht verlängert. |
| SAFETY_ALERT | Sicherheitswarnung, neue Kontraindikation, relevante Retraction oder unmittelbar problematische Aussage. | **Unverzüglich**, mit klinischer Eskalation. Kein automatisches Weiterlaufen unveränderter Empfehlungen ohne Eskalation. |

## Datumsfelder bewusst trennen

- **Medizinisches Fachreview:** Datum einer tatsächlichen namentlichen menschlichen Review. **Nie** durch den KI-Agenten überschreiben oder fingieren.
- **Textstand (\`updated\`):** Datum einer wirklichen inhaltlichen Artikeländerung; bleibt bei NO_CHANGE unverändert.
- **Letzte Evidenzprüfung (\`evidence_checked_at\`):** Datum des tatsächlich erfolgreich durchgeführten KI-/Quellenchecks.
- **Nächste Evidenzprüfung (\`next_evidence_check\`):** bei NO_CHANGE zwölf Monate nach \`evidence_checked_at\`; durch neue Erkenntnisse jederzeit vorziehbar.

Die letzten zwei Informationen werden in einer **separaten Audit-Akte** geführt und nicht als stille Änderung am eingefrorenen Artikel-Frontmatter gespeichert. So bleibt die bisherige Freigabe auf genau den veröffentlichten Text bezogen. Für die Beta-Version kann eine MediaWiki-Infobox künftig beide Datentypen unabhängig anzeigen: „Letzte Aktualitätsprüfung (KI)“ und „Fachlich geprüft am“.

## Technische Architektur

1. Täglicher PubMed-/Leitlinien-Import und Erfassung neuer PMIDs / Versionen. Der Scan muss erfolgreich und aktuell sein.
2. Mapping zu betroffenen Artikeln anhand MeSH, Fachgebiet, Synonymen, ICD/ATC und bereits verwendeten Quellen. Treffer nur als **Kandidaten** behandeln; unzureichend zugeordnete Evidenz kann nicht als „nichts Neues“ gewertet werden.
3. Fristen prüfen; spätestens nach zwölf Monaten alle seit dem letzten Check neu hinzugekommenen Quellen und geltenden Leitlinien in das Quellenpaket aufnehmen.
4. Der KI-Evidenzagent prüft den aktuellen **veröffentlichten Artikelstand** gegen das verifizierte Paket, benennt die geprüften Quellen und liefert ein strukturiertes Ergebnis mit Begründung.
5. Bei NO_CHANGE wird das Ergebnis mit Artikel-Commit-Hash und Quellenprüfung in einer append-only-Audit-Akte protokolliert. Die nächste Frist wird um zwölf Monate verlängert.
6. Bei UPDATE_REQUIRED/UNCERTAIN/SAFETY_ALERT wird ein konkreter GitHub-Issue-/PR-Auftrag mit Quellen und Änderungsvorschlägen für einen Fachreview vorbereitet.
7. Bei fehlendem PubMed-Import, veralteten Quellen, nicht erreichbaren Leitlinien, fehlgeschlagener Modellprüfung oder niedrigem Vertrauen: **keine automatische Fristverlängerung**.
8. Eine neue Publikation nach einem NO_CHANGE-Ergebnis kann jederzeit eine vorgezogene Untersuchung auslösen.

## Ersteinführung im Repository

- \`scripts/review/evidence_review_tracker.py\` verwaltet Fristen und eine separate nachvollziehbare Evidenz-Akte.
- Der Aufruf \`scan\` erstellt die Arbeitswarteschlange für den Evidenzagenten.
- Der Aufruf \`record --result-json ...\` nimmt einen nachweislich von einem Modell bearbeiteten, strukturierten Prüfbericht entgegen und ermittelt den nächsten Fälligkeitstermin.
- **Noch nicht enthalten:** ein angebundenes und validiertes KI-Modell, flächendeckendes PubMed-Artikel-Mapping und automatisiertes Verfassen von Änderungen-PRs. Diese Funktionen dürfen erst nach tatsächlicher Implementierung als „aktiv“ bezeichnet werden.

## Mindestinhalt eines NO_CHANGE-Prüfberichts

- eindeutiger Artikel-Slug und unveränderter Hash des geprüften Artikels,
- verwendetes Modell, Version/Konfiguration und Zeitpunkt,
- Stand, Abdeckung und erfolgreiche Ausführung der PubMed-/Leitlinien-Recherche,
- Liste der geprüften PMIDs und Leitlinienversionen bzw. ein belegbarer vollständiger Suchnachweis,
- Begründung, warum bestehende Aussagen weiterhin zutreffen,
- festgestellte Unsicherheiten und Angabe, dass **keine** sicherheitsrelevante Änderung vorliegt,
- \`decision: no_change\` nur bei hinreichend hoher Sicherheit.

**Wichtig:** Der Termin wird nur bei einer tatsächlich durchgeführten und protokollierten Prüfung verlängert – niemals lediglich, weil ein täglicher Job gelaufen ist oder keine Treffer gemeldet hat.
