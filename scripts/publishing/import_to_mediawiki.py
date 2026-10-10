#!/usr/bin/env python3
"""
import_to_mediawiki.py — publish approved Wikimedica articles from GitHub to MediaWiki.

GitHub is the single source of truth: this script turns Markdown+YAML files
into wiki pages through the MediaWiki Action API, idempotently. It contains no
AI and no manual override.

Examples
    # dry run: validates and renders everything, touches NO network
    python scripts/publishing/import_to_mediawiki.py --env staging --dry-run

    # staging import of approved articles
    python scripts/publishing/import_to_mediawiki.py --env staging --status approved

    # production: only published articles, only for a release tag that HEAD is at
    python scripts/publishing/import_to_mediawiki.py --env production --status published --release-tag v1.2.3

Safety gates (each failure = exit code 2, nothing is written)
    * only status approved/published is ever imported; draft/in-review never
    * production requires --status published AND --release-tag vX.Y.Z AND HEAD == that tag
    * production requires data/legal/disclaimers.yaml review_status == approved
    * production API URL must be https and must differ from the staging URL
    * credentials come from the environment only (WIKI_<ENV>_API_URL/_BOT_USER/_BOT_PASSWORD)
    * an article that fails validation is skipped and the run exits 1; others still import
    * a wiki page that is not managed by this script is never overwritten
    * unresolved {{ placeholders }} (= template transclusion in wikitext) are errors

Withdrawals: articles with safety_hold, or status retracted/archived, replace an
EXISTING managed page by a notice page, so unsafe content leaves the wiki.

Exit codes: 0 ok · 1 at least one article failed · 2 gate/config error · 3 wiki/API error
"""

from __future__ import annotations

import argparse
import http.cookiejar
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))

import wikipage  # noqa: E402  (needs sys.path above)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


vm = _load(REPO / "scripts" / "validation" / "validate-metadata.py", "validate_metadata")
pre = _load(HERE / "pre-publish-check.py", "pre_publish_check")

TAG_RE = re.compile(r"^v\d+\.\d+\.\d+$")
BOT_PASSWORD_RE = re.compile(r"^[0-9a-w]{32,}$")
SKIP_DIRS = {"templates"}
IMPORT_STATUSES = {"approved", "published"}
WITHDRAW_STATUSES = {"retracted", "archived"}

EXIT_OK, EXIT_ARTICLE, EXIT_GATE, EXIT_API = 0, 1, 2, 3


class GateError(Exception):
    """A safety gate or configuration problem (exit code 2)."""


class WikiError(Exception):
    """The wiki / API misbehaved (exit code 3)."""


# ---------------------------------------------------------------------------
# MediaWiki Action API client (stdlib only)
# ---------------------------------------------------------------------------

