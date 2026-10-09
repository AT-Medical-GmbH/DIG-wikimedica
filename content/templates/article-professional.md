---
# =============================================================================
# Wikimedica — Fachartikel-Vorlage (Professional Article Template)
# =============================================================================
# Kopieren nach content/specialties/<fachgebiet>/<slug>.md und alle Pflichtfelder (Pflicht) ausfüllen.
# Platzhalter {{ ... }} im Text werden beim Import aus den Metadaten ersetzt
# (siehe content/templates/README.md). Alle HTML-Kommentare vor der Freigabe entfernen.
# =============================================================================

title: ""                        # (Pflicht) Vollständiger Titel auf Deutsch
slug: ""                         # (Pflicht) = Dateiname ohne .md; Kleinbuchstaben + Bindestriche; nach Veröffentlichung nie ändern
specialty: ""                    # (Pflicht) Exakter kanonischer Fachgebietsname (siehe content/specialties/README.md)
secondary_specialties: []        # Optional: weitere Fachgebiete (kanonische Namen)
article_type: "professional"     # (Pflicht) Festgelegt
content_kind: "article"          # article | guideline-summary | qr-media-reference
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

> **Fachgebiet:** {{ specialty }}
> **Status:** {{ status }} · **Version:** {{ version }} · **Zuletzt aktualisiert:** {{ updated }}

---

## Übersicht

<!-- Kurze Zusammenfassung der Erkrankung oder des Themas (3–5 Sätze).
     Enthält: Definition, klinische Relevanz, Einordnung.
     Beispiel: "Die chronische Herzinsuffizienz ist ein klinisches Syndrom..."
-->

---

## Epidemiologie

<!-- Inzidenz, Prävalenz, Geschlechterverteilung, Altersverteilung, geografische Variation.
     Quellen: Bevölkerungsstudien, Register, Bundesgesundheitssurvey, WHO-Daten.
     Geschlechtsspezifische Daten sind, wo vorhanden, anzugeben.
     Beispiel: "In Deutschland leiden ca. 1,8 Millionen Menschen an..."
-->

---

## Ätiologie und Pathophysiologie

<!-- Ursachen, Risikofaktoren, pathophysiologische Mechanismen.
     Unterabschnitte nach Ätiologietypen möglich.
     Geschlechtsunterschiede in der Pathophysiologie explizit aufführen (falls vorhanden).
     Genetische Faktoren, Umweltfaktoren, molekulare Mechanismen.
-->

---

## Klinik

<!-- Leitsymptome, klinische Zeichen, Verlaufsformen.
     Geschlechtsunterschiede in der Symptompräsentation.
     Besonderheiten im Hinblick auf Alter, Komorbiditäten.
-->

---

## Diagnostik

<!-- Diagnostischer Algorithmus:
     1. Anamnese und körperliche Untersuchung
     2. Labordiagnostik (mit Referenzwerten wo sinnvoll)
     3. Bildgebung
     4. Weitere Spezialuntersuchungen
     Leitlinienempfehlungen mit Empfehlungsgrad angeben (A/B/C, Ia/Ib etc.).
     Differenzialdiagnosen.
-->

### Anamnese

### Körperliche Untersuchung

### Labordiagnostik

### Bildgebung

### Weitere Untersuchungen

### Differenzialdiagnosen

---

## Therapie

<!-- Evidenzbasierte Therapieempfehlung:
     - Allgemeinmaßnahmen / nicht-pharmakologische Therapie
     - Pharmakotherapie (mit Dosierungsangaben und Quellen)
     - Interventionelle / operative Verfahren
     - Leitlinienkonformität angeben
     Besonderheiten bei Frauen / Männern / Älteren / Schwangeren.
-->

### Allgemeinmaßnahmen

### Pharmakotherapie

### Interventionelle Therapie

### Therapie in besonderen Situationen

---

## Verlauf und Prognose

<!-- Natürlicher Verlauf, prognostische Faktoren, Komplikationen.
     Überlebensdaten, Remissionsraten, Hospitalisierungsrisiken.
     Unterschiede nach Geschlecht, Alter, Komorbiditäten.
-->

---

## Prävention

<!-- Primärprävention (Risikofaktoren-Modifikation)
     Sekundärprävention (Früherkennung, Screening)
     Tertiärprävention (Verhinderung von Verschlechterung/Komplikationen)
     Nur wenn evidenzbasiert belegt.
-->

---

## Besondere Patientengruppen

<!-- Optional: spezifische Hinweise für Schwangere, Kinder/Jugendliche, ältere Patienten,
     Patienten mit eingeschränkter Nieren-/Leberfunktion, Immunsupprimierte.
     Nur ausfüllen wenn relevant und evidenzbasiert.
-->

---

## Literatur

<!-- Nummerierte Literaturliste.
     Format:
     [1] Nachname V. Titel. *Zeitschrift*. Jahr;Band(Heft):Seiten. PMID: XXXXXXXX.
     [2] Leitlinienorganisation. Leitlinientitel. AWMF-Reg.-Nr. XXX-XXX. Versionsjahr. URL.
-->

1. <!-- Quelle 1 -->
2. <!-- Quelle 2 -->

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
