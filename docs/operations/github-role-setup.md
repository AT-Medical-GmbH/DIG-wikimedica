# GitHub-Rollen einrichten – WikiMedica

**Stand:** 2026-10-11 · **Status:** Umsetzungsvorschlag / administrativer Handlungsbedarf

## Festgestellter Ist-Zustand

Das Repository liegt unter `AT-Medical-GmbH/DIG-wikimedica`. Die bestehende `.github/CODEOWNERS` verweist dagegen auf `@atmedical-wikimedica/...`, also einen **anderen Organisationsnamen**. Laut `docs/operations/github-teams-needed.md` sind diese Teams nicht gültig bestätigt. Ein bloßes Anlegen einer Rollenbeschreibung schafft **keine GitHub-Teamrechte**. Die hier genutzte GitHub-Integration stellt keine Aktionen zum Erstellen von Organisationsteams, Vergeben von Team-Repository-Rechten oder Einrichten von Branch-Rulesets bereit. Daher wird CODEOWNERS bis zur tatsächlichen Team-Einrichtung **nicht** auf hypothetische Teamnamen geändert.

## Empfohlene GitHub-Teams in der vorhandenen Organisation

| Team-Slug in AT-Medical-GmbH | GitHub-Recht | Fachliche Aufgabe |
| --- | --- | --- |
| `wikimedica-medical-authors` | Triage bzw. Write für Branches/PRs | Autorinnen und Autoren |
| `wikimedica-medical-editors` | Write | Fachreview, Specialty Editors |
| `wikimedica-gender-medizin-editors` | Write | Querschnittsreview Gender-Medizin |
| `wikimedica-medical-advisors` | Write | Unabhängige Hochrisiko-Freigabe |
| `wikimedica-editorial-board` | Write/Maintain nach Bedarf | Redaktion, Richtlinien, Freigabe |
| `wikimedica-legal` | Write | Recht, Quellen, Lizenzen |
| `wikimedica-admins` | Admin, sehr restriktiv | Organisation und Notfalladministration |
| `atmed-devops` (bestehend, Mitgliedschaft prüfen) | Write/Maintain | CI, Infrastruktur, Release |

Eine eigene `wikimedica-editors`-Gruppe ist optional; Default-Codeowner kann die Editorial-Board-Gruppe sein. Qualifizierte Apotheker als Arzneimittelreviewer werden innerhalb der medizinischen Reviewer erfasst; deren **zusätzliche** Prüfung muss im Review-Prozess nachgewiesen werden. GitHub-CODEOWNERS mit mehreren Teamnamen verlangt nicht automatisch die Freigabe **jedes** Teams.

## Einrichtungsreihenfolge für einen Organisationsinhaber

1. In der GitHub-Organisation `AT-Medical-GmbH` unter **Teams** die Gruppen anlegen, bevorzugt privat/visible gemäß organisatorischer Richtlinie; Team-Slugs notieren.
2. Verantwortliche Personen nach Identitäts-, Qualifikations- und Interessenkonfliktprüfung einladen. 2FA verpflichtend; möglichst keine unnötigen Adminrechte.
3. Teams explizit auf `DIG-wikimedica` berechtigen. CODEOWNERS-Teams benötigen **Write**-Rechte und müssen für CODEOWNERS geeignet/sichtbar sein; reine Triage-Rechte reichen für Codeowner nicht.
4. `.github/CODEOWNERS` in einem gesonderten überprüften PR auf `@AT-Medical-GmbH/<team-slug>` korrigieren; alle Einträge prüfen, insbesondere `content/`, `content/templates/`, `docs/legal/`, `infra/`, `.github/`, `scripts/` und `data/metadata/`. Die CODEOWNERS-Datei selbst besonders schützen.
5. Branch-Schutz/Ruleset für `main`: Pull Request erforderlich, `ci-ok` als required check, erforderliche unabhängige Reviews, Codeowner-Review, veraltete Freigaben verwerfen, Gespräche auflösen, Force-Push und Löschung sperren; Bypass auch für Admins soweit praktikabel ausschließen.
6. **Wichtig:** Für medizinische Inhalte reichen allgemeine Codeowner-Reviews allein nicht, um die in der Review-Policy verlangten unterschiedlichen Personen/Funktionen zu garantieren. Zwei unabhängige Genehmigungen für `content/**` sowie gesonderter dokumentierter Apotheker-/ärztlicher Review und Medical-Advisor-Sign-off bei Pharmaka müssen durch zusätzliche Regeln/Prozessprüfungen nachgewiesen werden.
7. `staging` und `production` als GitHub-Environments konfigurieren; `production` nur nach manueller Freigabe durch benannte Berechtigte. Secrets ausschließlich in GitHub-Secrets/Server-Secret-Store, nie im Repo.
8. Test-PRs für `content/`, `docs/legal/` und `infra/` eröffnen. Tatsächlich angeforderte Codeowner, Statuschecks und Merge-Sperren prüfen. Ergebnisse im Go-live-Protokoll dokumentieren.
9. Erst nach erfolgreichem Test die GitHub-Gates der `docs/deployment/go-live-checklist.md` abhaken.

## Abgrenzung zur MediaWiki-Installation

Die Rollen in GitHub steuern Verfassen und Review; MediaWiki bleibt weitgehend schreibgeschützt. Der `importbot` veröffentlicht nur durch die Pipeline freigegebene Inhalte. Die bestehenden MediaWiki-Gruppen sind in `docs/editorial/roles-and-permissions.md` dokumentiert. Keine parallele freie Artikelbearbeitung in MediaWiki aktivieren.

## Noch offen

- Team-Erstellung und Team-Mitglieder: Organisationsinhaber
- CODEOWNERS-Korrektur: nach verifizierter Team-Erstellung
- Branch-Regeln, Environments, Secrets und Test-PR: Repository-Administrator/DevOps
- Namen und Qualifikationen der Fachreviewer und Medical Advisors: Editorial Board
- Produktionsfreigabe: Go-live-Checkliste; keine automatische Aktivierung