class WikiClient:
    """Minimal BotPassword client: login, read page, edit page."""

    def __init__(self, api_url: str, user: str, password: str, *, timeout: float = 30,
                 delay: float = 1.0, maxlag: int = 5, retries: int = 4):
        self.api_url, self.user, self._password = api_url, user, password
        self.timeout, self.delay, self.maxlag, self.retries = timeout, delay, maxlag, retries
        self._cookies = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self._cookies))
        self._opener.addheaders = [("User-Agent", "WikimedicaImporter/1.0 (editorial@wikimedica.de)")]
        self._csrf: str | None = None

    # -- transport ----------------------------------------------------------
    def _call(self, params: dict, *, post: bool = False) -> dict:
        params = {**params, "format": "json", "formatversion": "2"}
        if post:
            params.setdefault("maxlag", str(self.maxlag))
        data = urllib.parse.urlencode(params).encode("utf-8")
        for attempt in range(self.retries + 1):
            try:
                if post:
                    req = urllib.request.Request(self.api_url, data=data)
                else:
                    req = urllib.request.Request(self.api_url + "?" + data.decode("ascii"))
                with self._opener.open(req, timeout=self.timeout) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                if attempt == self.retries:
                    raise WikiError(f"request failed after {attempt + 1} attempts: {exc}") from exc
                time.sleep(min(2 ** attempt, 30))
                continue
            err = payload.get("error")
            if err and err.get("code") in ("maxlag", "ratelimited", "readonly") and attempt < self.retries:
                time.sleep(min(5 * (attempt + 1), 60))
                continue
            return payload
        raise WikiError("unreachable")  # pragma: no cover

    @staticmethod
    def _raise_on_error(payload: dict, what: str) -> None:
        if "error" in payload:
            err = payload["error"]
            raise WikiError(f"{what}: {err.get('code')}: {str(err.get('info', ''))[:200]}")

    # -- operations ---------------------------------------------------------
    def login(self) -> None:
        token = self._call({"action": "query", "meta": "tokens", "type": "login"})
        self._raise_on_error(token, "login token")
        result = self._call({
            "action": "login", "lgname": self.user, "lgpassword": self._password,
            "lgtoken": token["query"]["tokens"]["logintoken"],
        }, post=True)
        self._raise_on_error(result, "login")
        if result.get("login", {}).get("result") != "Success":
            raise WikiError(f"login failed: {result.get('login', {}).get('reason', 'unknown reason')}")
        self._password = ""  # not needed any more

    def _csrf_token(self, refresh: bool = False) -> str:
        if self._csrf is None or refresh:
            data = self._call({"action": "query", "meta": "tokens"})
            self._raise_on_error(data, "csrf token")
            self._csrf = data["query"]["tokens"]["csrftoken"]
        return self._csrf

    def get_page(self, title: str) -> dict | None:
        data = self._call({"action": "query", "prop": "revisions", "titles": title,
                           "rvprop": "content|ids", "rvslots": "main"})
        self._raise_on_error(data, f"read '{title}'")
        page = data["query"]["pages"][0]
        if page.get("missing") or page.get("invalid"):
            return None
        rev = page["revisions"][0]
        return {"text": rev["slots"]["main"]["content"], "revid": rev["revid"]}

    def edit(self, title: str, text: str, summary: str, *, baserevid: int | None = None,
             createonly: bool = False) -> dict:
        for attempt in range(2):
            params = {"action": "edit", "title": title, "text": text, "summary": summary,
                      "bot": "1", "token": self._csrf_token(refresh=attempt == 1),
                      "contentmodel": "wikitext"}
            if baserevid is not None:
                params["baserevid"] = str(baserevid)
            if createonly:
                params["createonly"] = "1"
            result = self._call(params, post=True)
            if result.get("error", {}).get("code") == "badtoken" and attempt == 0:
                continue
            self._raise_on_error(result, f"edit '{title}'")
            time.sleep(self.delay)
            return result["edit"]
        raise WikiError(f"edit '{title}': token rejected twice")  # pragma: no cover


# ---------------------------------------------------------------------------
# Configuration and gates
# ---------------------------------------------------------------------------

@dataclass
class Settings:
    env: str
    statuses: set[str]
    dry_run: bool
    release_tag: str | None
    content_dir: Path
    output_dir: Path
    log_file: Path
    only: set[str]
    show_names: bool
    adopt: bool
    skip_git_check: bool


def git_head_matches_tag(tag: str) -> bool:
    def rev(ref: str) -> str:
        return subprocess.run(["git", "rev-parse", "--verify", "-q", ref], cwd=REPO,
                              capture_output=True, text=True).stdout.strip()
    tag_commit, head = rev(f"{tag}^{{commit}}"), rev("HEAD")
    return bool(tag_commit) and tag_commit == head


def check_gates(args: argparse.Namespace, disclaimers: dict) -> Settings:
    env = args.env
    if args.status == "both":
        statuses = set(IMPORT_STATUSES)
    else:
        statuses = {args.status}
    if args.status is None:
        statuses = {"published"} if env == "production" else set(IMPORT_STATUSES)

    if env == "production":
        if statuses != {"published"}:
            raise GateError("production imports only status 'published' (use --status published)")
        if not args.release_tag or not TAG_RE.match(args.release_tag):
            raise GateError("production requires --release-tag vX.Y.Z (a release tag, no free-form refs)")
        if not args.dry_run and not args.skip_git_check and not git_head_matches_tag(args.release_tag):
            raise GateError(f"HEAD is not at tag {args.release_tag}; check out the release tag first")
        if disclaimers.get("review_status") != "approved":
            raise GateError("data/legal/disclaimers.yaml is not approved by the Legal Reviewer "
                            f"(review_status={disclaimers.get('review_status')!r}); production import refused")
    if args.release_tag and not TAG_RE.match(args.release_tag):
        raise GateError(f"invalid --release-tag {args.release_tag!r}")

    return Settings(
        env=env, statuses=statuses, dry_run=args.dry_run, release_tag=args.release_tag,
        content_dir=Path(args.content_dir), output_dir=Path(args.output_dir),
        log_file=Path(args.log_file or Path(args.output_dir) / "import-log.jsonl"),
        only=set(args.only or []), show_names=args.show_names, adopt=args.adopt,
        skip_git_check=args.skip_git_check,
    )


