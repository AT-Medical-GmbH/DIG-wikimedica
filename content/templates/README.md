# Content-Templates — Wikimedica

**Document version:** 1.0
**Owner:** AT Medical Digital Solutions — Editorial Board
**Last updated:** 2026-10-09

Diese Vorlagen sind der **einzige zulässige Ausgangspunkt** für neue Inhalte. Sie sind
durch `tests/test_templates.py` gegen das Schema (`data/metadata/article-schema.yaml`) und
die Pflichtabschnitte des Pre-Publish-Checks abgesichert.

---

## 1. Verfügbare Vorlagen

| Vorlage | `article_type` | `content_kind` | Standard-Risiko | Zielordner |
|---|---|---|---|---|
| `article-professional.md` | professional | article | wählbar | `content/specialties/<fachgebiet>/` |
| `guideline-summary.md` | professional | guideline-summary | wählbar | `content/specialties/<fachgebiet>/` |
| `article-patient.md` | patient | article | wählbar | `content/patient-info/` |
| `consent-module.md` | consent | article | wählbar | `content/consent-modules/` |
| `discharge-module.md` | discharge | article | wählbar | `content/discharge-modules/` |
| `article-pharmaka.md` | pharmaka | article | **high** (Pflicht) | `content/pharmaka/` |
| `article-therapy.md` | therapy | article | **high** (Pflicht) | `content/therapies/` |
| `qr-media-reference.md` | patient | qr-media-reference | wählbar | `content/patient-info/` (neben dem Elternartikel) |

Der Dateiname ohne `.md` **ist** der `slug` (z. B. `herzinsuffizienz-chronisch.md` → `slug: herzinsuffizienz-chronisch`).
Der Slug ist der Idempotenz-Schlüssel des MediaWiki-Imports und darf nach der Veröffentlichung nie geändert werden.

> **Offen (Editorial Board):** Die Verzeichnisse `content/drafts/`, `content/review-queue/`,
> `content/published/` und `content/articles/` stammen aus dem Initial-Scaffold. Der Status eines
> Artikels steht im Frontmatter (`status`), **nicht** im Verzeichnis. Bis zur Entscheidung, ob diese
> Verzeichnisse entfallen oder eine Aufgabe bekommen, bitte **nicht** für Inhalte verwenden.

---

## 2. Von der Vorlage zum Artikel

1. Vorlage in den Zielordner kopieren und in `<slug>.md` umbenennen.
2. Alle mit **(Pflicht)** markierten Felder ausfüllen. Eine unausgefüllte Vorlage besteht die
   Validierung bewusst **nicht** (leerer `title`, `slug`, `specialty`, `risk_level` …).
3. `risk_level` bewusst wählen. Pharmaka, Therapieprotokolle sowie Notfall-, Intensivmedizin und
   Onkologie sind **immer `high`** — der Validator erzwingt das.
4. `ai_assisted` ehrlich deklarieren; bei `true` auch `ai_assistance_description` ausfüllen.
5. Lokal prüfen:

   ```bash
   python scripts/validation/validate-metadata.py content/specialties/kardiologie/mein-artikel.md
   ```

6. Pull Request öffnen. Statuswechsel folgen `docs/editorial/content-lifecycle.md`; ein neuer
   Artikel startet als `draft` oder `in-review`.
7. **Vor der Freigabe** alle HTML-Kommentare (`<!-- ... -->`) entfernen. Der Pre-Publish-Check
   behandelt verbliebene Kommentare als offene Platzhalter.

---

## 3. Platzhalter `{{ ... }}`

> **Sicherheitsrelevant:** In MediaWiki-Wikitext ist `{{ name }}` eine **Vorlagen-Einbindung**
> (`Template:Name`). Ein unbekannter oder vergessener Platzhalter würde im Wiki als roter Link
> bzw. als Einbindung einer fremden Vorlage erscheinen.

Erlaubt sind ausschließlich diese Platzhalter (`tests/test_templates.py` erzwingt das):

| Gruppe | Platzhalter | Behandlung beim Import |
|---|---|---|
| Metadaten | `title`, `specialty`, `status`, `version`, `updated`, `license`, `procedure`, `parent_slug` | werden aus dem Frontmatter ersetzt |
| Medien | `qr_media_url` | wird durch die HTTPS-URL ersetzt (bei leerem Wert entfällt der Block) |
| Klinik-Branding | `clinic_name`, `clinic_address`, `clinic_phone` | in der öffentlichen Wiki-Fassung als neutraler Hinweistext (z. B. „[Klinikname]"); die Klinik setzt die Werte beim Ausgabeformat (PDF/Druck) |

Der Importer (Phase 4) muss jede übrig gebliebene `{{ ... }}`-Sequenz als **Fehler** behandeln
und darf sie nie unverändert an MediaWiki übergeben.

---

## 4. Was automatisch ergänzt wird

Beim Import erzeugt Wikimedica aus den Metadaten — **nicht** im Markdown pflegen:

- Kategorien (Fachgebiet, Artikeltyp, Gender-Medizin-Querschnitt)
- Infobox/Metadaten-Box und Versionsbox (Version, Stand, nächste Prüfung, Risikoklasse)
- PMID-/Literaturverweise aus `pubmed_ids` / `references` / `guidelines`
- Haftungsausschluss und Notfallhinweis aus `data/legal/disclaimers.yaml`

Der Abschnitt **Review-Historie** im Text ist das menschenlesbare Prüfprotokoll (wer hat welche
Version geprüft, mit welchem Ergebnis); `reviewers` im Frontmatter ist der aktuelle Freigabestand.

---

## 5. Vorlagen ändern

Änderungen an Vorlagen benötigen den **Editorial Board** (CODEOWNERS). Neue Pflichtfelder gehören
zuerst ins Schema und in die Tests, dann in alle Vorlagen. Bestehende Artikel werden dadurch nicht
automatisch verändert.
