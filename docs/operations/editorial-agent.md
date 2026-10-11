# WikiMedica Editorial-Agent

Der Dienst ist ein restart-sicherer, unprivilegierter Dispatcher für die
redaktionelle Warteschlange. Er führt **keinen** Codex-, Claude-, Browser- oder
Modellprozess aus. Ohne explizit integrierten, dienstbezogen autorisierten
Recherche-Executor verbleiben Artikel im Status `planned`; es werden weder
Artikel behauptet noch BETA-Seiten veröffentlicht.

## Zustände

`planned`, `researching`, `sources-verified`, `drafted`, `validated`,
`pr-created`, `beta-publication-queued`, `live-beta-verified`,
`review-pending`, `reviewed`, `approved`, `published`, `blocked`.

`live-beta-verified` setzt eine gespeicherte, zurückgelesene MediaWiki-Revision
voraus. Ein PR oder ein Merge genügen dafür nicht.

## Bedienung

Die produktive Unit verwendet ausschließlich:

```text
systemctl start wikimedica-editorial-agent.service
systemctl status wikimedica-editorial-agent.timer
```

Administrative lokale Kommandos mit dem Dienstbenutzer:

```text
python3 scripts/editorial/wikimedica_editorial_agent.py status
python3 scripts/editorial/wikimedica_editorial_agent.py health
python3 scripts/editorial/wikimedica_editorial_agent.py pause
python3 scripts/editorial/wikimedica_editorial_agent.py resume
python3 scripts/editorial/wikimedica_editorial_agent.py stop
python3 scripts/editorial/wikimedica_editorial_agent.py dry-run
python3 scripts/editorial/wikimedica_editorial_agent.py report
python3 scripts/editorial/wikimedica_editorial_agent.py retry --article-id WM-DIS-0012
python3 scripts/editorial/wikimedica_editorial_agent.py verify-publication --article-id WM-DIS-0012
```

Der State liegt unter `/var/lib/wikimedica-editorial-agent/`, wird atomar
geschrieben und durch eine nichtblockierende Dateisperre gegen Doppelstarts
geschützt. Die Unit darf erst installiert und aktiviert werden, wenn ihr
separater Quell-Snapshot, der Dienstbenutzer und die Zielrechte eingerichtet
sind. Ein künftiger Recherche-Executor benötigt einen eigenen Dienstzugang,
harte Kosten-/Zeitlimits, Quellen- und Sicherheitsgates; er darf den
Systemzugang des Codex-CLI nicht übernehmen.
