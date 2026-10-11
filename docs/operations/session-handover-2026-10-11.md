# WikiMedica – verbindliches Betriebs- und Session-Handover für Codex / Claude Code

**Stand:** 11.10.2026 · **Status:** Produktionsimport nachgewiesen · **Sprache:** Deutsch

**GitHub (Single Source of Truth):** https://github.com/AT-Medical-GmbH/DIG-wikimedica  
**Öffentliche Plattform:** https://wikimedica.info  
**Nachweisartikel:** https://wikimedica.info/index.php?title=Arterielle_Hypertonie

> **An alle zukünftigen Agenten:** Dies ist die Übergabe aus einer erfolgreichen Produktiv-Session, keine Absichtserklärung. Ältere Dokumentationen und das README enthalten inzwischen überholte Aussagen (alte Domain wikimedica.de, noch keine Artikel, API als einziger Importkanal). Diese Aussagen sollen sorgfältig aktualisiert werden. **Niemals** Zugangsdaten, Tokens, Inhalte von Secret-Dateien oder private Netzwerkziele in PRs, Chat-Logs oder Commit-Messages aufnehmen.

## 1. Nachweisbar erreicht

Der erste komplette Import von GitHub **main** in die produktive WikiMedica-Datenbank gelang am 11. Oktober 2026 mittels **MediaWiki 1.43 Maintenance-CLI direkt im Docker-Container**, unabhängig von GitHub Actions und öffentlicher Action API.

Produktive Terminalausgabe:

```text
HEAD: 45dba4873b64038583a658116e0f9b7ecddc6daa
mode=beta-local
Beta import of 1 changed article(s)
{"article":"Arterielle Hypertonie","result":"created","verified":true,"wiki":"production","commit":"45dba4873b64038583a658116e0f9b7ecddc6daa"}
{"due_count":0,"queue":"/var/lib/wikimedica-pull/evidence-review-queue.json"}
Completed successfully: beta-local at 45dba4873b64038583a658116e0f9b7ecddc6daa
```

Danach lieferte `docker exec wikimedica_app php maintenance/run.php getText "Arterielle Hypertonie"` den auf dem Wiki gespeicherten Text einschließlich verwaltetem Marker und deutlichem BETA-Hinweis zurück. Der Betreiber hat zusätzlich bestätigt: **Der Artikel ist auf der öffentlichen Website sichtbar.**

**Noch nicht als erfolgreich nachgewiesen:** Ein späterer geänderter PR, der nach Merge durch einen unbeaufsichtigten systemd-Lauf eine bestehende Seite aktualisiert. Dies ist der nächste End-to-End-Test.

## 2. Installationsstand / Systemgrenzen

**Host:** Ubuntu 26.04.1 LTS, administrativer Zugriff per SSH auf `core` (keine IP-Adressen oder SSH-Geheimnisse ins Git).  
**Produktion:** Docker `wikimedica_app` (Image `mediawiki:1.43`), `wikimedica_db` (`mariadb:10.11`).  
**Staging:** `wikimedica_app_staging`, `wikimedica_db_staging`. Nicht mit Produktion verwechseln!  
Alle vier Container waren am Ende der Session `healthy`.

**Produktive LocalSettings:** `/srv/atmed/stacks/wikimedica/infra/mediawiki/LocalSettings.php`.  
**Staging-LocalSettings:** `/srv/atmed/stacks/wikimedica-staging/infra/mediawiki/LocalSettings.php`.  
**Separater GitHub-Checkout:** `/opt/wikimedica-source`.

**Geplanter automatischer GitHub→MediaWiki-Pull:**

- Dienst: `/etc/systemd/system/wikimedica-beta-sync.service`
- Timer: `/etc/systemd/system/wikimedica-beta-sync.timer`
- Kalender: täglich **06:30 Europe/Berlin** (erster beobachteter Termin 11.10.2026, 06:30 CEST)
- Dienst-ExecStart: `/bin/bash /opt/wikimedica-source/infra/deploy/pull-content-from-github.sh --env production --mode beta-local`
- Letzte verifizierte Kontrolle: **enabled**, **active (waiting)**. Ein automatischer Lauf wurde noch nicht unabhängig bestätigt.
- Log: `journalctl -u wikimedica-beta-sync.service -n 100 --no-pager`
- Zustand: `/var/lib/wikimedica-pull/beta-last-successful-sha` (siehe Abschnitt 5)
- Review-Warteschlange: `/var/lib/wikimedica-pull/evidence-review-queue.json`
- Review-Auditlog: `/var/lib/wikimedica-pull/evidence-reviews.jsonl` (falls vorhanden)
- Exclusiver Lock: `/var/lib/wikimedica-pull/pull.lock`