def wiki_credentials(env: str) -> tuple[str, str, str]:
    prefix = f"WIKI_{env.upper()}_"
    api, user, password = (os.environ.get(prefix + k, "") for k in ("API_URL", "BOT_USER", "BOT_PASSWORD"))
    missing = [prefix + k for k, v in (("API_URL", api), ("BOT_USER", user), ("BOT_PASSWORD", password)) if not v]
    if missing:
        raise GateError("missing environment variables: " + ", ".join(missing))
    if "@" not in user:
        raise GateError(f"{prefix}BOT_USER must have the form 'AccountName@AppId' (see Special:BotPasswords)")
    if not BOT_PASSWORD_RE.match(password):
        # MediaWiki only treats [0-9a-w]{32,} as a bot password. Anything else is silently handled as a
        # normal account password and fails with the misleading "Incorrect username or password".
        raise GateError(f"{prefix}BOT_PASSWORD is not a MediaWiki bot password: it must be the generated "
                        "token from Special:BotPasswords (at least 32 characters, only 0-9 and a-w)")
    if env == "production" and not api.startswith("https://"):
        raise GateError("production API URL must use https")
    other = os.environ.get("WIKI_STAGING_API_URL" if env == "production" else "WIKI_PRODUCTION_API_URL", "")
    if other and other.rstrip("/") == api.rstrip("/"):
        raise GateError("staging and production API URLs are identical — refusing to continue")
    return api, user, password


# ---------------------------------------------------------------------------
# Selecting and validating articles
# ---------------------------------------------------------------------------

@dataclass
class Item:
    path: Path
    slug: str
    fm: dict
    body: str
    action: str = ""            # import | withdraw | skip
    reason: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    page: wikipage.Page | None = None
    result: str = ""            # created | updated | unchanged | withdrawn | dry-run | failed | skipped


def discover(settings: Settings, schema: dict) -> list[Item]:
    items: list[Item] = []
    for path in sorted(settings.content_dir.rglob("*.md")):
        if SKIP_DIRS & set(path.relative_to(settings.content_dir).parts) or path.name.lower() == "readme.md":
            continue
        article = vm.parse_article(path)
        if article.frontmatter is None:
            continue
        item = Item(path=path, slug=path.stem, fm=article.frontmatter, body=article.body)
        if settings.only and item.slug not in settings.only:
            continue
        status = item.fm.get("status")
        if item.fm.get("safety_hold") is True and status in (IMPORT_STATUSES | WITHDRAW_STATUSES):
            item.action, item.reason = "withdraw", "safety_hold"
        elif status in WITHDRAW_STATUSES:
            item.action, item.reason = "withdraw", str(status)
        elif status in settings.statuses:
            item.action = "import"
        else:
            item.action, item.reason, item.result = "skip", f"status '{status}' is not importable", "skipped"
        if item.action != "skip":
            vm.validate_article(article, schema)
            if item.action == "import":
                item.errors += [str(f) for f in article.errors]
            else:
                # A withdrawal must never be blocked by a metadata problem: unsafe
                # content has to leave the wiki. Problems are reported as warnings.
                item.warnings += [str(f) for f in article.errors]
            item.warnings += [str(f) for f in article.warnings]
        items.append(item)
    return items


def run_prepublish(item: Item) -> None:
    if item.action != "import":
        return
    for check in (pre.check_required_sections(item.fm, item.body), pre.check_no_todo_markers(item.body)):
        if not check.passed:
            item.errors.append(f"{check.name}: {check.message}")


