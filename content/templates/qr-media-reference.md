---
# =============================================================================
# Wikimedica — QR-Medien-Referenz (QR Media Reference Template)
# =============================================================================
# Datensatz für QR-verknüpfte Medien (Video, Audio, Animation, FAQ) einer Patienten-/Aufklärungs-/Entlassstrecke.
# Platzhalter {{ ... }} im Text werden beim Import aus den Metadaten ersetzt
# (siehe content/templates/README.md). Alle HTML-Kommentare vor der Freigabe entfernen.
# =============================================================================

title: ""                        # (Pflicht) Vollständiger Titel auf Deutsch
slug: ""                         # (Pflicht) = Dateiname ohne .md; Kleinbuchstaben + Bindestriche; nach Veröffentlichung nie ändern
specialty: ""                    # (Pflicht) Exakter kanonischer Fachgebietsname (siehe content/specialties/README.md)
secondary_specialties: []        # Optional: weitere Fachgebiete (kanonische Namen)
article_type: "patient"          # (Pflicht) Festgelegt
content_kind: "qr-media-reference"  # article | guideline-summary | qr-media-reference
status: "draft"                  # draft | in-review | advisor-review | approved | published | archived (siehe docs/editorial/content-lifecycle.md)

# Versionierung
version: "0.1.0"                 # SemVer; veröffentlichte Artikel >= 1.0.0
change_summary: ""               # Ab "in-review" Pflicht: 1–2 Sätze, was diese Version ändert

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

# Medium
media_type: ""                   # (Pflicht) video | audio | animation | faq | document
parent_slug: ""                  # (Pflicht) slug des zugehörigen Artikels/Moduls
qr_media_url: ""                 # (Pflicht) Ziel-URL — nur HTTPS
media_transcript: false          # Pflicht true ab "approved" bei audio/video/animation (Barrierefreiheit)

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

> **Zugehörig zu:** {{ parent_slug }}
> **Status:** {{ status }} · **Version:** {{ version }} · **Zuletzt aktualisiert:** {{ updated }}

---

## Medium

| Eigenschaft | Angabe |
|---|---|
| Titel |  |
| Art (Video / Audio / Animation / FAQ / Dokument) |  |
| Dauer / Umfang |  |
| Sprache |  |
| Anbieter / Hosting |  |
| Ziel-URL (HTTPS) | {{ qr_media_url }} |

---

## Zweck und Zielgruppe

---

## Inhaltliche Zusammenfassung

<!-- Kurze Beschreibung des Inhalts in einfacher Sprache (B1–B2). -->

---

## Transkript

<!-- Vollständiges Transkript bzw. Untertitel-Text. Pflicht bei Audio/Video/Animation. -->

---

## Zugriff und QR-Code

<!-- Ziel-URL ausschließlich über HTTPS. Keine Tracking-Parameter. Gültigkeit und Zuständigkeit für den Link nennen. -->

---

## Barrierefreiheit

<!-- Untertitel, Audiodeskription, einfache Sprache, Kontrast, Alternativtext. -->

---

## Datenschutz und Hosting

<!-- Kein Einbetten von Drittanbieter-Playern ohne Einwilligung — nur verlinken.
     Hosting-Standort und Auftragsverarbeitung klären (siehe docs/legal/privacy-notes.md). -->

---

## Pflege

<!-- Wer prüft den Link und die Aktualität wie oft? Das Medium unterliegt demselben Review-Zyklus. -->

---

## Literatur

1. <!-- Quelle der medizinischen Aussagen des Mediums -->

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
|  |  | Barrierefreiheitsprüfung |  |  |

---

## Änderungsverlauf

| Version | Datum | Autor/in | Änderung |
|---|---|---|---|
| 0.1.0 |  |  | Erstentwurf |

---

*{{ title }} · Version {{ version }} · Aktualisiert {{ updated }} · Wikimedica / AT Medical Digital Solutions · [wikimedica.de](https://wikimedica.de) · Lizenz: {{ license }}*
