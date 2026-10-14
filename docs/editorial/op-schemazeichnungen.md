# Schematische Zeichnungen für Operationsartikel

Stand: 14.10.2026. Auftrag Andreas Tremml: Operationsartikel erhalten grobe, eindeutig als Schema erkennbare Zeichnungen, zum Beispiel vom Zugangsweg. Beginn mit den Artikeln WM-OP-0011 bis 0080.

## Grundsätze

- Alle Zeichnungen werden selbst erzeugt (SVG, Skript `scripts/editorial/wm_op_figures.py`). Es werden keine fremden Bilder übernommen; damit entstehen keine Lizenzfragen.
- Einheitlicher Stil: gleicher Körperumriss je Vorlage, rote Markierungen für den Standardzugang, orange gestrichelt für Alternativen, graue Orientierungslinien, Beschriftung auf Deutsch, Seitenangabe („Patient rechts“, „Patient links“), Fußzeile „Schematische Darstellung, nicht maßstabsgetreu. Kein Ersatz für anatomische Atlanten oder Operationsanleitungen.“
- Lieber keine Zeichnung als eine falsche: Eine Zeichnung entsteht nur, wenn der Artikel in `data/media/op-figures/registry.json` mit `approved: true` steht. Die Einträge beschreiben nur Zugangswege und Punkte, die in der Fachliteratur als Standard gelten, und sind relativ zu Orientierungspunkten (Jugulum, Xiphoid, Nabel, Symphyse, Spina iliaca anterior superior, Gelenkspalt) gesetzt.
- Die Zeichnungen zeigen keine Operationsschritte und keine Maße.

## Vorlagen

| Vorlage | Inhalt |
| --- | --- |
| `torso` | Rumpf mit Kopf, Vorderansicht; Orientierungspunkte und -linien (Brustbein, Rippenbogen, Leistenband) |
| `neck` | Hals mit Zungenbein, Schildknorpel, Ringknorpel, Trachealspangen, Schlüsselbeinen |
| `knee` | rechtes Knie von vorn mit Patella, Patellarsehne, Tuberositas tibiae, Gelenkspalt (lateral links, medial rechts) |

Elementtypen: `line`, `curve`, `port`, `cross` (Punktionsstelle), `bracket` (Bereich entlang der Mittellinie), je mit Beschriftung.

## Aktueller Stand (19 Artikel)

Herz- und Gefäßchirurgie: Koronararterien-Bypassoperation, Aortenklappenersatz, Mitralklappenrekonstruktion, TAVI, EVAR, TEVAR. Gynäkologie: Kaiserschnitt, Hysterektomie, Myomektomie, Oophorektomie. Intensivmedizin: ECMO-Kanülierung, Tracheotomie. Orthopädie: Arthroskopie, Knietotalendoprothese. Transplantation: Herztransplantation, Lebertransplantation. Viszeralchirurgie (WM-OP-0001 bis 0010): Appendektomie, Cholezystektomie, Leistenhernienoperation.

Bewusst ohne Zeichnung, weil das Schema ohne fachliche Prüfung unsicher wäre oder eine andere Vorlage braucht (seitlicher Thorax, Extremitäten, Kopf, Auge, Mundhöhle, Geräteplatzierung): Lobektomie, Pneumonektomie, VATS, Thoraxdrainage, Pleurodese, Dialyseshuntanlage, Varizenoperation, Hüft- und Schulterendoprothese, Karpaltunnelspaltung, Kraniotomie und die übrigen Neurochirurgie-, Augen- und HNO-Artikel, Lungen- und Nierentransplantation, Prostatektomie, Nephrektomie, Zystektomie.

## Ablauf für neue Operationsartikel

1. `python3 scripts/editorial/wm_op_figures.py check` listet Operationsartikel ohne freigegebene Zeichnung.
2. `python3 scripts/editorial/wm_op_figures.py suggest` legt für passende Schlüsselwörter einen Vorschlag mit `approved: false` an; es wird nichts gezeichnet.
3. Nach fachlicher Durchsicht (Quelle für Zugangsweg und Orientierungspunkte im Eintrag nennen, Beschriftung und Elemente ausfüllen) wird `approved` auf `true` gesetzt.
4. `build` erzeugt `media/op/<slug>-schema.svg`, `insert` fügt den Abschnitt „Schematische Darstellung“ vor „Literatur“ ein. Der Test `tests/test_editorial_pipeline.py` prüft, dass Zeichnung und Abschnitt zum Register passen.

## Technik der Einbindung

- Im Artikel steht `![Titel](../../../media/op/<slug>-schema.svg)`. `md2wiki.py` macht daraus `[[File:<Name>|thumb|center|420px|…]]`; andere Bilder werden weiterhin durch ihren Alternativtext ersetzt.
- `import_merged_beta_local.py` lädt die SVG-Datei vor der Seite über `maintenance/importImages` hoch (`--overwrite --skip-dupes`, Benutzer wie bei den Artikeln).
- Die Wiki-Seite rendert SVG über `rsvg` (im Container vorhanden).

## Offen

- Weitere Vorlagen: seitlicher Thorax (Thoraxdrainage, VATS), Arm/Hand (Shunt, Karpaltunnel), Bein (Varizen), Kopf (Kraniotomie).
- Fachliche Durchsicht der 17 Einträge durch Chirurgie und Anästhesie; bis dahin steht die Zeichnung ohne Prüfvermerk als Schema.
- Originalbilder aus dem Operationssitus: siehe [Konzept geschützter Medienbereich](../architecture/geschuetzter-medienbereich.md).
