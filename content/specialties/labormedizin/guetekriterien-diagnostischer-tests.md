---
title: Gütekriterien diagnostischer Tests
slug: guetekriterien-diagnostischer-tests
specialty: Labormedizin
secondary_specialties:
- Prävention/Public Health
article_type: professional
content_kind: article
status: draft
version: 0.1.0
change_summary: Erstentwurf aus Lehrbuchquelle (KI-gestützt), noch ungeprüft.
authors:
- name: Wikimedica-Redaktion (KI-gestützter Entwurf)
reviewers: []
created: '2026-10-09'
updated: '2026-10-09'
risk_level: low
target_audience:
- physicians
- medical-professionals
sex_gender_relevance: not_assessed
icd10: []
pubmed_ids: []
guidelines: []
references:
- citation: Weiß C. Basiswissen Medizinische Statistik. 6., überarb. Aufl. Springer-Verlag, Berlin Heidelberg;
    2013. doi:10.1007/978-3-642-34261-5. Kapitel 14.1 (Diagnosestudien).
source_notes: Eigene Zusammenfassung und Neuformulierung aus Abschnitt 14.1.1–14.1.3 des Lehrbuchs Basiswissen
  Medizinische Statistik (6. Aufl., 2013); gelesen wurden diese Abschnitte bis zum Beginn der Diskussion,
  wann hohe Sensitivität bzw. Spezifität gefordert ist. Das Rechenbeispiel in diesem Artikel wurde selbst
  gewählt und nachgerechnet. Kein Text wörtlich übernommen.
language: de
language_level: professional
ai_assisted: true
ai_assistance_description: Entwurf wurde mit KI-Unterstützung (Claude) aus einer gelesenen Lehrbuchquelle
  in eigenen Worten formuliert und strukturiert. Es hat noch keine menschliche fachliche Prüfung stattgefunden;
  Aussagen sind vor Freigabe gegen die Primärliteratur und aktuelle Leitlinien zu verifizieren.
safety_hold: false
wikimedica_credit: true
---

# Gütekriterien diagnostischer Tests

Diagnostische Tests – Labortests, klinische Untersuchungen, bildgebende Verfahren oder Angaben aus der Anamnese – sollen mehr Sicherheit über den Krankheitsstatus einer Person geben. In **Diagnosestudien** wird ihre Güte bewertet. Zu den Gütekriterien zählen die *Validität* (Fähigkeit, zwischen Kranken und Gesunden zu unterscheiden) und die *Reliabilität* (Reproduzierbarkeit der Ergebnisse unter ähnlichen Bedingungen).

## Sensitivität und Spezifität

- **Sensitivität** ist die bedingte Wahrscheinlichkeit, dass der Test bei einer kranken Person positiv ausfällt, P(T+ | K).
- **Spezifität** ist die bedingte Wahrscheinlichkeit, dass eine nicht erkrankte Person ein negatives Ergebnis erhält, P(T− | K−).
- Die Wahrscheinlichkeit eines **falsch negativen** Ergebnisses beträgt 1 − Sensitivität, die eines **falsch positiven** 1 − Spezifität.

Im Idealfall sind beide gleich 1.

## Voraussetzungen einer Diagnosestudie

1. Ein **Goldstandard**, mit dem der wahre Krankheitsstatus bestimmt wird (oft aufwendig, teuer oder riskant, z. B. eine Biopsie; im Alltag werden einfachere Ersatzverfahren benutzt).
2. Hinreichend viele Kranke und Nichtkranke, die sowohl mit dem neuen Test als auch mit dem Goldstandard untersucht werden.
3. **Verblindete** Befundung, damit der Befund unvoreingenommen beurteilt wird.

Sensitivität und Spezifität sollten mit Konfidenzintervall angegeben werden.

## Zusammenfassende Maße

- **Youden-Index** = Sensitivität + Spezifität − 1 (maximal 1; 0 bei einem Test, der nicht besser als der Zufall ist).
- **Kappa-Koeffizient:** Grad der Übereinstimmung mit dem Goldstandard.
- **Likelihood-Quotienten:** positiv = Sensitivität / (1 − Spezifität), negativ = (1 − Sensitivität) / Spezifität. Werte nahe 1 kennzeichnen einen unbrauchbaren Test; als grobe Orientierung gilt bei einem leistungsfähigen Test ein positiver Quotient über 3 und ein negativer unter 1/3.
- *Accuracy* (Anteil korrekter Befunde) ist für die Praxis wenig geeignet, weil sie von der Prävalenz abhängt.

## Vorhersagewerte

Für Behandelnde und Betroffene sind meist die **Vorhersagewerte** wichtiger: der *positive Vorhersagewert* (PPV) ist die Wahrscheinlichkeit, dass bei positivem Test die Krankheit vorliegt, der *negative Vorhersagewert* (NPV) die Wahrscheinlichkeit, dass bei negativem Test keine Krankheit vorliegt. Sie ergeben sich mit dem Satz von Bayes aus Sensitivität, Spezifität und **Prävalenz** (A-priori-Wahrscheinlichkeit; der PPV ist die A-posteriori-Wahrscheinlichkeit).

*Rechenbeispiel (eigenes, fiktiv):* Ein Test habe eine Sensitivität von 90 % und eine Spezifität von 95 %. Bei einer Prävalenz von 1 % liegen auf 1000 getestete Personen 10 Kranke, von denen 9 positiv getestet werden, und 990 Gesunde, von denen etwa 50 falsch positiv getestet werden. Der PPV beträgt dann 9 / 59 ≈ 15 %; der NPV ≈ 99,9 %. Bei einer Prävalenz von 20 % steigt der PPV auf rund 82 %.

Die Vorhersagewerte hängen also stark von der Prävalenz ab: Bei niedriger Prävalenz, etwa im Screening, geht ein großer Teil der positiven Befunde auf gesunde Personen zurück, während ein negativer Befund die Krankheit praktisch ausschließt. Ein positives Ergebnis ist daher zunächst nur ein Hinweis und erfordert weitere Abklärung. Die Quelle weist darauf hin, dass viele Anwender die Umkehrung der bedingten Wahrscheinlichkeiten fälschlich als gleichwertig behandeln.

## Siehe auch

- [ROC-Analyse und Schwellenwerte](roc-analyse-schwellenwert.md)

## Literatur

1. Weiß C: Basiswissen Medizinische Statistik. 6. Aufl., Springer, 2013, Kap. 14.1.
