---
# =============================================================================
# Wikimedica — Patientenartikel-Vorlage (Patient Article Template)
# =============================================================================
# Für Patienten und Angehörige. Einfache Sprache (B1–B2), kein Fachjargon ohne Erklärung.
# Platzhalter {{ ... }} im Text werden beim Import aus den Metadaten ersetzt
# (siehe content/templates/README.md). Alle HTML-Kommentare vor der Freigabe entfernen.
# =============================================================================

title: ""                        # (Pflicht) Vollständiger Titel auf Deutsch
slug: ""                         # (Pflicht) = Dateiname ohne .md; Kleinbuchstaben + Bindestriche; nach Veröffentlichung nie ändern
specialty: ""                    # (Pflicht) Exakter kanonischer Fachgebietsname (siehe content/specialties/README.md)
secondary_specialties: []        # Optional: weitere Fachgebiete (kanonische Namen)
article_type: "patient"          # (Pflicht) Festgelegt
content_kind: "article"          # article | guideline-summary | qr-media-reference
status: "draft"                  # draft | in-review | advisor-review | approved | published | archived (siehe docs/editorial/content-lifecycle.md)

# Versionierung
version: "0.1.0"                 # SemVer; veröffentlichte Artikel >= 1.0.0
change_summary: ""               # Ab "in-review" Pflicht: 1–2 Sätze, was diese Version ändert

related_professional_article: "" # Optional: slug des zugehörigen Fachartikels

# Autorenschaft und Review
authors:                         # (Pflicht) Erste Person = Hauptautor/in
  - name: ""
    email: ""
    orcid: ""
    affiliation: ""

reviewers: []                    # Pflicht ab "advisor-review". Nie die Hauptautor/in; mind. 1 Person unabhängig von allen Autor/innen
  # - name: ""
  #   specialty: ""
  #   reviewed_date: YYYY-MM-DD

medical_advisor: ""              # Pflicht ab "approved" bei risk_level high (darf nicht Autor/in sein)
medical_advisor_signoff_date: "" # Pflicht ab "approved" bei risk_level high (YYYY-MM-DD)

# Datum
created: ""                      # (Pflicht) YYYY-MM-DD
updated: ""                      # (Pflicht) YYYY-MM-DD; bei jeder Änderung aktualisieren
next_review: ""                  # Pflicht ab "approved": YYYY-MM-DD, spätestens 12 Monate nach "updated"

# Risiko, Zielgruppe, Geschlechtersensibilität
risk_level: ""                   # (Pflicht) low | moderate | high — high ist Pflicht für Pharmaka, Therapieprotokolle, Notfall-/Intensivmedizin, Onkologie
target_audience: [patients, relatives]  # (Pflicht) physicians | nursing | emergency-services | pharmacists | medical-professionals | patients | relatives | clinical-teams
sex_gender_relevance: "not_assessed"  # (Pflicht) not_assessed | none | relevant — vor "approved" abschließen
sex_gender_notes: ""             # Pflicht bei "relevant": geschlechtsspezifische Aspekte kurz zusammenfassen
safety_hold: false               # true = Sicherheitsprüfung läuft; Artikel kann dann nicht freigegeben werden
language: "de"                   # ISO 639-1
language_level: "simple"         # professional | simplified | layperson | simple

# Klassifikation
icd10: []                        # z. B. ["I50.0", "I50.1"]
ops: []                          # OPS-Prozedurencodes

# Quellen (nur Verweise und eigene Zusammenfassungen — keine Volltextübernahme geschützter Quellen)
pubmed_ids: []                   # nur Ziffern, z. B. [12345678]
guidelines: []                   # Leitlinien
  # - title: ""
  #   issuer: ""
  #   awmf_register: ""          # z. B. "019-013"
  #   year: 2024
  #   url: ""
references: []                   # (Pflicht) strukturierte Literatur; ab "approved" mind. 1 Quelle in references/pubmed_ids/guidelines
  # - citation: ""
  #   pmid: ""
  #   doi: ""
  #   url: ""
source_notes: ""                 # Pflicht ab "approved": Wie entstand der Text? Eigene Zusammenfassung; ggf. eingeholte Genehmigungen

# KI-Deklaration (docs/editorial/ai-assistance-policy.md)
ai_assisted: false               # (Pflicht) explizit deklarieren
ai_assistance_description: ""    # Pflicht bei ai_assisted: true — Tool, Aufgabe und menschliche Verifikation

# Recht
wikimedica_credit: true          # Pflichtfeld, immer true
license: ""                      # Pflicht ab "approved". Bewusst ohne Vorgabe: Lizenzmodell ist offene Eigentümerentscheidung (docs/legal/license-decision-needed.md)

corrections: []                  # Korrekturen nach Veröffentlichung
  # - date: YYYY-MM-DD
  #   description: ""
  #   version_after: ""
---

# {{ title }}

<!-- Patiententexte sind ALLGEMEINE Information, keine individuelle ärztliche Anweisung:
     keine Dosierungen, keine Formulierungen wie "Nehmen Sie ..." oder "Setzen Sie ... ab".
     Niveau B1–B2, kurze Sätze. Verständlichkeitsprüfung: forms/reviewer-checklists/patient-comprehensibility-checklist.md -->

