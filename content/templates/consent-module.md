---
# =============================================================================
# Wikimedica — Aufklärungsmodul-Vorlage (Consent Module Template)
# =============================================================================
# Modularer Aufklärungsbogen, klinik-brandbar. Ersetzt nicht das ärztliche Aufklärungsgespräch.
# Platzhalter {{ ... }} im Text werden beim Import aus den Metadaten ersetzt
# (siehe content/templates/README.md). Alle HTML-Kommentare vor der Freigabe entfernen.
# =============================================================================

title: ""                        # (Pflicht) Vollständiger Titel auf Deutsch
slug: ""                         # (Pflicht) = Dateiname ohne .md; Kleinbuchstaben + Bindestriche; nach Veröffentlichung nie ändern
specialty: ""                    # (Pflicht) Exakter kanonischer Fachgebietsname (siehe content/specialties/README.md)
secondary_specialties: []        # Optional: weitere Fachgebiete (kanonische Namen)
article_type: "consent"          # (Pflicht) Festgelegt
content_kind: "article"          # article | guideline-summary | qr-media-reference
status: "draft"                  # draft | in-review | advisor-review | approved | published | archived (siehe docs/editorial/content-lifecycle.md)

# Versionierung
version: "0.1.0"                 # SemVer; veröffentlichte Artikel >= 1.0.0
change_summary: ""               # Ab "in-review" Pflicht: 1–2 Sätze, was diese Version ändert

# Modul
module_type: "consent"           # (Pflicht) Festgelegt: consent
procedure: ""                    # (Pflicht) Name des Eingriffs / der Maßnahme

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
target_audience: [patients, clinical-teams]  # (Pflicht) physicians | nursing | emergency-services | pharmacists | medical-professionals | patients | relatives | clinical-teams
sex_gender_relevance: "not_assessed"  # (Pflicht) not_assessed | none | relevant — vor "approved" abschließen
sex_gender_notes: ""             # Pflicht bei "relevant": geschlechtsspezifische Aspekte kurz zusammenfassen
safety_hold: false               # true = Sicherheitsprüfung läuft; Artikel kann dann nicht freigegeben werden
language: "de"                   # ISO 639-1
language_level: "simple"         # professional | simplified | layperson | simple

# Klinik-Branding (wird durch die Klinik befüllt — NICHT durch Wikimedica)
clinic_brandable: true
clinic_name: ""
clinic_address: ""
clinic_logo_url: ""              # nur HTTPS
qr_media_url: ""                 # Optional: HTTPS-URL zu Erklärvideo / Animation (siehe qr-media-reference)

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

<!-- =========================================================================
     KLINIK-BRIEFKOPF (durch Klinik auszufüllen)
     ========================================================================= -->

| | |
|---|---|
| **Klinik:** | {{ clinic_name }} |
| **Adresse:** | {{ clinic_address }} |
| **Datum:** | _____________ |
| **Patient/in:** | _____________ |
| **Geburtsdatum:** | _____________ |
| **Aufklärender Arzt:** | _____________ |

---

# Aufklärungsbogen: {{ procedure }}

*Dieser Aufklärungsbogen informiert Sie über den geplanten Eingriff, mögliche Risiken und Alternativen. Bitte lesen Sie ihn sorgfältig durch. Sprechen Sie Fragen offen mit Ihrem Arzt an.*

---

## Einleitung

<!-- Kurze, patientenfreundliche Einführung (3–5 Sätze).
     Wer führt den Eingriff durch? Wann? In welchem Kontext?
     Warum ist dieses Gespräch wichtig?
-->

---

## Was wird durchgeführt?

<!-- Beschreibung des Eingriffs in einfacher Sprache:
     - Vorbereitung (Nüchternheit, Medikamentenpause, etc.)
     - Ablauf des Eingriffs (Schritt für Schritt, kurz und klar)
     - Dauer
     - Anästhesieverfahren (Lokal-/Regionalanästhesie/Narkose)
     Optional: QR-Code zum Erklärungsvideo
