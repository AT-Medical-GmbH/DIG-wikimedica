# Übergabe an ATMED-core — Staging-Aufbau und vorbereitete Live-Schaltung

**Owner:** DevOps (ATMED-core-Sitzung) · **Freigaben:** Andreas Tremml · **Stand:** 2026-10-09 · **Status:** Active

Dieses Dokument ist die Arbeitsgrundlage für die Server-Sitzung `claude-code-atmed-core`.
Es fasst zusammen, was aus dem Repository auf `ATMED-core` umzusetzen ist, in welcher Reihenfolge,
und welche Schritte ausdrücklich **nicht** ohne Freigabe ausgeführt werden dürfen.

## 1. Ausgangslage

- Quelle: Repository `AT-Medical-GmbH/DIG-wikimedica`, Branch `claude/wikimedica-production-readiness-bks0x1`,
  Pull Request #257 (Entwurf, noch nicht zusammengeführt). Lokal getestet: 466 Tests bestanden, 16 übersprungen; Linter sauber.
  GitHub Actions dieses Pull Requests laufen derzeit nicht durch (Runner-Problem auf Organisationsebene, kein Codefehler).
- Zielserver: `ATMED-core` (`core.at-medical.de`), Docker Compose. Edge laut DEC-1: zentrales `ATINFRA-gateway`,
  Compose-Variante `infra/docker/docker-compose.gateway-target.yml` (kein eigener öffentlicher Traefik auf core).
- Domains: `wikimedica.info` und `wikimedica.net` gehören AT Medical (Zonen in Cloudflare angelegt, noch ohne Einträge).
  `wikimedica.de` und `wikimedica.com` gehören **nicht** AT Medical; Übernahmeanfragen laufen (Mail-Sitzung).
  Konfiguration und Doku nennen noch `wikimedica.de` als Beispiel; die Domain ist überall über `DOMAIN` in `.env` bzw.
  `$wgServer` austauschbar.
- Entscheidungen und Abweichungen: `docs/architecture/decision-log.md` (DEC-1 bis DEC-12).

## 2. Ziel

1. Staging-Instanz auf `ATMED-core` nach `docs/deployment/staging-first-deployment.md`, nur mit Zugriffsbeschränkung erreichbar.
2. Abnahme, Backup- und Restore-Test dokumentiert.
3. Produktionsinstanz vorbereitet, aber **nicht** live, bis die Gates in Abschnitt 5 erfüllt sind.

## 3. Reihenfolge auf dem Server

Jeder Schritt zuerst lesend prüfen; ein Schritt nach dem anderen; Ergebnis je Schritt notieren.

1. **Bestandsaufnahme (nur lesend):** Docker/Compose-Version, freier Plattenplatz, belegte Ports, vorhandene Netze,
   bestehender Weg vom Gateway zu core (Overlay, Tunnel oder Host-Port). Pfadkonvention des Servers verwenden
   (z. B. unter `/srv`), Pfad zurückmelden. Keine Annahmen über bestehende Container.
2. **Checkout:** Repository in `DEPLOY_PATH` klonen, Branch `claude/wikimedica-production-readiness-bks0x1`
   (nach Merge: `main`). Für Staging ist ein Branch zulässig, für Produktion nur ein Tag `vX.Y.Z` auf `main`.
3. **`.env` anlegen:** `cp infra/env/.env.example infra/env/.env`, alle `REPLACE_WITH_…` ersetzen
   (`openssl rand -hex 32`), Rechte `600`, Kopie der Werte in Vaultwarden. `DOMAIN` für Staging auf einen
   core-Hostnamen setzen (Vorschlag `staging.wikimedica.info`), `APP_BIND`/`APP_PORT` nach Gateway-Route.
   Secrets nie in Atlas, Chat oder Repo.
4. **Staging-Deploy:** `DEPLOY_ENV=staging COMPOSE_FILES=infra/docker/docker-compose.gateway-target.yml`
   `infra/deploy/deploy.sh --tag <branch> --skip-backup` (erster Lauf ohne Datenbank).
