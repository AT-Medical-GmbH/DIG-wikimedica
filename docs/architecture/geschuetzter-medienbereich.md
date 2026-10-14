# Konzept: geschützter Medienbereich für Originalbilder aus dem Operationssitus

Stand: 14.10.2026. Status: Konzept, nicht umgesetzt. Auftrag Andreas Tremml: Originalbilder aus dem Operationssitus dürfen nur registrierte, angemeldete Nutzer sehen, damit medizinische Laien sie nicht zu Gesicht bekommen.

## 1. Ist-Stand Anmeldung und Rollen (geprüft am 14.10.2026)

- Die Wiki-Seiten sind öffentlich lesbar und indexierbar (`$wgGroupPermissions['*']['read'] = true`). Es gibt keine Anmeldesperre wie auf dem Staging.
- Konten werden nicht selbst angelegt (`createaccount` aus); Administratoren legen sie an. Die E-Mail-Bestätigung ist Pflicht (`$wgEmailConfirmToEdit`).
- Es gibt lokale MediaWiki-Konten, keine zentrale Anmeldung (weder PluggableAuth noch OpenID-Erweiterung installiert; Authentik ist für die Wiki-Anmeldung nicht eingebunden). Zwei-Faktor-Anmeldung ist über die Erweiterung OATHAuth vorhanden.
- Gruppen: `*` (Leser), `user`/`autoconfirmed` (angemeldet, nur lesen), `wm-editor`, `wm-uploader`, `importbot`, `sysop`, `bureaucrat`. Artikel schreibt nur der Import (GitHub ist die Quelle).
- Dateien liegen unter `images/` des Containers und sind direkt über `/images/…` abrufbar. Das ist für die eigenen Schemazeichnungen gewünscht, für Originalbilder nicht zulässig.

Folgerung: Für geschützte Bilder reicht eine einfache Anmeldung nicht aus; es braucht eine eigene Gruppe „verifizierte Fachpersonen“ und eine Auslieferung, die nicht an der öffentlichen Dateiablage hängt.

## 2. Anforderungen

1. Kein direkter öffentlicher Link: Weder Bild noch Vorschau noch Dateibeschreibungsseite sind ohne Anmeldung abrufbar, auch nicht über Suchmaschinen, Vorschaukarten oder die Wiki-Schnittstelle.
2. Nur Angemeldete mit Recht `wm-view-protected-media` (Gruppe `wm-fachpersonal`) sehen das Bild.
3. Nicht angemeldete oder nicht berechtigte Besucher sehen an derselben Stelle einen Platzhalter mit Hinweis und Anmeldelink.
4. Die Artikel bleiben öffentlich lesbar; der Seitentext enthält keine Bildinhalte oder Beschreibungen, die das Bild ersetzen.
5. Nachvollziehbarkeit: Abrufprotokoll, Herkunft, Einwilligung und Freigabe je Bild.
6. Die Originale gehören nicht in das GitHub-Repository und nicht in die öffentliche Dateiablage.

## 3. Architektur

```text
Browser ──► Artikelseite (Parser-Ausgabe, benutzerunabhängig zwischengespeichert)
              └─ <figure class="wm-protected" data-media-id="OP-0042"> (Platzhalter-Gerüst)
Nachbearbeitung je Anfrage (Hook ParserOutputPostCacheTransform):
   berechtigt     -> <img src="/geschuetzt/OP-0042?e=<Ablauf>&t=<HMAC>"> mit Beschriftung
   nicht berechtigt -> Platzhalterkasten + Anmeldelink
Browser ──► /geschuetzt/<id> (eigener Einstiegspunkt im Wiki-Container)
              ├─ startet MediaWiki (Sitzung, Benutzer, Gruppen)
              ├─ prüft Recht + signierten Link (an Benutzer-ID und Ablaufzeit gebunden)
              ├─ liest Datei aus privatem Speicher (kein Webroot) und liefert sie aus
              └─ schreibt Abrufprotokoll
```

### 3.1 Speicher

- Privates Verzeichnis außerhalb des Webroots und außerhalb von `images/`, z. B. `/srv/atmed/wikimedica-protected-media/` auf dem Host, schreibgeschützt in den Wiki-Container eingebunden (`/var/www/protected`). Kein Traefik-Pfad zeigt auf dieses Verzeichnis.
- Metadaten je Bild in einer Tabelle `wm_protected_media` der Wiki-Datenbank: `id`, `datei` (Zufallsname), `sha256`, `mime`, `beschriftung`, `artikel_slug`, `quelle`, `einwilligung_ref`, `freigegeben_von`, `freigegeben_am`, `status`.
- Hochladen nur über ein Wartungsskript mit Administratorkonto (kein Upload über die Wiki-Oberfläche). Das Skript entfernt EXIF/Positionsdaten, prüft MIME und Größe, vergibt Zufallsnamen und erzeugt Vorschaugrößen.
- Aufnahme in die verschlüsselte Sicherung des Servers; Originale werden nie in Git abgelegt.

### 3.2 Auslieferung

- Eigener Einstiegspunkt (`protected-media.php` als kleine Erweiterung `WikiMedicaProtectedMedia`), der MediaWiki startet, damit Sitzung und Gruppen gelten.
- Antwort nur bei Recht und gültigem Link; sonst 403 ohne Inhalt. Kopfzeilen: `Cache-Control: private, no-store`, `X-Robots-Tag: noindex, noarchive`, `Content-Disposition: inline`, `X-Content-Type-Options: nosniff`.
- Signierter Link: HMAC über Bild-ID, Benutzer-ID und Ablaufzeit (z. B. 10 Minuten), Schlüssel aus der Wiki-Konfiguration. Ein weitergegebener Link ist damit nach kurzer Zeit und für andere Konten wertlos.
- Abrufbegrenzung je Konto (z. B. 120 Bilder pro Stunde) gegen Massenabzug; optionales dezentes Wasserzeichen mit Benutzerkennung für Bilder mit erhöhtem Schutzbedarf.

