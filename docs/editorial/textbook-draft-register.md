# Register der Artikelentwürfe aus Lehrbuchquellen

**Stand:** 2026-10-09 · **Status:** alle Artikel `status: draft` · **Verantwortlich:** Redaktion (Review noch nicht begonnen)

Dieses Register listet die 31 Entwürfe, die aus den im Quelleninventar (`data/sources/textbook-inventory.yaml`, Feld `used_in`)
geführten Lehrbüchern erstellt wurden. Die Texte sind in eigenen Worten verfasst, deutschsprachig, ohne Dosierungsempfehlungen
und mit KI-Unterstützung entstanden (`ai_assisted: true`). **Kein Artikel ist fachlich geprüft.** Jeder Entwurf nennt als einzige
Quelle das gelesene Lehrbuchkapitel und vermerkt in `source_notes`, welche Teile gelesen wurden.

## Vorgehen bis zur Veröffentlichung

1. Fachreview durch eine qualifizierte Person der jeweiligen Fachrichtung (nicht die Redaktion), Eintrag in `reviewers`.
2. Risikostufe `high` (Chemotherapie im Alter, Symptommanagement und Serotoninsyndrom in der Palliativmedizin): zusätzlich Medical Advisor.
3. Quellen aktualisieren: Die Pharmakologie-Kapitel und der Palliativband stammen von 2012, die Statistik von 2013; Regulierungsteile beziehen sich auf die USA.
4. Geschlechts- und Genderaspekte prüfen; bei `not_assessed` ist die Bewertung offen.
5. Lizenz (`license`) wird erst nach der Eigentümerentscheidung DEC-2 gesetzt.
6. Für die Freigabe verlangt `scripts/publishing/pre-publish-check.py` je Artikeltyp Pflichtabschnitte (z. B. Epidemiologie, Diagnostik,
   Therapie). Die Entwürfe folgen ihrem Thema; sie müssen dafür umgegliedert oder der Check muss für Querschnittsthemen angepasst werden.

## Urheberrecht

Die Lehrbücher sind urheberrechtlich geschützt. Die Entwürfe geben Inhalte sinngemäß wieder, enthalten keine wörtlichen Passagen und keine
Abbildungen der Originale; Tabellen sind eigene Zusammenstellungen. Siehe `docs/legal/copyright-and-sourcing-policy.md`. Ob die
Veröffentlichung solcher Zusammenfassungen zulässig ist, ist Teil des Legal-Reviews vor der Freigabe.

## Entwürfe

