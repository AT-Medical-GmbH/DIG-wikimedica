# Specialty Content — Wikimedica

This directory contains all medical articles organised by specialty. Each specialty has its own subdirectory with a `README.md` describing the editorial priorities, scope, and planned content for that area.

---

## Specialty Directory Structure

```text
content/specialties/
├── README.md                          ← this file
├── innere-medizin/
├── kardiologie/
├── pneumologie/
├── gastroenterologie/
├── nephrologie/
├── endokrinologie-diabetologie/
├── haematologie-onkologie/
├── infektiologie/
├── rheumatologie/
├── neurologie/
├── psychiatrie/
├── dermatologie/
├── paediatrie/
├── gynaekologie-geburtshilfe/
├── urologie/
├── orthopaedie-unfallchirurgie/
├── anaesthesiologie/
├── intensivmedizin/
├── notfallmedizin/
├── chirurgie/
├── radiologie/
├── labormedizin/
├── pharmakologie/
├── palliativmedizin/
├── praevention-public-health/
└── gender-medizin/                    ← flagship focus area
```

---

## Specialty Index

| # | Specialty | Directory | Status |
|---|---|---|---|
| 1 | Innere Medizin | `innere-medizin/` | Planned |
| 2 | Kardiologie | `kardiologie/` | Planned |
| 3 | Pneumologie | `pneumologie/` | Planned |
| 4 | Gastroenterologie | `gastroenterologie/` | Planned |
| 5 | Nephrologie | `nephrologie/` | Planned |
| 6 | Endokrinologie/Diabetologie | `endokrinologie-diabetologie/` | Planned |
| 7 | Hämatologie/Onkologie | `haematologie-onkologie/` | Planned |
| 8 | Infektiologie | `infektiologie/` | Planned |
| 9 | Rheumatologie | `rheumatologie/` | Planned |
| 10 | Neurologie | `neurologie/` | Planned |
| 11 | Psychiatrie | `psychiatrie/` | Planned |
| 12 | Dermatologie | `dermatologie/` | Planned |
| 13 | Pädiatrie | `paediatrie/` | Planned |
| 14 | Gynäkologie/Geburtshilfe | `gynaekologie-geburtshilfe/` | Planned |
| 15 | Urologie | `urologie/` | Planned |
| 16 | Orthopädie/Unfallchirurgie | `orthopaedie-unfallchirurgie/` | Planned |
| 17 | Anästhesiologie | `anaesthesiologie/` | Planned |
| 18 | Intensivmedizin | `intensivmedizin/` | Planned |
| 19 | Notfallmedizin | `notfallmedizin/` | Planned |
| 20 | Chirurgie | `chirurgie/` | Planned |
| 21 | Radiologie | `radiologie/` | Planned |
| 22 | Labormedizin | `labormedizin/` | Planned |
| 23 | Pharmakologie | `pharmakologie/` | Planned |
| 24 | Palliativmedizin | `palliativmedizin/` | Planned |
| 25 | Prävention/Public Health | `praevention-public-health/` | Planned |
| 26 | Gender-Medizin | `gender-medizin/` | **Active — Flagship** |

---

## Article Linking Convention

### Frontmatter Specialty Field

Every article in this directory tree must include the `specialty` field in its YAML frontmatter, using the **exact canonical name** from the list below:

```yaml
specialty: "Kardiologie"
```

Canonical specialty names (use exactly as listed):

- `Innere Medizin`
- `Kardiologie`
- `Pneumologie`
- `Gastroenterologie`
- `Nephrologie`
- `Endokrinologie/Diabetologie`
- `Hämatologie/Onkologie`
- `Infektiologie`
- `Rheumatologie`
- `Neurologie`
- `Psychiatrie`
- `Dermatologie`
- `Pädiatrie`
- `Gynäkologie/Geburtshilfe`
- `Urologie`
- `Orthopädie/Unfallchirurgie`
- `Anästhesiologie`
- `Intensivmedizin`
- `Notfallmedizin`
- `Chirurgie`
- `Radiologie`
- `Labormedizin`
- `Pharmakologie`
- `Palliativmedizin`
- `Prävention/Public Health`
- `Gender-Medizin`

### Cross-Specialty Articles

Articles that span multiple specialties should list the **primary** specialty in the `specialty` field and additional specialties in the `secondary_specialties` list:

```yaml
specialty: "Kardiologie"
secondary_specialties:
  - "Intensivmedizin"
  - "Notfallmedizin"
```

### MediaWiki Category Convention

When articles are imported to MediaWiki, the `specialty` frontmatter value maps to a MediaWiki category: `[[Kategorie:Kardiologie]]`. The import script handles this automatically.

---

## File Naming Convention

Article files are named using lowercase, hyphenated ASCII transliterations of the German title:

```text
content/specialties/kardiologie/herzinsuffizienz-chron.md
content/specialties/gender-medizin/herzinfarkt-bei-frauen.md
```

- No spaces (use hyphens)
- No umlauts in filenames (ä → ae, ö → oe, ü → ue, ß → ss)
- No special characters
- Descriptive but concise (max 60 characters)
- Use the article template as the starting point (`content/templates/`)
