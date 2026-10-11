# WikiMedica – Onboarding für Autorinnen, Autoren und Fachreviewer

**Version:** 1.0 · **Stand:** 2026-10-11 · **Verantwortlich:** Editorial Board · **Geltungsbereich:** GitHub-Repository DIG-wikimedica und MediaWiki auf wikimedica.de

> **Kurzregel:** Ein Artikel wird in GitHub als Markdown-Datei verfasst, durch unabhängige qualifizierte Menschen geprüft und erst nach redaktioneller Freigabe über den bestehenden Release-/Importprozess in MediaWiki veröffentlicht. Änderungen direkt im öffentlichen Wiki sind kein Redaktionsweg.

## 1. WikiMedica in 90 Sekunden

WikiMedica ist ein deutschsprachiges, evidenzbasiertes medizinisches Nachschlagewerk für Fachpersonal und – bei geeigneten Themen – Patienten. Die Texte sind sachlich, unabhängig, nachprüfbar und in eigenen Worten formuliert. GitHub ist die verbindliche Inhaltsquelle; MediaWiki zeigt freigegebene Versionen. Die klinische Verantwortung liegt bei benannten Menschen, nicht bei KI.

**Hier beginnen:** [Repository](../../README.md) · [Artikelvorlagen](../../content/templates/) · [Metadatenschema](../../data/metadata/article-schema.yaml) · [Rollen](../editorial/roles-and-permissions.md) · [Review-Policy](../editorial/peer-review-policy.md) · [KI-Richtlinie](../editorial/ai-assistance-policy.md) · [Go-live](../deployment/go-live-checklist.md).

**Kontakt:** Redaktion: editorial@wikimedica.de · Technik: tech@wikimedica.de. Keine Patienten- oder sonstigen vertraulichen personenbezogenen Daten in Issues, Pull Requests, Quelltext, Bildern oder KI-Prompts.

## 2. Rollen und Verantwortlichkeiten

| Rolle | Aufgabe | Darf nicht |
| --- | --- | --- |
| Registrierter Autor / Medical Author | Quellen recherchieren, Artikel im eigenen Branch verfassen, PR eröffnen, Rückmeldungen umsetzen | Eigene Beiträge selbst freigeben oder veröffentlichen |
| Fachreviewer | Medizinische Aussagen, Quellen, Aktualität, Risiken und fachliche Vollständigkeit prüfen | Eigene Texte als unabhängiger Reviewer abzeichnen |
| Specialty Editor | Reviewer zuweisen, Review koordinieren, fachlich geeignete PRs redaktionell freigeben | Fehlende Fachreviews ersetzen |
| Medical Advisor | Unabhängige zusätzliche klinische Freigabe bei Hochrisiko-Inhalten | Als Mitautor desselben Beitrags den Advisor-Sign-off geben |
| Editorial Board / Medical Director | Richtlinien, Eskalationen, Interessenkonflikte, finale klinische Entscheidungen | Ungeprüfte Artikel durchwinken |
| Legal Reviewer | Urheberrecht, Lizenzen, Einwilligungs-/Rechtstexte prüfen | Fachreview ersetzen |
| DevOps / Administrator | CI, GitHub-Rechte, sichere Releases, MediaWiki-Import, Wiederherstellung | Klinische Freigabe allein aufgrund technischer Rechte erteilen |
| KI-Assistent | Gliederungen und Entwürfe unter dokumentierter menschlicher Kontrolle unterstützen | Quellen erfinden, Dosiswerte festlegen, reviewen, mergen oder publizieren |

Die verbindliche detaillierte Rechte- und Statusmatrix steht in [roles-and-permissions.md](../editorial/roles-and-permissions.md). GitHub-Teammitgliedschaft und fachliche Zulassung sind getrennte Entscheidungen. Rechte werden nur nach dokumentierter Identitäts- und Qualifikationsprüfung vergeben.

## 3. Erstregistrierung und Zugang

1. GitHub-Konto mit Zwei-Faktor-Authentifizierung einrichten. Bei Bedarf GitHub-Grundlagen (Branches, Commits, Pull Requests) durchgehen.
2. Bei der Redaktion mit Name, beruflicher Qualifikation, Fachgebiet, Einrichtung, beruflicher Kontaktadresse, optional ORCID und gewünschter Rolle bewerben. **Nachweise und personenbezogene Unterlagen nur über den von der Redaktion freigegebenen vertraulichen Kanal**, niemals in einem öffentlichen Issue/PR.
3. Autorenvereinbarung, Urheber-/Lizenzbedingungen, Vertraulichkeit und Interessenkonflikte klären. Interessenkonflikte jährlich und vor einschlägigen Artikeln aktualisieren.
4. Editorial Board prüft Identität und Qualifikation, ordnet Fachgebiet und GitHub-Team zu, erklärt die Review-Regeln und stellt Vorlagen bereit.
5. Neue Mitarbeitende bearbeiten zunächst einen Probeartikel bzw. ein betreutes Review. Rechte werden nach dem Prinzip der minimal erforderlichen Berechtigung erteilt.
6. Beim Austritt: GitHub-Zugriff und gegebenenfalls Wiki-Gruppen am selben Tag entziehen; offene Aufgaben neu zuweisen.

