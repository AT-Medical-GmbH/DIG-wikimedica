---
# =============================================================================
# Wikimedica — Entlassmodul-Vorlage (Discharge Module Template)
# =============================================================================
# Patientenfreundliche Entlass-, Nachsorge- und Wundversorgungsinformation. Klinik-brandbar.
# Platzhalter {{ ... }} im Text werden beim Import aus den Metadaten ersetzt
# (siehe content/templates/README.md). Alle HTML-Kommentare vor der Freigabe entfernen.
# =============================================================================

title: ""                        # (Pflicht) Vollständiger Titel auf Deutsch
slug: ""                         # (Pflicht) = Dateiname ohne .md; Kleinbuchstaben + Bindestriche; nach Veröffentlichung nie ändern
specialty: ""                    # (Pflicht) Exakter kanonischer Fachgebietsname (siehe content/specialties/README.md)
secondary_specialties: []        # Optional: weitere Fachgebiete (kanonische Namen)
article_type: "discharge"        # (Pflicht) Festgelegt
content_kind: "article"          # article | guideline-summary | qr-media-reference
status: "draft"                  # draft | in-review | advisor-review | approved | published | archived (siehe docs/editorial/content-lifecycle.md)

# Versionierung
version: "0.1.0"                 # SemVer; veröffentlichte Artikel >= 1.0.0
change_summary: ""               # Ab "in-review" Pflicht: 1–2 Sätze, was diese Version ändert

# Modul
module_type: "discharge"         # (Pflicht) Festgelegt: discharge
procedure: ""                    # (Pflicht) Durchgeführter Eingriff / Diagnose

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
target_audience: [patients, relatives, clinical-teams]  # (Pflicht) physicians | nursing | emergency-services | pharmacists | medical-professionals | patients | relatives | clinical-teams
sex_gender_relevance: "not_assessed"  # (Pflicht) not_assessed | none | relevant — vor "approved" abschließen
sex_gender_notes: ""             # Pflicht bei "relevant": geschlechtsspezifische Aspekte kurz zusammenfassen
safety_hold: false               # true = Sicherheitsprüfung läuft; Artikel kann dann nicht freigegeben werden
language: "de"                   # ISO 639-1
language_level: "simple"         # professional | simplified | layperson | simple

# Klinik-Branding (wird durch die Klinik befüllt — NICHT durch Wikimedica)
clinic_brandable: true
clinic_name: ""
clinic_address: ""
clinic_phone: ""
clinic_logo_url: ""              # nur HTTPS
qr_media_url: ""                 # Optional: HTTPS-URL zu weiterführenden Medien (siehe qr-media-reference)

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
| **Telefon:** | {{ clinic_phone }} |
| **Entlassdatum:** | _____________ |
| **Patient/in:** | _____________ |
| **Geburtsdatum:** | _____________ |

---

# Entlassinformation: {{ title }}

*Wir freuen uns, dass Sie sich gut erholt haben. Bitte lesen Sie diese Informationen sorgfältig, damit Ihre Genesung zu Hause gut verläuft. Bei Fragen wenden Sie sich jederzeit an uns.*

---

## Ihre Diagnose

<!-- Ihre Erkrankung / Ihr Befund, verständlich erklärt.
     Kurz, klar, ohne Fachjargon.
-->

**Diagnose:** _______________________________________________

---

## Was wurde bei Ihnen durchgeführt?

<!-- Kurze Beschreibung des durchgeführten Eingriffs oder der Behandlung
     in Patientensprache.
     Beispiel: "Bei Ihnen wurde eine Magenspiegelung (Gastroskopie) durchgeführt.
     Dabei wurde ein kleines Polyp entfernt, der ins Labor geschickt wurde."
-->

---

## Ihre Medikamente

*Bitte nehmen Sie alle unten aufgeführten Medikamente wie angegeben ein.*

