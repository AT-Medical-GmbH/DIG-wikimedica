# WikiMedica: täglicher GitHub → MediaWiki-Beta-Import ohne GitHub Actions

> **WICHTIG: HISTORISCHE API-VARIANTE – Stand 11.10.2026:** Der unten dokumentierte `beta-import`-Weg via öffentlicher MediaWiki-API ist auf wikimedica.info an HTTP 403 gescheitert und **nicht** der produktive Standard. Seit PR #268 ist der erfolgreich getestete Modus **`beta-local`** aktiv (MediaWiki-Wartungsskripte im Docker-Container, **kein BotPassword erforderlich**). Für korrekte Befehle, betriebliche Zuständigkeiten, Sicherheitsregeln, den Live-Nachweis und die Vault-Migration gilt **[Session-Handover 11.10.2026](session-handover-2026-10-11.md)**. Den ursprünglichen Text unten nur als historische Implementationsbeschreibung verwenden.


**Stand:** 11.10.2026. **Einsatz:** auf dem Server der produktiven MediaWiki-Installation.

## Prinzip

In der Beta-Phase gilt der Merge eines Artikels in `AT-Medical-GmbH/DIG-wikimedica` / `main` als redaktionelle Veröffentlichungsentscheidung des verantwortlichen Betreibers.

Der Server zieht den GitHub-Stand über öffentliches HTTPS-Git und importiert **nur neue oder geänderte Markdown-Artikel** in MediaWiki. Die Seiten erhalten einen unübersehbaren BETA-Hinweis; der Prozess behauptet keine unabhängig erfolgte Fachbegutachtung. Er schreibt **nicht** in die produktiven Docker-Container hinein, sondern nutzt die authentifizierte MediaWiki Action API mit einem eingeschränkt berechtigten Botkonto.

Der bestehende reguläre Produktionsimport mit Release-Tag und seinen formalen Freigaberegeln bleibt unangetastet. Dieses Verfahren ist ein ausdrücklich getrenntes Beta-Veröffentlichungsverfahren.

## Voraussetzung

- Linux-Server mit systemd, Git und Python 3 sowie PyYAML (`sudo apt install -y git python3-yaml` auf Debian/Ubuntu).
- Bereits erreichbare MediaWiki-Installation unter `https://wikimedica.de/api.php`.
- Eigenes MediaWiki-Konto mit bestätigter E-Mail-Adresse. Unter `Special:BotPasswords` ein **BotPassword** für den Import anlegen; Berechtigungen für das Erstellen/Bearbeiten von Seiten, keine Administrationsrechte. Den dabei erzeugten Namen `Account@BotName` und das Token nur am Server eingeben.
- Aufruf mit sudo für die erstmalige systemd-Einrichtung; Zugangsdaten werden ausschließlich in `/etc/wikimedica/github-pull.env` mit Dateirechten `0600` abgelegt.
- **PR erst mergen**, bevor der Installationsbefehl ausgeführt wird.

## Installation (auf dem WikiMedica-Server)

```bash
sudo apt-get update
sudo apt-get install -y git python3-yaml
sudo git clone --branch main https://github.com/AT-Medical-GmbH/DIG-wikimedica.git /opt/wikimedica-source
sudo bash /opt/wikimedica-source/infra/deploy/install-beta-sync.sh
```

Der Installer fragt die MediaWiki-API-URL und die BotPassword-Zugangsdaten ab, legt `wikimedica-beta-sync.service` und `wikimedica-beta-sync.timer` an, aktiviert den täglichen Lauf **06:30 Uhr Europe/Berlin** und importiert danach ausdrücklich den bereits gemergten Hypertonie-Pilotartikel. Anschließend muss die Seite auch über die öffentliche MediaWiki-URL geprüft werden; maßgeblich sind die im JSON-Ergebnis zurückgemeldete Seitenrevision und die korrekte Darstellung.

**Erwarteter Seitentitel:** `Arterielle Hypertonie` (normaler Wiki-Artikelname, mit BETA-Hinweis). Die exakte Seitennavigation hängt von der installierten URL-Konfiguration ab.

