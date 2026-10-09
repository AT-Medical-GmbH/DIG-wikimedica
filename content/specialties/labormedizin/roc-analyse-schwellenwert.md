---
title: ROC-Analyse und Schwellenwerte
slug: roc-analyse-schwellenwert
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

# ROC-Analyse und Schwellenwerte

Viele Testergebnisse sind kontinuierliche Messwerte (z. B. Laborwerte). Für eine ja/nein-Entscheidung wird ein **Schwellenwert** (Trenngröße) festgelegt: Liegt der Messwert darüber, gilt der Befund als positiv. Jedem Schwellenwert gehören bestimmte Werte für Sensitivität und Spezifität.

## ROC-Kurve

Trägt man für jeden Schwellenwert den Anteil falsch positiver Befunde (1 − Spezifität) auf der x-Achse gegen den Anteil richtig positiver Befunde (Sensitivität) auf der y-Achse ab und verbindet die Punkte, entsteht die **ROC-Kurve** (*receiver operating characteristic*, ursprünglich ein Begriff der Nachrichtentechnik für Signalerkennung). Es besteht ein Zielkonflikt:

- Ein *niedriger* Schwellenwert klassifiziert viele Personen als positiv: hohe Sensitivität, aber viele falsch positive Befunde (niedrige Spezifität).
- Ein *hoher* Schwellenwert ergibt für die meisten Gesunden und relativ viele Kranke einen negativen Befund: hohe Spezifität, aber mehr falsch negative Befunde.

Gut trennende Schwellenwerte liegen in der oberen linken Ecke der Kurve.

## Fläche unter der Kurve (AUC)

Die Güte des Tests wird durch die Fläche unter der ROC-Kurve (*area under the curve*, AUC) beschrieben. Sie erreicht 1, wenn ein Schwellenwert Kranke und Nichtkranke perfekt trennt (praktisch kaum der Fall); eine AUC von 0,5 bedeutet, dass der Test nicht besser ist als eine zufällige Zuordnung.

## Optimaler Schwellenwert

Wenn Sensitivität und Spezifität als gleich wichtig gelten, kann der Schwellenwert mit dem größten Youden-Index gewählt werden. Allgemein hängt der optimale Wert von den Folgen falscher Befunde ab: Ein falsch negativer Befund kann fatale Folgen haben, weil die Erkrankung zu spät oder gar nicht behandelt wird; falsch positive Befunde belasten Betroffene und führen zu unnötigen, teuren und mitunter gefährlichen Folgemaßnahmen. Das Lehrbuch erläutert dies am Beispiel der Kreatinkinase zur Diagnose des Myokardinfarkts (AUC 0,94 in der dort beschriebenen Studie).

## Siehe auch

- [Gütekriterien diagnostischer Tests](guetekriterien-diagnostischer-tests.md)

## Literatur

1. Weiß C: Basiswissen Medizinische Statistik. 6. Aufl., Springer, 2013, Kap. 14.1.3.