> Dieser Artikel ist für Patienten und Angehörige geschrieben. Er verwendet einfache Sprache und soll Ihnen helfen, Ihre Erkrankung besser zu verstehen.

---

## Was ist das?

<!-- Was ist diese Erkrankung / dieser Zustand?
     Erklärung in 3–5 einfachen Sätzen.
     Medizinische Fachbegriffe in Klammern erklären.
     Beispiel: "Die Herzinsuffizienz (Herzschwäche) bedeutet, dass das Herz
     nicht mehr so gut pumpen kann wie ein gesundes Herz."
-->

---

## Wie entsteht es?

<!-- Ursachen und Risikofaktoren in verständlicher Sprache.
     Was kann die Erkrankung auslösen?
     Was macht manche Menschen anfälliger dafür?
     Beispiel: "Herzinsuffizienz kann durch verschiedene Ursachen entstehen:
     - Ein früherer Herzinfarkt
     - Dauerhaft hoher Blutdruck
     - ..."
-->

---

## Wie häufig ist es?

<!-- Kurze, verständliche Angabe zur Häufigkeit.
     Beispiel: "In Deutschland leben etwa 1,8 Millionen Menschen mit Herzinsuffizienz."
     Optional, wenn epidemiologische Daten für Patienten relevant sind.
-->

---

## Wie wird es festgestellt?

<!-- Diagnoseweg in Patientensprache:
     - Welche Fragen stellt der Arzt?
     - Welche Untersuchungen werden gemacht?
     - Was sucht der Arzt dabei?
     Kein technischer Jargon ohne Erklärung.
     Beispiel: "Der Arzt wird zuerst fragen, ob Sie kurzatmig oder erschöpft sind.
     Dann hört er Ihr Herz und Ihre Lunge ab..."
-->

---

## Wie wird es behandelt?

<!-- Behandlungsmöglichkeiten in einfacher Sprache:
     - Medikamente (Wirkung und Nutzen — keine genauen Dosierungen, da nicht individualisierbar)
     - Lebensstiländerungen
     - Operationen / Eingriffe (falls relevant)
     - Was kann ich selbst tun?
     Beispiel: "Die Behandlung zielt darauf ab, das Herz zu entlasten und
     Ihre Symptome zu verbessern. Ihr Arzt wird Ihnen Medikamente verschreiben,
     die dem Herzen helfen, besser zu arbeiten..."
-->

### Medikamente

### Lebensstiländerungen

### Eingriffe und Operationen

---

## Was muss ich beachten?

<!-- Praktische Hinweise für den Alltag:
     - Warnsymptome (wann sofort zum Arzt)
     - Verhaltenstipps
     - Was sollte ich meinem Arzt mitteilen?
     Beispiel: "Rufen Sie sofort den Notarzt (112), wenn Sie..."
-->

### Wann sofort zum Arzt?

<!-- Klare rote Fahnen:
     - Starke Schmerzen
     - Plötzliche Luftnot
     - Usw.
-->

### Hinweise für den Alltag

---

## Weiterführende Informationen

<!-- Links zu seriösen Patientenselbsthilfeorganisationen, AWMF-Patientenleitlinien, etc.
     Nur verifizierte, qualitätsgesicherte Quellen.
     Kein Verweis auf nicht-verifizierte Websites oder Gesundheitsforen.
-->

- [Patientenleitlinie der AWMF](https://www.awmf.org/patientenleitlinien)
- [Gesundheitsinformation.de (IQWiG)](https://www.gesundheitsinformation.de)
- [Deutsche Herzstiftung](https://www.herzstiftung.de) *(Beispiel — nur wenn fachlich passend)*

---

## Quellen und Grundlagen

<!-- Verständliche Angabe der Grundlagen, z. B. "Dieser Text beruht auf der Patientenleitlinie ...".
     Die vollständigen Quellen stehen in den Metadaten (references, pubmed_ids, guidelines). -->

---

## Hinweise und Haftungsausschluss

<!-- Wird bei der Veröffentlichung automatisch aus data/legal/disclaimers.yaml ergänzt
     (Profil nach article_type und risk_level, inkl. Notfallhinweis).
     Hier nur artikelspezifische Zusatzhinweise eintragen; der Abschnitt darf leer bleiben. -->

---

## Review-Historie

| Datum | Version | Rolle | Name | Ergebnis / Anmerkung |
|---|---|---|---|---|
|  |  | Fachreview |  |  |
|  |  | Redaktion |  |  |
|  |  | Medical Advisor (Hochrisiko) |  |  |
|  |  | Gender-Check |  |  |
|  |  | Verständlichkeitsprüfung |  |  |

---

## Änderungsverlauf

| Version | Datum | Autor/in | Änderung |
|---|---|---|---|
| 0.1.0 |  |  | Erstentwurf |

---

*{{ title }} · Version {{ version }} · Aktualisiert {{ updated }} · Wikimedica / AT Medical Digital Solutions · [wikimedica.de](https://wikimedica.de) · Lizenz: {{ license }}*