Beim allerersten automatischen Lauf ohne Importzustand wird nur eine Baseline angelegt, um nicht sämtliche vorhandenen historischen und möglicherweise ungeprüften Entwürfe auf einmal zu veröffentlichen. Der manuelle Pilotimport oben setzt gleichzeitig diese Baseline.

## Wiederkehrende Ausführung und Prüfung

```bash
sudo systemctl list-timers wikimedica-beta-sync.timer
sudo systemctl start wikimedica-beta-sync.service
sudo journalctl -u wikimedica-beta-sync.service -n 100 --no-pager
```

Ein erfolgreicher Job:
1. Sperrt parallele Läufe mit `flock`.
2. Prüft den unveränderten, separaten Git-Checkout und holt `origin/main` ab.
3. Vergleicht den zuletzt erfolgreich synchronisierten Commit mit dem neuen `main` und identifiziert neue oder geänderte Artikel in den zugelassenen `content/`-Verzeichnissen.
4. Wandelt Markdown sicher in Wikitext um und aktualisiert nur bereits **beta-managed** Seiten; fremde oder von Hand geänderte Seiten werden nicht überschrieben.
5. Liest jede Seite unmittelbar über die MediaWiki Action API zurück und verifiziert die übernommenen Inhalte.
6. Aktualisiert den Synchronisationsstand **erst nach erfolgreichem Import aller betroffenen Dateien**.
7. Erstellt den Fälligkeitsbericht für die jährlichen Evidenzprüfungen.

Für einzelne Kontrollimporte:

```bash
sudo bash /opt/wikimedica-source/infra/deploy/pull-content-from-github.sh --env production --mode beta-import --only arterielle-hypertonie
```

Die gespeicherten Daten liegen unter `/var/lib/wikimedica-pull/`; der Timer ist unabhängig von GitHub Actions. Keine Benutzerkonten oder Bot-Tokens in GitHub-PRs oder Wiki-Seiten posten.

## Jährliche KI-Aktualitätsprüfung

Der tägliche Import baut bereits die Fälligkeitswarteschlange unter `/var/lib/wikimedica-pull/evidence-review-queue.json`. Der Quellen-/KI-Agent wird anschließend angebunden. Ein gültiges Ergebnis `no_change` dokumentiert die Aktualitätsprüfung und setzt die nächste Prüfung +12 Monate; `update_required`, `uncertain` und `safety_alert` setzen keine Frist zurück und erfordern die entsprechenden Maßnahmen.

**Bis ein echter KI- und Quellenprüfagent angeschlossen ist, werden keine Artikel automatisch als aktuell bestätigt.**

## Bekannte Grenzen und Betriebshinweise

- Nur ein PR-Merge berechtigt in der Pilotphase zur Veröffentlichung, nicht irgendein beliebiger PubMed-JSON-Eintrag oder ein offener Branch.
- Die vorhandenen alten `draft`-Artikel werden durch die Erstinstallation **nicht massenhaft veröffentlicht**.
- Die Beta-API-Authentifizierung braucht ein gültiges BotPassword; wenn die API, E-Mail-Bestätigung oder Rechte fehlen, endet der Import mit Fehler, nicht mit einer Erfolgsmeldung.
- Existiert eine Seite bereits und wurde nicht von diesem Beta-Importer angelegt, wird sie zum Schutz gegen Überschreiben nicht übernommen. Dann ist eine bewusste Migrationsentscheidung erforderlich.
- Archivierung, Löschungen und sicherheitsrelevante Rücknahmen erfolgen nicht automatisch im Beta-Importer. Sie müssen über den regulären Sicherheitsprozess behandelt werden; entsprechend markierte Inhalte werden nicht neu importiert.
- Der Verlauf der GitHub-Versionen ist bei jedem Release nachvollziehbar; für einen belastbaren Betrieb sind Servermonitoring und Offsite-Backup zusätzlich erforderlich.
