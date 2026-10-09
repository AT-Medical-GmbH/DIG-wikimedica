---
# =============================================================================
# Wikimedica — Leitlinien-Zusammenfassung (Guideline Summary Template)
# =============================================================================
# Eigene Zusammenfassung einer Leitlinie. KEINE wörtliche Übernahme; Nutzungsbedingungen des Herausgebers beachten.
# Platzhalter {{ ... }} im Text werden beim Import aus den Metadaten ersetzt
# (siehe content/templates/README.md). Alle HTML-Kommentare vor der Freigabe entfernen.
# =============================================================================

title: ""                        # (Pflicht) Vollständiger Titel auf Deutsch
slug: ""                         # (Pflicht) = Dateiname ohne .md; Kleinbuchstaben + Bindestriche; nach Veröffentlichung nie ändern
specialty: ""                    # (Pflicht) Exakter kanonischer Fachgebietsname (siehe content/specialties/README.md)
secondary_specialties: []        # Optional: weitere Fachgebiete (kanonische Namen)
article_type: "professional"     # (Pflicht) Festgelegt
content_kind: "guideline-summary"  # article | guideline-summary | qr-media-reference
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
target_audience: [physicians, medical-professionals]  # (Pflicht) physicians | nursing | emergency-services | pharmacists | medical-professionals | patients | relatives | clinical-teams
sex_gender_relevance: "not_assessed"  # (Pflicht) not_assessed | none | relevant — vor "approved" abschließen
sex_gender_notes: ""             # Pflicht bei "relevant": geschlechtsspezifische Aspekte kurz zusammenfassen
safety_hold: false               # true = Sicherheitsprüfung läuft; Artikel kann dann nicht freigegeben werden
language: "de"                   # ISO 639-1
language_level: "professional"   # professional | simplified | layperson | simple

# Klassifikation
icd10: []                        # z. B. ["I50.0", "I50.1"]
ops: []                          # OPS-Prozedurencodes

# Quellen (nur Verweise und eigene Zusammenfassungen — keine Volltextübernahme geschützter Quellen)
pubmed_ids: []                   # nur Ziffern, z. B. [12345678]
guidelines: []                   # (Pflicht) mind. 1 Eintrag: die zusammengefasste Leitlinie
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

> **Fachgebiet:** {{ specialty }}
> **Status:** {{ status }} · **Version:** {{ version }} · **Zuletzt aktualisiert:** {{ updated }}

---

## Übersicht

<!-- Leitlinie (Titel, Herausgeber, AWMF-Registernummer bzw. Fachgesellschaft), Version, Gültigkeit,
     Klassifikation (z. B. S1/S2k/S3) und Kernaussage in 3–5 Sätzen. Eigene Worte. -->

---

## Geltungsbereich und Zielgruppe

---

## Kernempfehlungen

<!-- Eigene Zusammenfassung der wichtigsten Empfehlungen — keine wörtliche Übernahme.
     Empfehlungs- und Evidenzgrade in der Systematik der Original-Leitlinie angeben. -->

| Nr. | Empfehlung (Zusammenfassung) | Empfehlungsgrad | Evidenz | Fundstelle (Kapitel / Seite) |
|---|---|---|---|---|
|  |  |  |  |  |

---

## Evidenz- und Empfehlungsgrade

<!-- Legende der in der Leitlinie verwendeten Systematik. -->

---

## Anmerkungen der Redaktion

<!-- Abweichungen, Einschränkungen oder Hinweise zur Anwendung in Deutschland. -->

---

## Sex- und Gender-Aspekte

<!-- Was sagt die Leitlinie zu geschlechtsspezifischen Unterschieden? Wo fehlen Daten? -->

---

## Aktualität und Überwachung

<!-- Stand/Gültigkeit der Leitlinie, Eintrag in data/registries/guideline-registry.yaml (id),
     geplante Überprüfung. -->

---

## Verknüpfte Wikimedica-Artikel

---

## Literatur

1. <!-- Original-Leitlinie: Herausgeber. Titel. Registernummer. Version/Jahr. URL. -->

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

---

## Änderungsverlauf

| Version | Datum | Autor/in | Änderung |
|---|---|---|---|
| 0.1.0 |  |  | Erstentwurf |

---

*{{ title }} · Version {{ version }} · Aktualisiert {{ updated }} · Wikimedica / AT Medical Digital Solutions · [wikimedica.de](https://wikimedica.de) · Lizenz: {{ license }}*