| Medikament | Dosierung | Einnahme | Dauer | Hinweis |
|---|---|---|---|---|
| <!-- z.B. Ibuprofen 400 mg --> | | <!-- z.B. 1-0-1 --> | <!-- z.B. 5 Tage --> | <!-- z.B. mit Mahlzeit --> |
| | | | | |
| | | | | |

**Bestehende Medikamente:**

- [ ] Alle bisherigen Medikamente weiter nehmen wie gewohnt.
- [ ] Folgende Medikamente vorübergehend pausieren: ________________________
- [ ] Folgende Medikamente dauerhaft absetzen: ________________________

---

## Verhaltenshinweise

<!-- Konkrete, alltagstaugliche Anweisungen:
     Was darf ich? Was sollte ich vermeiden?
     Wann kann ich wieder arbeiten? Sport treiben? Auto fahren?
     Ernährungshinweise?
-->

### In den ersten 24 Stunden

- [ ] Bitte ruhen Sie sich aus.
- [ ] Kein Autofahren (besonders nach Narkose oder Sedierung).
- [ ] Kein Alkohol.
- [ ] Kein Heben schwerer Gegenstände.

### In den nächsten Tagen / Wochen

<!-- Spezifische Hinweise je nach Eingriff -->

- [ ] <!-- Hinweis 1 -->
- [ ] <!-- Hinweis 2 -->

### Ernährung

<!-- Falls relevant — z.B. nach Magenspiegelung, Darmeingriff etc. -->

---

## Wunden und Verbände

<!-- Wundversorgungsanweisungen:
     - Wie lange Verband belassen?
     - Wie oft wechseln?
     - Darf die Wunde nass werden?
     - Wann Fäden gezogen? (Datum oder bei wem)
-->

### Wundversorgung

| Frage | Antwort |
|---|---|
| Verband belassen bis | _____________ |
| Wunde trocken halten bis | _____________ |
| Fadenentfernung | _____________ |
| Durchführung durch | _____________ |

### Wundsymptome, die Sie beachten sollten

*Kontaktieren Sie uns, wenn Sie an der Wunde folgendes bemerken:*

- [ ] Zunehmende Rötung, Schwellung oder Wärme
- [ ] Eiternde oder übel riechende Wundsekretion
- [ ] Wundöffnung / Nahtdehiszenz
- [ ] Blutung aus der Wunde, die nicht aufhört

---

## Nachsorge

<!-- Folgetermine, Kontrolluntersuchungen:
     Wann? Bei wem? Was wird kontrolliert?
-->

| Termin | Bei wem? | Zweck |
|---|---|---|
| _____________ | Hausarzt | Allgemeine Nachsorge |
| _____________ | _________________________ | _________________________ |
| _____________ | _________________________ | _________________________ |

Bitte vereinbaren Sie bei Ihrem Hausarzt einen Nachsorgetermin innerhalb von **___ Tagen**.

---

## Notfallkontakt

**Wann sollten Sie sofort den Notarzt (112) rufen oder die Notaufnahme aufsuchen?**

- [ ] Starke, plötzlich auftretende Schmerzen
- [ ] Atemnot oder Brustschmerzen
- [ ] Hohes Fieber (> 38,5 °C)
- [ ] Starke Blutung (Wunde oder innere Blutung)
- [ ] Plötzliche Bewusstlosigkeit, Verwirrtheit, Krampfanfall
- [ ] Starke Schwellung eines Beins (Thromboseverdacht)
- [ ] <!-- Eingriffsspezifisches Warnsymptom -->

**Unsere Notaufnahme:** {{ clinic_phone }}

---

## Weiterführende Informationen

<!-- Optional: QR-Code zu weiterführendem Video / Animationsmaterial -->

{{ qr_media_url }}

---

## Quellen und Grundlagen

<!-- Fachliche Grundlagen der Verhaltens- und Wundversorgungshinweise in verständlicher Form nennen.
     Das Modul ersetzt NICHT die individuellen Anweisungen des behandelnden Teams. -->

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