### 3.3 Einbettung und Platzhalter

- In Artikeln: Etikett `<geschuetztes-bild id="OP-0042">Beschriftung</geschuetztes-bild>` (Erweiterung registriert das Etikett). Das Markdown-Format im Repository erhält dafür eine eigene Syntax, die `md2wiki.py` in dieses Etikett übersetzt; im Repository stehen nur ID und Beschriftung.
- Die Parser-Ausgabe enthält nur ein Gerüst ohne Bildadresse. Erst der Hook `ParserOutputPostCacheTransform` setzt je Anfrage entweder das Bild oder den Platzhalter ein. Damit bleibt der Parser-Cache benutzerunabhängig und Dateicache für Anonyme (falls aktiv) zeigt nur den Platzhalter.
- Platzhaltertext: „Originalaufnahme aus dem Operationssitus. Nur für registrierte Fachpersonen sichtbar. Bitte anmelden.“ Der Platzhalter verrät weder Inhalt noch Dateinamen.
- Schnittstellen (`action=query`, `Special:Redirect`, `Special:ListFiles`, `Special:Search`, Feeds, `og:image`/PageImages) enthalten die geschützten Bilder nicht, weil sie keine Dateien im Namensraum `File:` sind.

### 3.4 Rollen und Rechte

- Neue Gruppe `wm-fachpersonal` mit Recht `wm-view-protected-media`; zusätzlich `sysop`. Die Berufsnachweisprüfung erfolgt durch Administratoren vor der Aufnahme in die Gruppe, bevorzugt mit Zwei-Faktor-Anmeldung (OATHAuth) als Voraussetzung.
- Verwaltung der Gruppe durch Bureaucrats im bestehenden Verfahren (`$wgAddGroups`).
- Bild-Freigabe (Aufnahme in `wm_protected_media` mit `status = freigegeben`) nur durch Medical Advisor oder Editorial Board; die Prüfung enthält Einwilligung und Anonymisierung.

## 4. Datenschutz und Recht

- Aufnahmen aus dem Operationssitus können Gesundheitsdaten (Art. 9 DSGVO) sein. Voraussetzung je Bild: dokumentierte Einwilligung oder wirksame Anonymisierung (kein Gesicht, keine Tätowierung, keine Namens- oder Datumsangaben, keine Geräte- oder Etikettendaten mit Personenbezug), Herkunft und Rechteinhaber. Rechtliche Prüfung vor erstem Bild: Andreas Tremml bzw. Legal Reviewer.
- Heilmittelwerbegesetz: Bilder dürfen nicht in Verbindung mit Produktnamen werben; Geräte nur sachlich.
- Abrufprotokolle enthalten Benutzerkennung und Bild-ID, Aufbewahrung begrenzen (z. B. 90 Tage).

## 5. Verworfene Alternativen

| Alternative | Grund |
| --- | --- |
| Gesamtes Wiki nur für Angemeldete | widerspricht dem öffentlichen Zweck und der Auffindbarkeit der Artikel |
| `img_auth.php` mit Dateien im Namensraum `File:` | schützt nur die Auslieferung, nicht Beschreibungsseiten, Vorschaubilder und Schnittstellen; benötigt zusätzlich eine Lockdown-Erweiterung, die den ganzen Namensraum sperrt (dann wären auch die öffentlichen Schemazeichnungen gesperrt) |
| Erweiterung NSFileRepo | pflegt eigene Namensräume je Dateigruppe; hoher Wartungsaufwand, Kompatibilität mit MediaWiki 1.43 ungeprüft |
| Weiterleitungs-Authentifizierung am Proxy (Traefik forwardAuth, Authentik) | Anmeldung am Proxy kennt die Wiki-Gruppen nicht; zweite Benutzerverwaltung nötig |
| Bild als eingebettete Daten im Seitentext | landet im Seitenquelltext, im Cache und im Verlauf; kein Schutz |

## 6. Umsetzungsplan (nach Freigabe)

1. Entscheidungen: Rechtsprüfung, Gruppenpolitik (wer wird `wm-fachpersonal`), Aufbewahrung.
2. Erweiterung `WikiMedicaProtectedMedia` (Etikett, Hook, Einstiegspunkt, Tabelle, Wartungsskript, Protokoll) in einem eigenen Zweig; Test auf dem Staging (`wikimedica_app_staging`).
3. Traefik: kein Pfad auf den privaten Speicher; `/geschuetzt/` nur an den Wiki-Container; `robots.txt` mit Sperre.
4. `md2wiki.py` und Importer erweitern (Syntax für geschützte Bilder; keine Bilddateien im Repository).
5. Prüfungen: anonymer Abruf (403), falscher Benutzer, abgelaufener Link, Parser-Cache mit zwei Benutzerarten, Suchmaschinen-Vorschau, Schnittstellenabfragen.
6. Erst danach das erste echte Bild, mit Sicherung und Rückweg (Erweiterung abschalten entfernt die Bildanzeige, Dateien bleiben im privaten Speicher).

Aufwand: etwa zwei bis drei Arbeitstage Entwicklung plus Test; die rechtliche Klärung ist der Engpass.