def render_all(items: list[Item], settings: Settings, disclaimers: dict) -> None:
    internal = {i.slug: str(i.fm.get("title", i.slug)) for i in items if i.action == "import"}
    titles: dict[str, Item] = {}
    for item in items:
        if item.action == "skip" or item.errors:
            if item.action != "skip":
                item.result = "failed"
            continue
        try:
            if item.action == "import":
                item.page = wikipage.build_article_page(
                    item.fm, item.body, slug=item.slug, disclaimers=disclaimers,
                    internal_pages=internal, show_names=settings.show_names)
            else:
                item.page = wikipage.build_withdrawal_page(
                    item.fm, slug=item.slug, reason=item.reason, disclaimers=disclaimers)
        except Exception as exc:  # a bug in one article must not stop the others
            item.errors.append(f"render error: {exc!r}")
            item.result = "failed"
            continue
        item.errors += item.page.errors
        item.warnings += item.page.warnings
        if item.errors:
            item.result = "failed"
            continue
        other = titles.get(item.page.title)
        if other and other.slug != item.slug:
            item.errors.append(f"page title '{item.page.title}' is also used by article '{other.slug}'")
            item.result = "failed"
        else:
            titles[item.page.title] = item


# ---------------------------------------------------------------------------
# Applying to the wiki
# ---------------------------------------------------------------------------

