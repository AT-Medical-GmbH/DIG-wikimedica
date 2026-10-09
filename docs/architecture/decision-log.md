# Entscheidungsprotokoll — WikiMedica

**Stand:** 2026-10-09 · **Entscheider:** Andreas Tremml (Management) · **Status:** Active

Entscheidungen zu den offenen Punkten aus `production-readiness-concept.md`. „Folgearbeit" nennt, was daraus noch umzusetzen
ist; bis dahin gelten die Sperren der Skripte unverändert.

| ID | Entscheidung | Abweichung von der Empfehlung | Folgearbeit |
|---|---|---|---|
| DEC-1 | Anbindung über das zentrale ATINFRA-gateway (Compose-Variante `gateway-target`) | nein | Gateway-Routing und Cloudflare-Eintrag einrichten; Staging mit derselben Variante testen |
| DEC-2 | Artikel unter CC BY-SA 4.0, Code proprietär (`LICENSE` bleibt) | nein | `license` in Artikeln erst nach Legal-Bestätigung setzen; Rechtsprüfung der Lehrbuch-Zusammenfassungen (siehe DEC-8) |
| DEC-3 | APCu + Datenbanksuche, kein Redis/OpenSearch zum Start | nein | Bei Last oder schlechter Suchqualität neu bewerten |
| DEC-4 | Keine öffentliche Registrierung, Konten nur durch Admin | nein | `$wgGroupPermissions` prüfen (Registrierung aus, `createaccount` nur für Admin) und im Staging-Test absichern |
| DEC-5 | Drittanbieter-Analytics mit Consent-Banner | **ja** (Empfehlung: kein Tracking) | Anbieter wählen, AVV, Consent-Management, Datenschutzerklärung und Cookie-Hinweis anpassen; `privacy-notes.md` und `monitoring.md` aktualisieren; ohne Einwilligung kein Skript laden |
| DEC-6 | GitHub-Teams `wm-editorial`, `wm-medical-review`, `wm-devops`, `wm-legal` | nein | Teams anlegen, `.github/CODEOWNERS` darauf umstellen, Branch-Protection setzen |
| DEC-7 | Offsite-Backup per SFTP auf ATINFRA-backup, GPG-verschlüsselt | nein | SFTP-Zugang, GPG-Schlüssel (Offline-Kopie), `BACKUP_SFTP_*` und `BACKUP_GPG_RECIPIENT` setzen, Restore-Test |
| DEC-8 | Lehrbuch-Entwürfe: erst Rechtsprüfung, dann Fachreview, dann Quellen aktualisieren | nein | Legal-Auftrag; je Artikel Review und Primärquellen (PubMed, Leitlinien) |
| DEC-9 | PubMed-Workflow: Bot-Ausnahme in der Branch-Protection | **ja** (Empfehlung: Pull-Request pro Lauf) | Eng begrenztes Bot-Token (nur `data/pubmed/`), Ausnahme dokumentieren; Risiko: schwächerer Schutz von `main` — Pfadbeschränkung per Ruleset prüfen |
| DEC-10 | Medical Advisor intern, externe Fachreviewer je Fachgebiet | nein | Personen benennen (`roles-and-permissions.md`) |
| DEC-11 | Dependabot: sofort untersuchen und beheben | nein | Siehe Befund unten |
| DEC-12 | Go-Live direkt in Produktion mit allen Artikeln nach Review | **ja** (Empfehlung: Staging, Soft-Launch) | Staging-Abnahme und Restore-Test bleiben Pflicht-Gates; Review-Engpass einplanen |

## Anmerkungen zu abweichenden Entscheidungen

- **DEC-5:** Tracking auf einem Medizinportal erfordert eine wirksame Einwilligung vor dem Laden von Skripten (TTDSG § 25 / DSGVO). Bis die
  Umsetzung steht, bleibt Tracking aus.
- **DEC-9:** Mit Bot-Ausnahme kann der Workflow ohne Review auf `main` schreiben. Empfohlene Absicherung: Token nur für den Bot-Account, Ruleset
  mit Pfadbeschränkung, Daten dürfen keine Veröffentlichung auslösen (der Deploy läuft nur per Release-Tag).
- **DEC-12:** „Alle Artikel" heißt: alle, die den Review-Prozess bestehen. Nicht freigegebene Artikel bleiben `draft`; die Skripte verhindern ihre
  Veröffentlichung.

## Dependabot-Befund (2026-10-09)

`npm audit` meldet 6 Schwachstellen (3 niedrig, 3 mittel), alle in transitiven Abhängigkeiten von `markdownlint-cli` (u. a. `katex`,
`smol-toml`), ausschließlich in der CI-Prüfkette, nicht im Betrieb. Eine Aktualisierung ist erst mit einer neuen Version von
`markdownlint-cli` möglich; `npm audit fix --force` würde auf eine ältere Version zurückfallen. Die auf dem Default-Branch gemeldeten
Alerts (1 hoch, 1 mittel) sind mit den verfügbaren Werkzeugen nicht einsehbar und müssen im Dependabot-Dashboard geprüft werden.