-->

---

## Warum ist der Eingriff notwendig?

<!-- Medizinische Begründung in Patientensprache:
     - Diagnose / Indikation
     - Was passiert, wenn nicht behandelt wird?
     - Nutzen des Eingriffs
-->

---

## Mögliche Risiken und Komplikationen

*Alle medizinischen Eingriffe können Risiken mit sich bringen. Ihr Arzt wird diese mit Ihnen besprechen und kann erklären, wie groß das Risiko in Ihrem individuellen Fall ist.*

### Allgemeine Risiken (bei fast allen Eingriffen möglich)

- [ ] Blutung / Nachblutung
- [ ] Infektion / Wundinfektion
- [ ] Thrombose (Blutgerinnsel) / Lungenembolie
- [ ] Allergische Reaktion (auf Medikamente, Narkosemittel, Materialien)
- [ ] Verletzung umliegender Strukturen (Blutgefäße, Nerven, Organe)
- [ ] Narbenentstehung / Wundheilungsstörung

### Eingriffsspezifische Risiken

<!-- Hier die spezifischen Risiken des Eingriffs auflisten.
     Format: - [ ] Beschreibung (Häufigkeitsangabe, falls belegt)
     Beispiel: - [ ] Stimmveränderung (ca. 1 von 200 Patienten)
-->

- [ ] <!-- Risiko 1 -->
- [ ] <!-- Risiko 2 -->
- [ ] <!-- Risiko 3 -->

### Sehr seltene, schwerwiegende Risiken

<!-- Risiken, die selten auftreten, aber schwerwiegende Folgen haben können. -->

- [ ] <!-- Seltenes schwerwiegendes Risiko -->

---

## Alternativen

<!-- Welche Behandlungsalternativen gibt es?
     - Konservative Therapie
     - Andere operative Verfahren
     - Abwarten / Beobachten
     Was sind Vor- und Nachteile der Alternativen?
-->

---

## Verhalten nach dem Eingriff

<!-- Kurze Hinweise für die unmittelbare Nachsorge.
     Details im Entlassbrief / Discharge Module.
-->

---

## Ihre Fragen

*Haben Sie noch Fragen? Ihr Arzt steht Ihnen gerne zur Verfügung.*

Meine Fragen / Notizen:

_______________________________________________________________________________

_______________________________________________________________________________

---

## Einwilligung

Ich erkläre, dass mir der Inhalt dieses Aufklärungsbogens erläutert wurde. Ich hatte Gelegenheit, Fragen zu stellen, und habe ausreichend Zeit zum Nachdenken erhalten. Ich willige in die Durchführung des oben beschriebenen Eingriffs ein.

| | |
|---|---|
| **Ort, Datum:** | _________________________ |
| **Unterschrift Patient/in:** | _________________________ |
| **Unterschrift aufklärender Arzt:** | _________________________ |
| **Unterschrift gesetzl. Vertreter (falls zutreffend):** | _________________________ |

---

## Quellen und Grundlagen

<!-- Fachliche Grundlagen des Aufklärungsmoduls (Leitlinien, Fachgesellschaften, Risikostatistiken) in
     verständlicher Form nennen. Vollständige Quellen stehen in den Metadaten.
     Wichtig: Das Modul ersetzt NICHT das individuelle Aufklärungsgespräch. -->

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
|  |  | Rechtsprüfung (Legal Reviewer) |  |  |
|  |  | Verständlichkeitsprüfung |  |  |

---

## Änderungsverlauf

| Version | Datum | Autor/in | Änderung |
|---|---|---|---|
| 0.1.0 |  |  | Erstentwurf |

---

*{{ title }} · Version {{ version }} · Aktualisiert {{ updated }} · Wikimedica / AT Medical Digital Solutions · [wikimedica.de](https://wikimedica.de) · Lizenz: {{ license }}*