5. **MediaWiki-Installation (einmalig):** `php maintenance/run.php install …` mit den `.env`-Werten,
   `infra/mediawiki/LocalSettings.example.php` nach `LocalSettings.php`, `$wgServer` auf die Staging-Domain,
   `update.php`. Registrierung aus, `createaccount` nur Admin (DEC-4).
6. **Gateway-Route und DNS:** Route am `ATINFRA-gateway` auf den core-Port, Cloudflare-Eintrag für den
   Staging-Hostnamen mit Zugriffsbeschränkung (Cloudflare Access oder Basic Auth). Über die zuständige
   Gateway-/Control-Sitzung, nicht raten.
7. **Bot und Systemseiten:** `Special:BotPasswords` für ein eigenes Konto mit bestätigter E-Mail-Adresse,
   Rechte „Edit existing pages" und „Create, edit, and move pages"; Werte als GitHub-Environment-Secrets
   `WIKI_STAGING_API_URL`, `WIKI_STAGING_BOT_USER`, `WIKI_STAGING_BOT_PASSWORD` (durch Andreas im Repo-Environment).
   Dann `infra/deploy/bootstrap-wiki.sh --env staging`.
8. **Abnahme:** Checkliste in `staging-first-deployment.md` Abschnitt „Per release" abarbeiten, Ergebnis notieren.
9. **Backup/Restore:** Cron-Einträge aus `docs/operations/runbook.md`; `infra/deploy/backup.sh`; dann
   `infra/deploy/restore-test.sh`. Offsite laut DEC-7: SFTP auf `ATINFRA-backup`, nur GPG-verschlüsselt
   (`BACKUP_GPG_RECIPIENT`, privater Schlüssel offline). Datum und Dauer in die Go-Live-Checkliste eintragen.
10. **Produktion vorbereiten:** zweites Compose-Projekt (`DEPLOY_ENV=production`, eigene `.env`, eigene Volumes),
    `DOMAIN` erst nach Domain-Entscheidung setzen. Kein Start der Produktionsinstanz vor Freigabe.

## 4. Rückmeldung über Atlas

Nach jedem abgeschlossenen Block (Bestandsaufnahme, Staging läuft, Abnahme, Restore-Test) eine kurze
ERLEDIGT- oder FRAGE-Nachricht mit: Server, Pfad, Compose-Projekt, ausgeführte Kommandos (ohne Secrets), Befund,
offene Punkte. Blockierende Entscheidungen als AUFGABE an Andreas, nicht selbst entscheiden.

## 5. Gates vor der Live-Schaltung (alle Pflicht)

- [ ] Pull Request #257 zusammengeführt, Tag `v1.0.0` auf `main`, GitHub-Environment `production` mit Pflicht-Reviewer.
- [ ] Ausdrückliche Freigabe von Andreas für die Live-Schaltung (Domain, Zeitpunkt) liegt in Atlas vor.
- [ ] Domain-Entscheidung: welche Domain live geht (`wikimedica.info` als Hauptdomain, `.net` als Weiterleitung,
      `.de`/`.com` nach Übernahme), DNS und Gateway-Route eingerichtet, TLS „Full (strict)".
- [ ] Rechtliche Gates aus `docs/deployment/go-live-checklist.md` Abschnitt A: Disclaimer freigegeben,
      Impressum/Datenschutz ohne Platzhalter, Lizenz umgesetzt (DEC-2).
- [ ] Staging-Abnahme, Backup und Restore-Test mit Datum dokumentiert.
- [ ] Mindestens ein Artikel mit `status: published` nach menschlichem Review; Entwürfe bleiben `draft`
      und werden nie nach Produktion importiert (Importer-Gate).

## 6. Rollback

- Deploy: automatisch bei fehlgeschlagenem Health-Check; manuell `infra/deploy/rollback.sh <tag>`.
- Staging-Aufbau: Compose-Projekt stoppen und Volumes entfernen; kein produktives System betroffen.
- Repository: Revert des Merge-Commits.