def apply_item(item: Item, client: WikiClient, settings: Settings) -> None:
    page = item.page
    assert page is not None
    existing = client.get_page(page.title)
    marker = wikipage.parse_marker(existing["text"]) if existing else None

    if existing and (not marker or marker["slug"] != page.slug):
        if item.action == "withdraw":
            item.result, item.reason = "skipped", "page exists but is not managed by this article"
            return
        if not settings.adopt:
            item.errors.append(f"page '{page.title}' exists and is not managed by '{page.slug}' "
                               "(refusing to overwrite; use --adopt for a deliberate takeover)")
            item.result = "failed"
            return
        item.warnings.append("adopted an unmanaged page")

    if item.action == "withdraw" and not existing:
        item.result = "skipped"
        item.reason += " (no page in the wiki, nothing to withdraw)"
        return

    if existing and marker and marker["sha"] == page.sha256:
        item.result = "unchanged"
        return
    if existing and marker and not wikipage.marker_is_intact(existing["text"]):
        item.warnings.append("page was edited by hand in the wiki; overwritten (GitHub is the source of truth)")

    tag = f" {settings.release_tag}" if settings.release_tag else ""
    summary = (f"Wikimedica import{tag}: {page.slug} v{page.version}" if item.action == "import"
               else f"Wikimedica withdrawal ({item.reason}): {page.slug}")
    client.edit(page.title, page.wikitext, summary,
                baserevid=existing["revid"] if existing else None, createonly=existing is None)
    item.result = ("withdrawn" if item.action == "withdraw"
                   else "updated" if existing else "created")


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def write_outputs(items: list[Item], settings: Settings, wiki_error: str | None) -> dict:
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    wt_dir = settings.output_dir / "wikitext"
    wt_dir.mkdir(exist_ok=True)
    counts: dict[str, int] = {}
    with settings.log_file.open("w", encoding="utf-8") as log:
        for it in items:
            if it.page and not it.errors:
                (wt_dir / f"{it.slug}.wiki").write_text(it.page.wikitext, encoding="utf-8")
            counts[it.result or "unknown"] = counts.get(it.result or "unknown", 0) + 1
            log.write(json.dumps({
                "slug": it.slug, "file": str(it.path), "action": it.action, "result": it.result,
                "reason": it.reason, "errors": it.errors, "warnings": it.warnings,
                "title": it.page.title if it.page else None, "sha256": it.page.sha256 if it.page else None,
                "env": settings.env, "release_tag": settings.release_tag, "dry_run": settings.dry_run,
            }, ensure_ascii=False) + "\n")

    lines = [f"## Wikimedica import — `{settings.env}`" + (" (dry run)" if settings.dry_run else ""),
             "", f"Release tag: `{settings.release_tag or '—'}`  ·  statuses: `{', '.join(sorted(settings.statuses))}`", "",
             "| Result | Count |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in sorted(counts.items())]
    failed = [i for i in items if i.result == "failed"]
    if failed:
        lines += ["", "### Failed articles", ""]
        for it in failed:
            lines.append(f"- **{it.slug}** (`{it.path}`)")
            lines += [f"  - {e}" for e in it.errors[:12]]
    warned = [i for i in items if i.warnings and i.result != "failed"]
    if warned:
        lines += ["", "<details><summary>Warnings</summary>", ""]
        for it in warned:
            lines += [f"- {it.slug}: {w}" for w in it.warnings[:6]]
        lines += ["", "</details>"]
    if wiki_error:
        lines += ["", f"### Wiki/API error\n\n`{wiki_error}`"]
    summary = "\n".join(lines) + "\n"
    (settings.output_dir / "summary.md").write_text(summary, encoding="utf-8")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write(summary)
    return counts


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Import approved Wikimedica articles into MediaWiki.")
    p.add_argument("--env", required=True, choices=["staging", "production"])
    p.add_argument("--status", choices=["approved", "published", "both"], default=None,
                   help="which statuses to import (default: staging both, production published)")
    p.add_argument("--dry-run", action="store_true", help="validate and render only; no network access")
    p.add_argument("--release-tag", help="release tag vX.Y.Z (mandatory for production)")
    p.add_argument("--content-dir", default=str(REPO / "content"))
    p.add_argument("--output-dir", default=str(REPO / "import-output"),
                   help="where rendered wikitext, log and summary are written")
    p.add_argument("--log-file", help="JSONL import log (default: <output-dir>/import-log.jsonl)")
    p.add_argument("--only", action="append", metavar="SLUG", help="import only this slug (repeatable)")
    p.add_argument("--show-names", action="store_true",
                   help="show author and reviewer names in the info box (requires their consent)")
    p.add_argument("--adopt", action="store_true", help="take over existing unmanaged pages (deliberate!)")
    p.add_argument("--schema", default=str(REPO / "data" / "metadata" / "article-schema.yaml"))
    p.add_argument("--disclaimers", default=str(REPO / "data" / "legal" / "disclaimers.yaml"))
    p.add_argument("--skip-git-check", action="store_true", help=argparse.SUPPRESS)
    return p


def main(argv: list[str] | None = None, client_factory=WikiClient) -> int:
    import yaml

    args = build_parser().parse_args(argv)
    try:
        disclaimers = yaml.safe_load(Path(args.disclaimers).read_text(encoding="utf-8"))
        settings = check_gates(args, disclaimers)
        schema = vm.load_schema(Path(args.schema))
        credentials = None if settings.dry_run else wiki_credentials(settings.env)
    except GateError as exc:
        print(f"GATE: {exc}", file=sys.stderr)
        return EXIT_GATE
    except (OSError, yaml.YAMLError) as exc:
        print(f"CONFIG: {exc}", file=sys.stderr)
        return EXIT_GATE

    if disclaimers.get("review_status") != "approved":
        print("NOTE: disclaimers are not yet approved by Legal (acceptable for staging only).", file=sys.stderr)

    items = discover(settings, schema)
    for item in items:
        run_prepublish(item)
    render_all(items, settings, disclaimers)

    wiki_error = None
    if settings.dry_run:
        for it in items:
            if it.action != "skip" and not it.errors:
                it.result = "dry-run"
    else:
        try:
            client = client_factory(*credentials)
            client.login()
            for it in items:
                if it.result or it.errors or it.page is None:
                    continue
                try:
                    apply_item(it, client, settings)
                except WikiError as exc:
                    it.errors.append(str(exc))
                    it.result = "failed"
                    wiki_error = wiki_error or str(exc)
        except WikiError as exc:
            wiki_error = str(exc)

    counts = write_outputs(items, settings, wiki_error)
    print(open(settings.output_dir / "summary.md", encoding="utf-8").read())

    if wiki_error and not any(i.result in ("created", "updated", "unchanged", "withdrawn") for i in items):
        return EXIT_API
    if counts.get("failed"):
        return EXIT_ARTICLE if not wiki_error else EXIT_API
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