Keinen Neustart des gesamten Servers und keine Änderung der vier Wiki-Container für normale Artikelimporte.

## 3. Tatsächliche Session-Chronik

1. Vorhandene, ältere MediaWiki-Installation identifiziert, ohne sie neu aufzusetzen. Staging und Produktion sicher auseinandergehalten.
2. Benutzer `Andreas.Tremml` wurde über `docker exec wikimedica_app php maintenance/run.php createAndPromote --force --sysop --bureaucrat ...` als **sysop + bureaucrat** eingerichtet. Rückmeldung `done`; danach `Account exists and nothing to do.` Passwort wurde **nicht** in diese Dokumentation übernommen; initiales Admin-Passwort wurde in einem Chat genannt und muss aus Sicherheitsgründen rotiert werden.
3. Bei kontrollierter MariaDB-Abfrage am 11.10.2026 vorhanden: `WikiAdmin`, `MediaWiki default`, `Maintenance script`, `Andreas.Tremml`. **Keine anderen Konten gelöscht.** Technische Systemidentitäten nicht pauschal entfernen. `WikiAdmin` separat auf tatsächliche Nutzung prüfen, bevor deaktiviert wird.
4. Auf dem Host waren **608 Zombies**, davon **607** unter Python `/app/anwesenheit.py` des Docker-Containers `edu-msg-docblue-anwesenheit`. Kontrollierter Neustart **nur dieses Containers** reduzierte den Zombiestand **608 → 1**. Dieser letzte Zombie wurde einem `turnserver`-Elternprozess zugeordnet. Er kann separat geprüft werden; kein Anlass für einen ungezielten Hostneustart. Swap war zeitweise **91–93 %**, jedoch ca. **13 GiB verfügbarer RAM**.
5. GitHub Actions schlugen bereits vor dieser Session fehl (Issue **#264**, keine erfolgreichen Workflow-Steps). Die Produktionspublikation darf daher **nicht** von GitHub Actions abhängen.
6. PR **#265** schuf serverseitigen Pull und einen ersten BETA-Importer über MediaWiki Action API; **#267** behob einen beschädigten Shell-Case-Abschnitt und korrigierte die Domain auf wikimedica.info.
7. Das API-Botkonto wurde als **`Andreas.Tremml@WikiMedicaImport`** angelegt. Eine alte Umgebungskonfiguration liegt auf dem Server unter `/etc/wikimedica/github-pull.env`, Root-Dateirechte **0600**. Der API-Aufruf gegen `https://wikimedica.info/api.php` ergab **HTTP 403 Forbidden**; die konkrete Proxy/WAF-Ursache ist **ungeklärt**.
8. PR **#268** lieferte `beta-local`: Import per `docker exec wikimedica_app php maintenance/run.php edit`, Rücklesen per `getText`. PR wurde in main gemergt, Commit **45dba4873b64038583a658116e0f9b7ecddc6daa**.
9. Der Betreiber führte `bash -n` für beide Skripte und einen Python-AST-Syntaxcheck erfolgreich durch. `infra/deploy/install-beta-sync.sh` stellte den Timer auf **beta-local** um und importierte den Hypertonie-Pilotartikel. Erfolgs-JSON `created` / `verified: true`; serverseitiges `getText` bestätigte Inhalt.
10. Offenes Brandingproblem laut Betreiber: Das Logo zeigt **BETA doppelt**; die ältere hochgestellte Logo-BETA-Version ist inkonsistent mit der neuen Kennzeichnung. **Codex übernimmt die Korrektur separat**, ohne den zwingend sichtbaren medizinischen BETA-Hinweis auf Artikeln zu entfernen.

## 4. Aktiver Veröffentlichungsweg

**Source of truth:** GitHub `main`, Markdown mit YAML-Frontmatter in `content/`. Beispiel `content/specialties/kardiologie/arterielle-hypertonie.md`.

**BETA-Redaktionsentscheidung des verantwortlichen Betreibers:** Der **von ihm vorgenommene Merge** in `main` gibt den BETA-Pilotartikel zur Veröffentlichung frei. Der Importer kann daher auch Markdown mit `status: draft` importieren, **nur als klar gekennzeichnete BETA-Seite**. Das ersetzt **keine** externe fachärztliche Begutachtung; niemals Reviewer, klinische Sign-offs oder menschliche Reviewdaten erfinden. Vor Hochrisikoinhalten Quellen- und Sicherheitsprüfung beachten.

**Technik:**

1. `infra/deploy/pull-content-from-github.sh` verwendet `flock`, holt `origin/main` in den separaten Checkout und liest den vorherigen Erfolgs-SHA.
2. Bei normalem Timerlauf berücksichtigt `--env production --mode beta-local` neue/geänderte zulässige Markdown-Dateien seit dem vorherigen SHA (nicht pauschal alle historischen Entwürfe).
3. `scripts/publishing/import_merged_beta.py` erzeugt BETA-Hinweis, Managed-Marker und konvertierten Wikitext mittels `scripts/publishing/md2wiki.py`.
4. `scripts/publishing/import_merged_beta_local.py` schreibt die Seite **lokal** über den Produktivcontainer `wikimedica_app`, mit MediaWiki-Editbenutzer **Andreas.Tremml**, und verifiziert den tatsächlichen gespeicherten Text über `getText`. Der **lokale** Importpfad verwendet **weder das BotPassword noch die öffentlich gesperrte API**.
5. Bereits existente, nicht vom Importer verwaltete oder manuell bearbeitete Seiten werden **nicht** überschrieben (Integritätsprüfung durch Managed-Marker/Hash). Änderungen am Text immer über GitHub und PR, nicht durch Handedits in MediaWiki.
6. Erst wenn alle betroffenen Dateien erfolgreich importiert wurden, schreibt der Runner den aktuellen Commit in `/var/lib/wikimedica-pull/beta-last-successful-sha`. Fehler lassen den alten Stand für den nächsten Versuch bestehen.
7. `scripts/review/evidence_review_tracker.py scan` aktualisiert danach die jährliche Fälligkeits-Queue. Diese Queue **führt noch keine KI-Evidenzbewertung durch**.

**WICHTIGE SEPARATION:** Der bisherige reguläre Produktions-Release-Weg `scripts/publishing/import_to_mediawiki.py` mit Release-Tags, `status: published`, Legal- und Review-Gates bleibt bestehen und darf nicht durch die BETA-Ausnahme ausgehöhlt werden.

## 5. Zwingende nächsten Prüfungen / Betrieb

Der manuelle Pilotimport `--only arterielle-hypertonie` hat **nicht zwangsläufig** den allgemeinen Baseline-SHA gespeichert. Bei der vorangehenden Diagnose war die Datei **nicht vorhanden**; nach dem erfolgreichen manuellen Import wurde dies nicht wieder kontrolliert. **Zuerst prüfen, nicht blind überschreiben.**

```bash
# auf dem Produktionshost:
sudo test -s /var/lib/wikimedica-pull/beta-last-successful-sha &&
  sudo cat /var/lib/wikimedica-pull/beta-last-successful-sha ||
  echo "Kein Baseline-SHA gefunden"
sudo systemctl list-timers wikimedica-beta-sync.timer
sudo journalctl -u wikimedica-beta-sync.service -n 100 --no-pager
```

Wenn noch keine Datei vorhanden ist und **keine späteren in main gemergten Artikeländerungen übersehen werden**, nach sorgfältigem Abgleich als Startwert den verifizierten Pilotcommit `45dba4873b64038583a658116e0f9b7ecddc6daa` setzen. Besser ist vorab festzustellen, ob es bereits neuere Main-Commits mit medizinischen Inhaltsänderungen gibt; diese müssen dann beim ersten inkrementellen Sync importiert werden.

Dann Test über `sudo systemctl start wikimedica-beta-sync.service`; Logs und SHA prüfen. Nächster echte Regressionstest: einen kontrollierten PR mit kleiner Änderung an `arterielle-hypertonie.md` mergen, systemd-Dienst starten, Erfolg `updated` und `verified: true` prüfen, Wikitext und öffentliche Darstellung vergleichen. Sicherheitsfall: manuell geänderte Wiki-Seiten werden absichtlich nicht überschrieben.

Regelbetrieb:

```bash
sudo systemctl status wikimedica-beta-sync.timer --no-pager
sudo systemctl start wikimedica-beta-sync.service
sudo journalctl -u wikimedica-beta-sync.service -n 100 --no-pager
sudo docker exec wikimedica_app php maintenance/run.php getText "Arterielle Hypertonie"
```

Die dauerhafte Qualität umfasst Monitoring auf Nichtausführung, Fehler im Journal, Git-Rewrites, fehlende Seitenrevisionen, Performance, Sicherung/Restore und die Web/API-403-Ursache (ohne Firewall pauschal zu öffnen).

## 6. Secret-Verwaltung und Migrationsauftrag an Codex (SEPARATER Server!)

**Identität:** MediaWiki-BotPassword für `Andreas.Tremml@WikiMedicaImport`. **Kein Klartext in GitHub.**

**Aktuell bereits vorhanden, historischer Speicherort auf dem WikiMedica-Produktivhost:** `/etc/wikimedica/github-pull.env`, Variable `WIKI_PRODUCTION_BOT_PASSWORD`, root-only 0600. Die alte Env-Datei enthält außerdem API-Konfiguration. Nur Root lesen lassen, niemals `cat` in Terminal-Logs.

**Vom Betreiber gesondert angelegter lokaler Secret-Speicherort (erst nach gesondertem Terminalbefehl und dessen Erfolg vorhanden):**

```text
/etc/wikimedica/secrets/mediawiki-import-botpassword
```

- Auf dem **produktiven WikiMedica-Host**, root:root, **Datei 0600**, übergeordnetes Verzeichnis **0700**.
- Enthält **ausschließlich den Tokenwert**, mit einem abschließenden Zeilenumbruch. Keinesfalls in Git, PR, Ticket, Issue, Wiki-Seite oder gewöhnliche Logs übernehmen.
- **Codex-Auftrag nach bestätigtem Anlegen:** **Diesen Secret-Wert vom produktiven WikiMedica-Server auf den anderen Server übertragen, auf dem die zentrale Passwortverwaltung läuft, und ihn dort in dessen Passworttresor als eigenständigen Eintrag „WikiMedica / MediaWiki Import BotPassword“ importieren.** Ziel ist der zentrale Tresor des Betreiber-Ökosystems, nicht irgendein beliebiger Server, Nextcloud-Shares oder Klartext-Dateiverzeichnis.
- **Der exakte Zielhost, Tresortyp, Zugriff, Autorisierung und API/CLI sind in dieser Session NICHT ermittelt.** Codex muss die vorhandene IT-Dokumentation/gesicherten Infrastrukturkonfigurationen dazu befragen und vor Transfers das richtige Ziel, die Identität und die Berechtigungen bestätigen. **Keine Zieladresse raten oder erfinden.**
- **Transport nur verschlüsselt und authentisiert** (SSH/SFTP zu geprüfter Zielidentität oder die authentisierte TLS-API des konkreten Vault). Bevorzugt Secret direkt über einen authentisierten Vault-Client oder -API, ohne Klartext-Zwischendateien auf dem Zielserver und ohne Shell-Prozessargumente; stdout, Shell-Tracing, Command-History, Debug-Logs und GitHub Actions dürfen den Wert niemals enthalten. **Keine Ausführung eines über das Netzwerk geholten Shellskripts.**
- Vault-Eintrag mit Bezeichnung, Dienst/URL und Bot-Benutzername dokumentieren, **nicht** mit Passwort. Bei Bedarf zentrale Secret-ID/Referenz im internen Operations-DMS festhalten.
- **Nach Tresor-Readback/Audit-Bestätigung:** Die lokale separate Secret-Datei und das alte BotPassword in `/etc/wikimedica/github-pull.env` als veraltete Kopien entfernen bzw. so anpassen, dass der aktive `beta-local`-Dienst weiter läuft. Vorher prüfen, ob andere Dienste/Importer `beta-import` oder API-Zugangsdaten noch verwenden; andernfalls auf den Vault umstellen und erst danach lokale Kopien löschen. **Keinesfalls unbestätigt löschen.**
- Der aktive **beta-local**-Importer braucht das BotPassword nicht; die systemd-Unit lädt momentan die optionale alte EnvironmentFile noch. Codex soll dieses unnötige EnvironmentFile im lokalen Betriebsmodus nach erfolgreicher Tresormigration entfernen und den Dienst anschließend prüfen. Das Token nicht als MediaWiki-Adminpasswort missverstehen.
- Authentisierung/Autorisation und Rotation regeln; das während dieser Session im Chat gezeigte **Admin-Startpasswort** muss unabhängig davon gewechselt werden.

## 7. KI-Evidenzprüfungen und medizinischer Betrieb

Das Konzept: pro Artikel mindestens alle **12 Monate** ein *echter* KI-unterstützter Evidenzabgleich gegen verifizierte Quellen, zusätzlich bei relevanten neuen Leitlinien/Publikationen. Bei `no_change`: **nur KI-/Evidenz-Prüfdatum aktualisieren**, niemals das unabhängige menschliche Reviewdatum fingieren. Bei `update_required`, `uncertain` oder `safety_alert`: entsprechenden Fachreview-/Sicherheitsprozess auslösen.

`scripts/review/evidence_review_tracker.py` erstellt heute **nur eine Queue und akzeptiert auditierbare externe Prüfergebnisse**. Es ruft selbst kein KI-Modell auf. `due_count: 0` beim Pilotlauf bedeutet **keine fälligen Reviews nach Queue-Logik**, nicht „alle Artikel KI-geprüft“. GitHub-Issue **#266** behandelt die echte Agentenimplementation; hier besonders AI-Modellversion, Quelle, Suchprotokoll, Inhalts-Hash, Quellenmonitor-/Leitlinienmonitor-Health und Safety-Signale berücksichtigen. Kein Phantomreview.

## 8. Konkreter Codex-Backlog

1. **Sicherheitsrelevant:** Admin-Startpasswort-Rotation bestätigen, BotPassword in den **zentralen Tresor auf separatem Server migrieren** (Abschnitt 6), lokale Alt-Kopien erst nach bestätigtem Transfer beseitigen; systemd-Unit keine unnötigen Secrets mehr laden lassen.
2. **Sync-Baseline** `beta-last-successful-sha` kontrollieren/korrigieren, ohne gemergte Änderungen zu überspringen.
3. **Zweiter E2E-Test:** Änderung an bestehendem Hypertonieartikel via GitHub PR mergen → `beta-local` → `updated` / `verified: true` / sichtbarer Wiki-Stand.
4. **Branding:** doppelte BETA-Auszeichnung im Logo beheben, ältere hochgestellte BETA-Variante vereinheitlichen. Medizinischen BETA-Warnhinweis auf Artikel unbedingt beibehalten.
5. **Doku modernisieren:** `README.md`, `docs/operations/server-sync-beta.md`, weitere altdomain-Links und alte Preproduction-Aussagen mit belegten Befunden aktualisieren, ohne das reguläre Release-Verfahren zu verwässern.
6. **WAF/Proxy:** HTTP 403 auf öffentlicher API diagnostizieren; keine unkontrollierten Proxy-, Cloudflare- oder DNS-Änderungen. Für den produktiven lokalen Import ist die API nicht erforderlich.
7. **Monitoring/Backup:** systemd-OnFailure und Fehleralarme, Lock-/SHA-/Importfehlermonitoring, Restoretest, Logrotation und kontrollierte Release-Rollback-Prozedur nachziehen.
8. **Evidenzprüfung:** Issue #266 mit Quellenbelegen und realem KI-Prüfagenten implementieren; menschliche Reviewdaten strikt getrennt lassen.
9. **Konten:** `WikiAdmin` auf Nutzung prüfen und ggf. sperren; technische Benutzer `MediaWiki default`, `Maintenance script` nicht blind löschen.
10. **Technische Schuld:** Import-Code hat hardcodierten Editbenutzer `Andreas.Tremml` und den Container `wikimedica_app`: dokumentieren, später über geprüfte Konfiguration parametrisierbar machen. Sicherstellen, dass GitHub-Merge tatsächlich nur mit Betreiberfreigabe möglich ist.

## 9. Dokumentations- und Änderungsregeln für Agenten

- Diesen Handover aus dem Repo vor allen Operationen lesen; neue Befunde mit Datum und nachvollziehbaren Logs/Commits dokumentieren.
- **Kein Geheimnis abrufen oder an externe Agenten ausgeben, nur um einen Pfad zu verifizieren.** Für Secret-Migration den passenden authentisierten Zielconnector/Vault benutzen.
- Keine Produktionsänderungen als „erledigt“ melden, bevor der Benutzer/Operator deren Terminalergebnis belegt hat.
- GitHub-PRs vor dem Deploy mergen; `main` ist die verbindliche Quelle; bei Serveränderungen Syntaxchecks durchführen.
- Staging/Produktion strikt trennen; keine pauschalen Docker-Restarts oder Konto-/Artikel-Massenlöschungen.
- Verantwortlicher Betreiber: fachärztlicher Projektleiter; Merge bedeutet **Beta-Publikationsentscheid**, nicht automatisch unabhängige medizinische Begutachtung.

## 10. Referenzen

- Pilotartikel: GitHub PR **#261**
- GitHub Actions-Problem: Issue **#264**
- Erstes Server-Pull-Verfahren: PR **#265**
- KI-Evidenzagent noch nicht umgesetzt: Issue **#266**
- Shell-/Domain-Fix: PR **#267**
- Erfolgreicher lokaler Docker-Weg: PR **#268**, gemergter Commit **45dba4873b64038583a658116e0f9b7ecddc6daa**
- Live-Seite: https://wikimedica.info/index.php?title=Arterielle_Hypertonie
