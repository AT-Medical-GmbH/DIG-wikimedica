# Automatische Querverweise und Rückverweise (ENTWURF, Auftrag Andreas 10.11.2026, Projekt 15, #712)

**Regel (fest in der Pipeline):** Beim Bauen jeder Wiki-Seite (`import_merged_beta.build_page`) werden Fachbegriffe, für die es einen Artikel oder eine Weiterleitung gibt, im Fließtext beim ersten Vorkommen verlinkt. Zuständiger Code: `scripts/publishing/autolink.py`.

- Keine Selbstlinks (auch nicht über Weiterleitungen auf den eigenen Artikel); pro Ziel ein Link (ein schon vorhandener Link zählt als erstes Vorkommen); höchstens 40 Links je Artikel.
- Nie verlinkt: Überschriften, Tabellenköpfe, Zitate (`<blockquote>`), Vorlagen, Fußnoten, Code/Math/nowiki/pre, Kommentare, Warnkasten, vorhandene Links, Web-Adressen, Abschnitte „Siehe auch“, „Einzelnachweise“, „Weblinks“, „Literatur“, „Für Patientinnen und Patienten“, BETA-Hinweis.
- Weiterleitungen werden aufgelöst (`[[Ziel|Anzeigetext]]`); längste Übereinstimmung zuerst; erster Buchstabe darf abweichen, Rest exakt; Wortgrenzen und Bindestriche werden beachtet; mehrdeutige oder zu kurze Formen (unter 4 Zeichen, Kürzel ab 3 Großbuchstaben) nie.
- Ziele: Artikel des Quellbestands plus `data/editorial/link-aliases.json` (Wiki-Titel und Weiterleitungen). Auffrischen (nur lesend): `python3 scripts/publishing/autolink.py --refresh-aliases`.
- Notbremse: Umgebungsvariable `WIKIMEDICA_AUTOLINK=0` schaltet die Regel ab.

**Rückverweise:** „Siehe auch“ (`related_articles`) enthält zusätzlich bis zu 4 Artikel, die diesen Artikel in ihrem „Siehe auch“ nennen (`reverse_related`).

**Wirkung auf bestehende Seiten:** erst beim nächsten Import der jeweiligen Datei (Hashabgleich über Marker). Ein Neuaufbau aller Artikel ist ein eigener, freizugebender Schritt (Produktion, Stufe 2).

**Probelauf:** `scripts/publishing/autolink_staging_probe.py` (nur Staging-Container, sichert Vorher-Stand, `--rollback` stellt ihn wieder her).

Grenzen: nur exakte Oberflächenformen (keine Beugung wie „Herzinsuffizienzen“ oder „chronischer Herzinsuffizienz“); Begriffe in Mehrdeutigkeit werden ausgelassen; Wirkung auf Lesbarkeit durch Obergrenze und Erst-Vorkommen begrenzt.