**Wichtig:** Teamnamen in CODEOWNERS sind gegenwärtig nicht korrekt auf die tatsächliche Repository-Organisation ausgerichtet. Vor einer verbindlichen Codeowner-Freigabe müssen die Teams erstellt, Berechtigungen erteilt und CODEOWNERS korrigiert werden; siehe [Team-Einrichtung](../operations/github-role-setup.md). Bis dahin ist ein grüner CI-Status **kein** Nachweis eines gültigen medizinischen Reviews.

## 4. Themenwahl und Recherche

1. Bestehende Artikel und offene Issues durchsuchen, um Doppelarbeit zu vermeiden. Neues Thema mit Fachgebiet, Zielgruppe und Priorität vorschlagen.
2. Quellenhierarchie: aktuelle Fachinformation/EMA/BfArM für Arzneimittelsicherheit, einschlägige AWMF-/NVL-/Fachgesellschaftsleitlinien, systematische Reviews, hochwertige Primärstudien, RKI/Destatis/WHO für Epidemiologie. Studien und Leitlinien mit Jahr/Version angeben; Geltungsbereich Deutschland beachten.
3. Zahlen nur mit Bezugsjahr, Grundgesamtheit und Zählweise nennen. Bei kontroverser Evidenz Unterschiede transparent darstellen.
4. Jeder klinisch relevanten Aussage eine überprüfbare Quelle zuordnen; Zitate sparsam und urheberrechtskonform; keine Wikipedia-Texte kopieren.
5. Literaturangaben vollständig erfassen (Autor/Herausgeber, Titel, Journal/Institution, Jahr, DOI/PMID/URL, ggf. Abrufdatum). Im Fließtext ausschließlich numerische hochgestellte Referenzen über den vorhandenen Import-/Konvertierungsweg verwenden; Ausgabe auf Staging prüfen. Keine ausgedachten DOIs/PMIDs.
6. Bei verbreiteten Erkrankungen zusätzlich eine deutlich abgegrenzte verständliche Erklärung für Laien; diese ersetzt nicht die Fachinformation und benötigt eine Verständlichkeitsprüfung.

## 5. Einen Artikel anlegen – Schritt für Schritt

1. Im Repository die **bestehende passende Vorlage** unter `content/templates/` auswählen: Fachartikel, Patientenartikel, Arzneimittel oder Therapie. Keine parallele eigene Schema-Variante erfinden.
2. Einen Feature-Branch von `main` anlegen (z. B. `article/hypertonie-erster-entwurf`), per GitHub-Weboberfläche oder Git-Client.
3. Artikel im bestehenden `content/`-Verzeichnis der passenden Kategorie speichern. Der Dateiname ohne `.md` muss **exakt** dem `slug` im YAML-Frontmatter entsprechen; Kleinbuchstaben, ASCII, Bindestriche. Nach Erstveröffentlichung ist der Slug unveränderlich.
4. Alle Pflichtfelder anhand von `data/metadata/article-schema.yaml` befüllen, insbesondere `title`, `slug`, `specialty`, `article_type`, `status`, `version`, `authors`, `reviewers`, `created`, `updated`, `risk_level`, `target_audience`, `sex_gender_relevance`, `references`. Für neue Dateien `status: draft` oder `in-review` verwenden. Keine fiktiven Reviewer/Sign-off-Daten eintragen.
5. Nach Vorlage definierte Abschnitte ausformulieren: Definition, Epidemiologie, Ursachen/Risikofaktoren, Pathophysiologie, Klinik, Diagnostik, Differenzialdiagnosen, Therapie, Prognose, Prävention, Literatur/Einzelnachweise; je nach Artikeltyp ergänzen.
6. Bei Arzneimitteln: `article_type: pharmaka`, `risk_level: high`. Dosierungen, Interaktionen, Kontraindikationen, Schwangerschaft/Stillzeit und Nieren-/Leberanpassungen **manuell anhand aktueller Fachinformation und ergänzender Leitlinien verifizieren**. Pharmaka erfordern Apotheker- und ärztlichen Fachreview sowie Medical-Advisor-Sign-off.
7. KI-Nutzung gemäß [AI Assistance Policy](../editorial/ai-assistance-policy.md) offenlegen: `ai_assisted: true` plus `ai_assistance_description` mit Tool, betroffenen Abschnitten und menschlicher Verifikation. KI ist keine Primärquelle.
8. Lokal oder im PR die Prüfungen laufen lassen: `python3 scripts/validation/validate-metadata.py`, `python3 -m pytest -q`; zusätzlich die im Repository dokumentierten Lint-/CI-Prüfungen. Fehlermeldungen beheben.
9. Draft-Pull-Request mit präzisem Titel, Zusammenfassung, Quellen-/Leitlinienstand, Risikoeinstufung, AI-Erklärung, Interessenkonflikten, offenen Fragen und gewünschtem Fachreview öffnen. Bei Review-Reife auf „Ready for review“ stellen.
10. Review-Kommentare einzeln bearbeiten, Änderungen committen und im PR nachvollziehbar beantworten. **Kein Merge in eigener Sache.**

