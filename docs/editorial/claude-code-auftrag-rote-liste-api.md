# Auftrag an Claude Code: autorisierten RL-DataHub-Zugang anfragen

## Ziel

Bereite eine **Entwurfs-E-Mail zur Freigabe durch Andreas** an die Rote Liste Service GmbH vor. Nicht selbst versenden. Zweck ist die Klärung eines kommerziellen, vertraglich autorisierten Zugangs zum RL DataHub für AT Medical / AT Digital Systems, zunächst für EduKlinik und die redaktionell kontrollierte Wirkstoffdatenpflege von WikiMedica.

## Nachgewiesener Ausgangspunkt

Die Rote Liste bewirbt den RL DataHub als JSON-API für Softwareanbieter. Laut offizieller FAQ werden Konditionen, Vertragsunterlagen, Testdaten und technische Dokumentation auf Anfrage bereitgestellt. Daraus folgt **kein** kostenloser oder öffentlicher Produktionszugang. Keinen Scraper bauen und keine Zugangsdaten anfordern oder speichern, bevor Vertrags- und Datenschutzprüfung abgeschlossen sind.

Offizielle Links:

- https://rote-liste.com/rote-liste-l%C3%B6sungen-f%C3%BCr-softwarehersteller
- https://www.rote-liste.de/faq

## Inhalt der Entwurfs-E-Mail

1. AT Medical und AT Digital Systems knapp als Betreiber medizinischer Lern- und Wissensplattformen vorstellen.
2. Zwei getrennte Use Cases nennen: serverseitige Arzneimittelinformation in EduKlinik und redaktionell kontrollierte Wirkstoff-/Präparate-Referenzen in WikiMedica.
3. Ausdrücklich nach Datenumfang, Aktualisierungsintervallen, JSON/OpenAPI-Dokumentation, Testzugang, Authentifizierung, Rate Limits, Mandantenmodell, Lizenz-/Nutzungsrechten, Preisen und Support fragen.
4. Klären, ob und in welchem Umfang Inhalte öffentlich in WikiMedica angezeigt werden dürfen; Fachkreis- und Patienteninhalte strikt trennen.
5. Nach PZN-, Wirkstoff-, Handelsnamen-, Fach-/Gebrauchsinformation-, Lieferbarkeits- und Rückrufdaten fragen, jeweils nur soweit lizenzierbar.
6. Keine Zusage zu Abnahme, Preis, Datennutzung oder Verarbeitung personenbezogener Daten abgeben.

## Nach einer schriftlichen Antwort

Erst dann eine technische Evaluierung durchführen: Vertragsprüfung durch zuständige Stelle, Datenmodell-Mapping, minimales Staging, Secret-Manager, serverseitiger Proxy, Audit-Logging ohne sensible Inhalte, Lizenzkennzeichnung, Rollen-/Fachkreis-Gates und Lösch-/Ablaufkonzept. Produktion erst nach separater Freigabe.