| Artikel | Fachgebiet | Risiko | Geschlecht/Gender |
|---|---|---|---|
| [Osteoporose im Alter: medikamentöse Therapie](../../content/specialties/endokrinologie-diabetologie/osteoporose-pharmakotherapie-alter.md) | Endokrinologie/Diabetologie | moderate | relevant |
| [Leberinsuffizienz und Pharmakokinetik](../../content/specialties/gastroenterologie/leberinsuffizienz-pharmakokinetik.md) | Gastroenterologie | moderate | not_assessed |
| [Frauen in klinischen Studien](../../content/specialties/gender-medizin/frauen-in-klinischen-studien.md) | Gender-Medizin | moderate | relevant |
| [Geschlechtsunterschiede bei Schmerz und Analgetika](../../content/specialties/gender-medizin/geschlechtsunterschiede-analgetika.md) | Gender-Medizin | moderate | relevant |
| [Geschlechtsunterschiede in der Pharmakologie](../../content/specialties/gender-medizin/geschlechtsunterschiede-pharmakologie.md) | Gender-Medizin | moderate | relevant |
| [Chemotherapie im höheren Lebensalter](../../content/specialties/haematologie-onkologie/chemotherapie-im-alter.md) | Hämatologie/Onkologie | high | not_assessed |
| [Polypharmazie im Alter](../../content/specialties/innere-medizin/polypharmazie-im-alter.md) | Innere Medizin | moderate | not_assessed |
| [Arzneimittelinduzierte QT-Verlängerung und Torsade de pointes](../../content/specialties/kardiologie/arzneimittelinduzierte-qt-verlaengerung.md) | Kardiologie | moderate | relevant |
| [Gütekriterien diagnostischer Tests](../../content/specialties/labormedizin/guetekriterien-diagnostischer-tests.md) | Labormedizin | low | not_assessed |
| [ROC-Analyse und Schwellenwerte](../../content/specialties/labormedizin/roc-analyse-schwellenwert.md) | Labormedizin | low | not_assessed |
| [Nierenfunktion im Alter und Arzneimittel](../../content/specialties/nephrologie/nierenfunktion-alter-arzneimittel.md) | Nephrologie | moderate | not_assessed |
| [Niereninsuffizienz und Pharmakokinetik](../../content/specialties/nephrologie/niereninsuffizienz-pharmakokinetik.md) | Nephrologie | moderate | not_assessed |
| [Geschichte der Palliativmedizin](../../content/specialties/palliativmedizin/geschichte-der-palliativmedizin.md) | Palliativmedizin | low | not_assessed |
| [Serotoninsyndrom in der Palliativmedizin](../../content/specialties/palliativmedizin/serotoninsyndrom-palliativmedizin.md) | Palliativmedizin | high | not_assessed |
| [Grundlagen des Symptommanagements in der Palliativmedizin](../../content/specialties/palliativmedizin/symptommanagement-palliativmedizin.md) | Palliativmedizin | high | not_assessed |
| [Pharmakokinetische Arzneimittelinteraktionen](../../content/specialties/pharmakologie/arzneimittelinteraktionen-pharmakokinetik.md) | Pharmakologie | moderate | not_assessed |
| [Arzneimittelsicherheit und Risikominimierung](../../content/specialties/pharmakologie/arzneimittelsicherheit-risikominimierung.md) | Pharmakologie | moderate | not_assessed |
| [Arzneimitteltherapie im Alter](../../content/specialties/pharmakologie/arzneimitteltherapie-im-alter.md) | Pharmakologie | moderate | relevant |
| [Arzneimitteltherapie in der Schwangerschaft](../../content/specialties/pharmakologie/arzneimitteltherapie-schwangerschaft.md) | Pharmakologie | moderate | relevant |
| [Arzneimitteltherapie in der Stillzeit](../../content/specialties/pharmakologie/arzneimitteltherapie-stillzeit.md) | Pharmakologie | moderate | relevant |
| [CYP2D6-Polymorphismus](../../content/specialties/pharmakologie/cyp2d6-polymorphismus.md) | Pharmakologie | moderate | not_assessed |
| [Hepatische Clearance und Extraktionsrate](../../content/specialties/pharmakologie/hepatische-clearance-extraktionsrate.md) | Pharmakologie | moderate | not_assessed |
| [Kausalitätsbewertung bei Arzneimittelnebenwirkungen](../../content/specialties/pharmakologie/kausalitaetsbewertung-arzneimittelnebenwirkungen.md) | Pharmakologie | moderate | not_assessed |
| [Ontogenese arzneimittelmetabolisierender Enzyme](../../content/specialties/pharmakologie/ontogenese-arzneistoffmetabolismus.md) | Pharmakologie | moderate | not_assessed |
| [Pharmakogenetik](../../content/specialties/pharmakologie/pharmakogenetik.md) | Pharmakologie | moderate | not_assessed |
| [Plazentatransfer von Arzneistoffen](../../content/specialties/pharmakologie/plazentatransfer-arzneistoffe.md) | Pharmakologie | moderate | relevant |
| [Teratogenese und teratogene Arzneistoffe](../../content/specialties/pharmakologie/teratogenese-arzneistoffe.md) | Pharmakologie | moderate | relevant |
| [Unerwünschte Arzneimittelwirkungen](../../content/specialties/pharmakologie/unerwuenschte-arzneimittelwirkungen.md) | Pharmakologie | moderate | not_assessed |
| [Arzneiformen und Adhärenz bei Kindern](../../content/specialties/paediatrie/kinder-arzneiformen-adhaerenz.md) | Pädiatrie | moderate | not_assessed |
| [Pharmakodynamik und Arzneimittelentwicklung bei Kindern](../../content/specialties/paediatrie/kinder-pharmakodynamik-arzneimittelentwicklung.md) | Pädiatrie | moderate | not_assessed |
| [Pharmakokinetik im Kindesalter](../../content/specialties/paediatrie/pharmakokinetik-im-kindesalter.md) | Pädiatrie | moderate | not_assessed |