**Metadatenbeispiel:** Nicht blind kopieren: Das aktuelle Schema und die Vorlagen sind maßgeblich. Insbesondere `license`, `source_notes`, `next_review`, Reviewer und Sign-off werden je nach Status erst später verpflichtend.

## 6. Fachreview – Schritt für Schritt

1. Einladung prüfen: passt das Thema zur eigenen nachgewiesenen Fachkompetenz? Liegen Unabhängigkeit und keine relevanten Interessenkonflikte vor? Andernfalls zurückgeben.
2. Den vollständigen PR-Diff, den Artikel, Frontmatter und die aktuelle Quellenliste lesen. Nicht nur die Zusammenfassung.
3. **Quellenprüfung:** alle wesentlichen Aussagen belegen lassen; Leitlinienversion, Originalpublikation, Statistikjahr und deutsche Zulassung/Indikation prüfen. Quellen öffnen, nicht nur DOI/PMID-Strings kontrollieren.
4. **Klinische Prüfung:** Definitionen, Klassifikationen, Warnzeichen, Differenzialdiagnosen, Schwellenwerte, diagnostische Tests, Kontraindikationen, Dosierungen, Interaktionen, Patientengruppen und Evidenzgrade gegenprüfen.
5. **Sicherheitsprüfung:** Artikeltyp und `risk_level` korrekt? Bei Hochrisiko die separate Medical-Advisor-Freigabe anfordern; bei Pharmaka außerdem Apotheker- und fachärztlichen Review.
6. **Patientenverständlichkeit:** bei patientengerichteten Texten separate Prüfung von Lesbarkeit, Risikokommunikation und missverständlichen Handlungsanweisungen sicherstellen.
7. **Formales:** Metadaten, Referenznummern, Urheberrecht, interne Links, Datum `updated`, `next_review`, geschlechtsbezogene Unterschiede und KI-Deklaration kontrollieren.
8. GitHub-Review mit konkreten, auf Zeilen bezogenen Kommentaren abgeben: `Request changes` bei fachlichen/formalen Mängeln; `Approve` erst nach vollständiger Prüfung. Den fachlichen Sign-off gemäß [Review-Policy](../editorial/peer-review-policy.md) dokumentieren; bloßer GitHub-Klick ersetzt die qualifizierte Prüfung nicht.
9. Nach wesentlichen Änderungen erneut prüfen; der Specialty Editor kontrolliert die vollständige Review-Kette und koordiniert die Statusübergänge.

**Mindestanforderungen:** Standard-Fachartikel: 1 unabhängiger qualifizierter Reviewer; Hochrisiko: zusätzlich Medical Advisor; Patientenartikel: zusätzlich Verständlichkeitsprüfung; Arzneimittel: Apotheker + ärztlicher Fachreview + Medical Advisor. Weitere Anforderungen siehe Review-Policy.

## 7. Status und Veröffentlichung

`draft → in-review → (advisor-review bei Hochrisiko) → approved → published → archived/retracted`

- **draft:** Autor bearbeitet, nicht freigegeben.
- **in-review:** Prüfung läuft; Änderungswünsche führen ggf. zurück zu `draft`.
- **advisor-review:** zusätzliche Hochrisiko-Freigabe.
- **approved:** menschliche Freigaben und Pflichtmetadaten vollständig; noch **nicht** öffentlich.
- **published:** durch redaktionell/technisch kontrollierten Release-Tag für MediaWiki-Import vorgesehen.
- **archived/retracted:** historische oder zurückgezogene Artikel, mit entsprechendem Verfahren.

Der bestehende Prozess nutzt Pull Requests, `ci-ok`, einen freigegebenen Release-Tag `vX.Y.Z`, Backup/Healthcheck und den idempotenten Importer unter `scripts/publishing/`. **Nicht** direkt in MediaWiki veröffentlichen. Freigegebene Artikel sind gegen stillschweigende Inhaltsänderungen geschützt; spätere inhaltliche Aktualisierungen durchlaufen einen neuen Review-Zyklus. Der Go-live bleibt bis zur Erfüllung der [Checkliste](../deployment/go-live-checklist.md) gesperrt.

## 8. Fristen, Aktualisierung und Sicherheitsmeldungen

Zielzeiten laut Review-Policy: regulär 14 Kalendertage, neue Leitlinien 7 Tage, dringende Sicherheitsfragen 48 Stunden, aktive Sicherheitswarnungen 24 Stunden. Diese Zeiten sind Ziele, keine automatische Freigabe.

Spätestens jährlich fachlich überprüfen; neue Leitlinien und Sicherheitswarnungen können sofortige Neubewertung erfordern. Die automatisierte PubMed-/Leitlinienüberwachung erzeugt Hinweise und Issues, **keine ungeprüften Publikationen**.

**Bei möglicher Patientengefährdung:** sofort Editorial Board/Medical Director kontaktieren, `safety_hold`-Prozess nach Review-Policy einleiten und Veröffentlichung stoppen. Kritische Fehler nicht durch heimliche Direktbearbeitung auf dem Wiki „reparieren“.

## 9. Datenschutz, Lizenz, Transparenz

Keine echten Patientenfälle mit identifizierenden Daten; keine vertraulichen Unterlagen in öffentlichen GitHub-Dateien. Rechte an Texten, Bildern und Tabellen müssen dokumentiert sein. Repository-Code und veröffentlichte Artikel können **unterschiedliche Lizenzen** haben; vor dem Go-live ist die Artikel-Lizenzentscheidung und die rechtliche Prüfung verbindlich umzusetzen. Bis dahin keine ungeprüften Lizenzangaben in Artikeln. Siehe `LICENSE`, `docs/legal/` und Go-live-Checkliste.

## 10. Häufige Fragen

**Brauche ich Programmierkenntnisse?** Nein. Dateien und Pull Requests lassen sich über GitHub im Browser bearbeiten; die Redaktion unterstützt beim ersten Beitrag.

**Kann ich direkt auf wikimedica.de schreiben?** Nein. GitHub ist die Inhaltsquelle, MediaWiki die veröffentlichte Ansicht.

**Darf ich ChatGPT für einen Entwurf nutzen?** Nur im Rahmen der genehmigten KI-Richtlinie, mit Deklaration und menschlicher Vollprüfung. Keine generierten Quellen oder unbestätigten Dosiswerte.

**Wer entscheidet über die Veröffentlichung?** Fachreviewer und ggf. Medical Advisor liefern die fachlichen Freigaben; Specialty Editor/Editorial Board entscheiden redaktionell; DevOps veröffentlicht nur einen zulässigen Release.

**Wie melde ich einen Fehler?** Über einen GitHub-Issue oder an editorial@wikimedica.de; bei akuter Patientensicherheitsgefahr unverzüglich eskalieren.

**Wo erhalte ich Zugang?** Redaktion kontaktieren; Berechtigungen werden erst nach Qualifikationsprüfung vergeben.

## 11. Checklisten zum Abhaken

**Autor vor „Ready for review“:** [ ] Vorlage/Schema korrekt [ ] eigenes Deutsch, keine Textübernahme [ ] wesentliche Aussagen belegt [ ] Statistikjahr und Zulassungsstand [ ] Risiken/COI [ ] KI offengelegt [ ] Gender-Relevanz [ ] Patiententext falls nötig [ ] CI bestanden [ ] keine Patientendaten.

**Reviewer vor „Approve“:** [ ] unabhängig und fachlich qualifiziert [ ] Originalquellen geprüft [ ] klinische Aussagen überprüft [ ] Dosierungen/Fachinformation geprüft, falls relevant [ ] Risikoklasse korrekt [ ] zusätzliche Reviewer/Advisor eingebunden [ ] Verständlichkeit geprüft [ ] Metadaten/Referenzen korrekt [ ] alle Blocking-Kommentare erledigt [ ] Sign-off dokumentiert.

**Editor vor „approved“:** [ ] vollständige fachliche Review-Kette [ ] Interessenkonflikte geklärt [ ] Lizenz/Quellen geklärt [ ] Pflichtfelder für Status erfüllt [ ] CI grün [ ] keine Safety-Holds [ ] nächste Prüfung terminiert.

---
**Normenhierarchie:** Bei Widersprüchen gelten das maschinenlesbare Metadatenschema, die bestehende verbindliche Review-/AI-/Rollenpolicy und die Go-live-Gates; dieses Onboarding erklärt deren Anwendung, ersetzt sie aber nicht.
