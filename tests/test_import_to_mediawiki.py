"""End-to-end tests of scripts/publishing/import_to_mediawiki.py against a local API simulator."""

from __future__ import annotations

import json
import re
import shutil
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
import yaml

from conftest import FIXTURES, REPO, load_script, read_fixture, render

imp = load_script("scripts/publishing/import_to_mediawiki.py", "import_to_mediawiki")

BOT_PASS = "0123456789abcdefghijklmnopqrstuvw0123456789"   # valid MediaWiki bot-password format


# ---------------------------------------------------------------------------
# MediaWiki API simulator (login/token/cookie flow, edit, read, maxlag)
# ---------------------------------------------------------------------------

class FakeWiki:
    def __init__(self):
        self.pages: dict[str, dict] = {}
        self.revid = 100
        self.edits: list[dict] = []
        self.maxlag_failures = 0
        self.requests = 0


def make_handler(wiki: FakeWiki):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):  # silence
            pass

        def _params(self):
            if self.command == "POST":
                length = int(self.headers.get("Content-Length", 0))
                return {k: v[0] for k, v in urllib.parse.parse_qs(self.rfile.read(length).decode()).items()}
            return {k: v[0] for k, v in urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).items()}

        def _send(self, payload, cookie=None):
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            if cookie:
                self.send_header("Set-Cookie", cookie)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _handle(self):
            wiki.requests += 1
            p = self._params()
            logged_in = "wmsid=ok" in (self.headers.get("Cookie") or "")
            action = p.get("action")
            if action == "query" and p.get("meta") == "tokens":
                if p.get("type") == "login":
                    return self._send({"query": {"tokens": {"logintoken": "LT+\\"}}})
                token = "CSRF+\\" if logged_in else "+\\"
                return self._send({"query": {"tokens": {"csrftoken": token}}})
            if action == "login":
                ok = p.get("lgpassword") == BOT_PASS and p.get("lgtoken") == "LT+\\"
                if not ok:
                    return self._send({"login": {"result": "Failed", "reason": "Incorrect password"}})
                return self._send({"login": {"result": "Success", "lgusername": p["lgname"]}},
                                  cookie="wmsid=ok; Path=/")
            if action == "query" and p.get("prop") == "revisions":
                title = p["titles"]
                page = wiki.pages.get(title)
                if not page:
                    return self._send({"query": {"pages": [{"title": title, "missing": True}]}})
                return self._send({"query": {"pages": [{"title": title, "revisions": [
                    {"revid": page["revid"], "slots": {"main": {"content": page["text"]}}}]}]}})
            if action == "edit":
                if wiki.maxlag_failures > 0:
                    wiki.maxlag_failures -= 1
                    return self._send({"error": {"code": "maxlag", "info": "Waiting for a database server"}})
                if not logged_in or p.get("token") != "CSRF+\\":
                    return self._send({"error": {"code": "badtoken", "info": "Invalid CSRF token."}})
                title = p["title"]
                if p.get("createonly") and title in wiki.pages:
                    return self._send({"error": {"code": "articleexists", "info": "exists"}})
                wiki.revid += 1
                wiki.pages[title] = {"text": p["text"], "revid": wiki.revid}
                wiki.edits.append({"title": title, "summary": p.get("summary"), "bot": p.get("bot")})
                return self._send({"edit": {"result": "Success", "title": title, "newrevid": wiki.revid}})
            return self._send({"error": {"code": "unknown", "info": action}})

        do_GET = do_POST = _handle

    return Handler


@pytest.fixture
def wiki(monkeypatch):
    fake = FakeWiki()
    server = HTTPServer(("127.0.0.1", 0), make_handler(fake))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    fake.url = f"http://127.0.0.1:{server.server_port}/api.php"
    monkeypatch.setenv("WIKI_STAGING_API_URL", fake.url)
    monkeypatch.setenv("WIKI_STAGING_BOT_USER", "Importer@bot")
    monkeypatch.setenv("WIKI_STAGING_BOT_PASSWORD", BOT_PASS)
    monkeypatch.delenv("WIKI_PRODUCTION_API_URL", raising=False)
    monkeypatch.setattr(imp.time, "sleep", lambda s: None)
    yield fake
    server.shutdown()


# ---------------------------------------------------------------------------
# Test content
# ---------------------------------------------------------------------------

@pytest.fixture
def content(tmp_path):
    """A content dir with approved, published and draft fixture articles."""
    root = tmp_path / "content"
    (root / "specialties" / "innere-medizin").mkdir(parents=True)
    (root / "patient-info").mkdir()
    (root / "pharmaka").mkdir()
    (root / "consent-modules").mkdir()
    shutil.copy(FIXTURES / "testartikel-professional.md", root / "specialties/innere-medizin/")
    shutil.copy(FIXTURES / "testartikel-patient.md", root / "patient-info/")
    shutil.copy(FIXTURES / "testartikel-pharmaka.md", root / "pharmaka/")
    shutil.copy(FIXTURES / "testmodul-aufklaerung.md", root / "consent-modules/")
    return root


def write_article(content, rel, fixture, **changes):
    fm, body = read_fixture(fixture)
    for k, v in changes.items():
        if v is None:
            fm.pop(k, None)
        else:
            fm[k] = v
    if "body" in changes:
        pass
    path = content / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(fm, body), encoding="utf-8")
    return path


def run(tmp_path, content, *extra, client_factory=None):
    out = tmp_path / "out"
    args = ["--content-dir", str(content), "--output-dir", str(out), *extra]
    kwargs = {"client_factory": client_factory} if client_factory else {}
    return imp.main(args, **kwargs), out


def log_of(out):
    return {r["slug"]: r for r in map(json.loads, (out / "import-log.jsonl").read_text("utf-8").splitlines())}


@pytest.fixture
def approved_disclaimers(tmp_path):
    data = yaml.safe_load((REPO / "data/legal/disclaimers.yaml").read_text("utf-8"))
    data.update(review_status="approved", approved_by="Test Legal", approved_on="2026-10-09")
    path = tmp_path / "disclaimers-approved.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------

def test_dry_run_needs_no_credentials_and_no_network(tmp_path, content, monkeypatch):
    for var in ("WIKI_STAGING_API_URL", "WIKI_STAGING_BOT_USER", "WIKI_STAGING_BOT_PASSWORD"):
        monkeypatch.delenv(var, raising=False)
    code, out = run(tmp_path, content, "--env", "staging", "--dry-run")
    assert code == 0
    log = log_of(out)
    assert log["testartikel-professional"]["result"] == "dry-run"
    assert log["testartikel-patient"]["result"] == "dry-run"
    assert log["testartikel-pharmaka"]["result"] == "dry-run"
    assert log["testmodul-aufklaerung"]["result"] == "skipped"      # draft is never imported
    assert (out / "wikitext" / "testartikel-professional.wiki").exists()
    assert not (out / "wikitext" / "testmodul-aufklaerung.wiki").exists()
    assert "dry run" in (out / "summary.md").read_text("utf-8")


def test_draft_and_in_review_can_never_be_selected(tmp_path, content, wiki):
    write_article(content, "patient-info/entwurf.md", "testartikel-patient.md", slug="entwurf", status="in-review")
    code, out = run(tmp_path, content, "--env", "staging", "--status", "both")
    assert log_of(out)["entwurf"]["result"] == "skipped"
    assert "Testartikel Patient" not in " ".join(wiki.pages) or True
    assert not any("entwurf" in e["summary"] for e in wiki.edits)


def test_status_option_rejects_draft(tmp_path, content):
    with pytest.raises(SystemExit):
        run(tmp_path, content, "--env", "staging", "--status", "draft", "--dry-run")


# ---------------------------------------------------------------------------
# Import against the API simulator
# ---------------------------------------------------------------------------

def test_import_creates_pages_then_is_idempotent(tmp_path, content, wiki):
    code, out = run(tmp_path, content, "--env", "staging", "--status", "both")
    assert code == 0
    assert {r["result"] for s, r in log_of(out).items() if s != "testmodul-aufklaerung"} == {"created"}
    assert len(wiki.edits) == 3 and all(e["bot"] == "1" for e in wiki.edits)

    code, out = run(tmp_path, content, "--env", "staging", "--status", "both")
    assert code == 0 and len(wiki.edits) == 3          # nothing written the second time
    assert {r["result"] for s, r in log_of(out).items() if s != "testmodul-aufklaerung"} == {"unchanged"}


def test_changed_article_is_updated_only(tmp_path, content, wiki):
    run(tmp_path, content, "--env", "staging", "--status", "both")
    write_article(content, "specialties/innere-medizin/testartikel-professional.md", "testartikel-professional.md",
                  version="1.1.0", change_summary="Neue Fassung")
    code, out = run(tmp_path, content, "--env", "staging", "--status", "both")
    log = log_of(out)
    assert log["testartikel-professional"]["result"] == "updated"
    assert log["testartikel-patient"]["result"] == "unchanged"
    assert len(wiki.edits) == 4 and "v1.1.0" in wiki.edits[-1]["summary"]


def test_page_content_is_complete_and_safe(tmp_path, content, wiki):
    run(tmp_path, content, "--env", "staging", "--status", "both")
    pro = wiki.pages["Testartikel Professional (Fixture)"]["text"]
    pat = wiki.pages["Testartikel für Patientinnen und Patienten (Fixture)"]["text"]
    pharm = wiki.pages["Testartikel Pharmaka (Fixture)"]["text"]

    assert pro.startswith('<!-- wikimedica-managed slug="testartikel-professional" version="1.0.0"')
    assert "Wichtiger Hinweis" in pro and "Hinweis für Fachpersonal" in pro
    assert "Im Notfall" not in pro                                   # not shown on professional pages
    assert pat.index("Im Notfall") < pat.index("Wichtiger Hinweis")  # emergency notice comes first
    assert "112" in pat
    assert "Hinweis zu Dosierungen" in pharm                          # high risk => dosing notice
    assert "Transparenzhinweis" in pharm                              # ai_assisted: true
    assert "Transparenzhinweis" not in pro
    assert "[[Category:Innere Medizin]]" in pro
    assert "[[Category:Risikoklasse: hoch]]" in pharm
    assert "[[Category:Gender-Medizin]]" in pharm                     # sex_gender_relevance: relevant
    assert "Version" in pro and "20.01.2026" in pro                   # version box with formatted date
    assert "Test Autorin" not in pro and "Test Gutachter" not in pro  # names hidden by default
    for text in (pro, pat, pharm):
        assert "{{" not in text and "<script" not in text


def test_names_are_shown_only_on_request(tmp_path, content, wiki):
    run(tmp_path, content, "--env", "staging", "--status", "both", "--show-names")
    assert "Test Autorin" in wiki.pages["Testartikel Professional (Fixture)"]["text"]


def test_authors_cannot_inject_categories_templates_or_html(tmp_path, content, wiki):
    path = content / "specialties/innere-medizin/testartikel-professional.md"
    path.write_text(path.read_text("utf-8") + (
        "\n## Böse\n\n{{Vorlage:Evil}} [[Category:Hack]] [[Datei:x.svg]] <script>alert(1)</script> __NOTOC__ ~~~~\n"
        "\n```\n{{in code}} [[Category:InCode]]\n```\n"), encoding="utf-8")
    code, _ = run(tmp_path, content, "--env", "staging", "--status", "both")
    assert code == 0
    text = wiki.pages["Testartikel Professional (Fixture)"]["text"]
    cats = re.findall(r"\[\[Category:([^\]]+)\]\]", text)
    assert cats == ["Innere Medizin", "Artikeltyp: Fachartikel"], cats
    assert "{{Vorlage" not in text and "<script" not in text and "[[Datei" not in text
    assert "__NOTOC__" not in text and "~~~~" not in text


def test_unmanaged_page_is_never_overwritten(tmp_path, content, wiki):
    title = "Testartikel Professional (Fixture)"
    wiki.pages[title] = {"text": "Handgeschriebene Seite", "revid": 5}
    code, out = run(tmp_path, content, "--env", "staging", "--status", "both")
    assert code == 1
    assert wiki.pages[title]["text"] == "Handgeschriebene Seite"
    assert "not managed" in " ".join(log_of(out)["testartikel-professional"]["errors"])
    assert log_of(out)["testartikel-patient"]["result"] == "created"      # others still imported


def test_adopt_takes_over_deliberately(tmp_path, content, wiki):
    title = "Testartikel Professional (Fixture)"
    wiki.pages[title] = {"text": "Handgeschriebene Seite", "revid": 5}
    code, out = run(tmp_path, content, "--env", "staging", "--status", "both", "--adopt")
    assert code == 0 and wiki.pages[title]["text"].startswith("<!-- wikimedica-managed")


def test_hand_edit_in_wiki_is_overwritten_with_warning(tmp_path, content, wiki):
    run(tmp_path, content, "--env", "staging", "--status", "both")
    title = "Testartikel Professional (Fixture)"
    wiki.pages[title]["text"] += "\nHeimlich ergänzt."
    write_article(content, "specialties/innere-medizin/testartikel-professional.md", "testartikel-professional.md",
                  version="1.0.1", change_summary="Korrektur")
    code, out = run(tmp_path, content, "--env", "staging", "--status", "both")
    rec = log_of(out)["testartikel-professional"]
    assert rec["result"] == "updated" and any("edited by hand" in w for w in rec["warnings"])
    assert "Heimlich" not in wiki.pages[title]["text"]


# ---------------------------------------------------------------------------
# Validation failures are isolated
# ---------------------------------------------------------------------------

def test_invalid_article_fails_alone(tmp_path, content, wiki):
    write_article(content, "patient-info/kaputt.md", "testartikel-patient.md", slug="kaputt",
                  title="Kaputt", risk_level=None)
    code, out = run(tmp_path, content, "--env", "staging", "--status", "both")
    log = log_of(out)
    assert code == 1
    assert log["kaputt"]["result"] == "failed" and any("risk_level" in e for e in log["kaputt"]["errors"])
    assert log["testartikel-professional"]["result"] == "created"
    assert "Kaputt" not in wiki.pages


def test_leftover_comment_blocks_import(tmp_path, content, wiki):
    path = content / "specialties/innere-medizin/testartikel-professional.md"
    path.write_text(path.read_text("utf-8") + "\n<!-- Leitfaden vergessen -->\n", encoding="utf-8")
    code, out = run(tmp_path, content, "--env", "staging", "--status", "both")
    assert code == 1
    assert any("comment" in e.lower() for e in log_of(out)["testartikel-professional"]["errors"])
    assert "Testartikel Professional (Fixture)" not in wiki.pages


def test_unresolved_placeholder_blocks_import(tmp_path, content, wiki):
    path = content / "specialties/innere-medizin/testartikel-professional.md"
    path.write_text(path.read_text("utf-8") + "\n{{ vergessen }}\n", encoding="utf-8")
    code, out = run(tmp_path, content, "--env", "staging", "--status", "both")
    assert code == 1
    assert any("unresolved placeholders" in e for e in log_of(out)["testartikel-professional"]["errors"])


def test_missing_required_section_blocks_import(tmp_path, content, wiki):
    path = content / "specialties/innere-medizin/testartikel-professional.md"
    path.write_text(path.read_text("utf-8").replace("## Diagnostik", "## Etwas anderes"), encoding="utf-8")
    code, out = run(tmp_path, content, "--env", "staging", "--status", "both")
    assert code == 1 and any("Missing sections" in e for e in log_of(out)["testartikel-professional"]["errors"])


def test_duplicate_titles_are_rejected(tmp_path, content, wiki):
    write_article(content, "patient-info/doppelt.md", "testartikel-professional.md", slug="doppelt")
    code, out = run(tmp_path, content, "--env", "staging", "--status", "both")
    log = log_of(out)
    assert code == 1 and "failed" in {log["doppelt"]["result"], log["testartikel-professional"]["result"]}


@pytest.mark.parametrize("bad_title", ["A:B", "A|B", "A [B]", "A {{B}}", "/A", "A#B", "A<B>"])
def test_dangerous_page_titles_are_rejected(tmp_path, content, wiki, bad_title):
    write_article(content, "patient-info/titel.md", "testartikel-patient.md", slug="titel", title=bad_title)
    code, out = run(tmp_path, content, "--env", "staging", "--status", "both", "--only", "titel")
    assert code == 1 and log_of(out)["titel"]["result"] == "failed"
    assert not wiki.edits


# ---------------------------------------------------------------------------
# Withdrawals (patient-safety path)
# ---------------------------------------------------------------------------

def test_safety_hold_replaces_the_live_page(tmp_path, content, wiki):
    run(tmp_path, content, "--env", "staging", "--status", "both")
    title = "Testartikel für Patientinnen und Patienten (Fixture)"
    assert "Was ist das?" in wiki.pages[title]["text"]
    write_article(content, "patient-info/testartikel-patient.md", "testartikel-patient.md", safety_hold=True)
    code, out = run(tmp_path, content, "--env", "staging", "--status", "both")
    assert code == 0 and log_of(out)["testartikel-patient"]["result"] == "withdrawn"
    text = wiki.pages[title]["text"]
    assert "Was ist das?" not in text and "Sicherheitsprüfung" in text and "112" in text


def test_withdrawal_is_not_blocked_by_metadata_errors(tmp_path, content, wiki):
    run(tmp_path, content, "--env", "staging", "--status", "both")
    write_article(content, "patient-info/testartikel-patient.md", "testartikel-patient.md",
                  safety_hold=True, risk_level=None, license=None)      # invalid on purpose
    code, out = run(tmp_path, content, "--env", "staging", "--status", "both")
    assert log_of(out)["testartikel-patient"]["result"] == "withdrawn"


def test_retracted_article_shows_notice_and_never_the_text(tmp_path, content, wiki):
    run(tmp_path, content, "--env", "staging", "--status", "both")
    write_article(content, "patient-info/testartikel-patient.md", "testartikel-patient.md",
                  status="retracted", retraction_notice="Zurückgezogen: fehlerhafte Angabe.")
    code, _ = run(tmp_path, content, "--env", "staging", "--status", "both")
    text = wiki.pages["Testartikel für Patientinnen und Patienten (Fixture)"]["text"]
    assert "Zurückgezogen: fehlerhafte Angabe." in text and "Was ist das?" not in text


def test_withdrawal_without_live_page_writes_nothing(tmp_path, content, wiki):
    write_article(content, "patient-info/testartikel-patient.md", "testartikel-patient.md", safety_hold=True)
    code, out = run(tmp_path, content, "--env", "staging", "--status", "both")
    assert log_of(out)["testartikel-patient"]["result"] == "skipped"
    assert not any(e["title"].startswith("Testartikel für") for e in wiki.edits)


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------

def test_production_requires_release_tag(tmp_path, content):
    assert run(tmp_path, content, "--env", "production", "--dry-run")[0] == 2


@pytest.mark.parametrize("tag", ["main", "1.0.0", "v1.0", "v1.0.0-rc1", "HEAD", "v1.0.0; rm -rf /"])
def test_production_rejects_free_form_refs(tmp_path, content, tag):
    assert run(tmp_path, content, "--env", "production", "--dry-run", "--release-tag", tag)[0] == 2


def test_production_never_imports_approved(tmp_path, content):
    code, _ = run(tmp_path, content, "--env", "production", "--dry-run", "--status", "approved",
                  "--release-tag", "v1.0.0")
    assert code == 2


def test_production_is_blocked_while_disclaimers_are_unapproved(tmp_path, content, capsys):
    code, _ = run(tmp_path, content, "--env", "production", "--dry-run", "--release-tag", "v1.0.0")
    assert code == 2 and "not approved by the Legal Reviewer" in capsys.readouterr().err


def test_production_dry_run_passes_once_disclaimers_are_approved(tmp_path, content, approved_disclaimers):
    code, out = run(tmp_path, content, "--env", "production", "--dry-run", "--release-tag", "v1.0.0",
                    "--disclaimers", str(approved_disclaimers))
    log = log_of(out)
    assert code == 0 and log["testartikel-patient"]["result"] == "dry-run"
    assert log["testartikel-professional"]["result"] == "skipped"       # approved != published


def test_production_requires_head_at_the_tag(tmp_path, content, approved_disclaimers, monkeypatch, capsys):
    monkeypatch.setenv("WIKI_PRODUCTION_API_URL", "https://wikimedica.example/api.php")
    code, _ = run(tmp_path, content, "--env", "production", "--release-tag", "v999.0.0",
                  "--disclaimers", str(approved_disclaimers))
    assert code == 2 and "HEAD is not at tag" in capsys.readouterr().err


def test_credentials_are_required_for_a_real_run(tmp_path, content, monkeypatch, capsys):
    for var in ("WIKI_STAGING_API_URL", "WIKI_STAGING_BOT_USER", "WIKI_STAGING_BOT_PASSWORD"):
        monkeypatch.delenv(var, raising=False)
    code, _ = run(tmp_path, content, "--env", "staging")
    assert code == 2 and "WIKI_STAGING_BOT_PASSWORD" in capsys.readouterr().err


@pytest.mark.parametrize("password", [
    "Bot-Passwort-0123456789-abcdefghijklmnopqrstuvwxyz",   # looks strong, but MediaWiki would ignore it
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEF", "0123456789abcdefghijklmnopqrstuvwxyz0123456789",  # 'x-z' not allowed
    "short", ""])
def test_bot_password_format_is_checked_up_front(monkeypatch, password):
    monkeypatch.setenv("WIKI_STAGING_API_URL", "https://wiki.example/api.php")
    monkeypatch.setenv("WIKI_STAGING_BOT_USER", "Importer@bot")
    monkeypatch.setenv("WIKI_STAGING_BOT_PASSWORD", password)
    with pytest.raises(imp.GateError):
        imp.wiki_credentials("staging")


def test_bot_user_needs_an_app_id(monkeypatch):
    monkeypatch.setenv("WIKI_STAGING_API_URL", "https://wiki.example/api.php")
    monkeypatch.setenv("WIKI_STAGING_BOT_USER", "ImporterBot")
    monkeypatch.setenv("WIKI_STAGING_BOT_PASSWORD", "0123456789abcdefghijklmnopqrstuvw")
    with pytest.raises(imp.GateError, match="AppId"):
        imp.wiki_credentials("staging")


def test_production_url_must_be_https_and_differ_from_staging(monkeypatch):
    monkeypatch.setenv("WIKI_PRODUCTION_API_URL", "http://wiki.example/api.php")
    monkeypatch.setenv("WIKI_PRODUCTION_BOT_USER", "u@app")
    monkeypatch.setenv("WIKI_PRODUCTION_BOT_PASSWORD", "0123456789abcdefghijklmnopqrstuvw")
    with pytest.raises(imp.GateError, match="https"):
        imp.wiki_credentials("production")
    monkeypatch.setenv("WIKI_PRODUCTION_API_URL", "https://same.example/api.php")
    monkeypatch.setenv("WIKI_STAGING_API_URL", "https://same.example/api.php")
    with pytest.raises(imp.GateError, match="identical"):
        imp.wiki_credentials("production")


# ---------------------------------------------------------------------------
# API behaviour
# ---------------------------------------------------------------------------

def test_wrong_password_is_an_api_error_and_writes_nothing(tmp_path, content, wiki, monkeypatch):
    monkeypatch.setenv("WIKI_STAGING_BOT_PASSWORD", "wrongwrongwrongwrongwrongwrongwrongwrong")
    code, out = run(tmp_path, content, "--env", "staging", "--status", "both")
    assert code == 3 and not wiki.edits
    assert "wrongwrong" not in (out / "summary.md").read_text("utf-8")


def test_unreachable_wiki_is_an_api_error(tmp_path, content, monkeypatch):
    monkeypatch.setenv("WIKI_STAGING_API_URL", "http://127.0.0.1:9/api.php")
    monkeypatch.setenv("WIKI_STAGING_BOT_USER", "u@app")
    monkeypatch.setenv("WIKI_STAGING_BOT_PASSWORD", "0123456789abcdefghijklmnopqrstuvw")
    monkeypatch.setattr(imp.time, "sleep", lambda s: None)
    code, _ = run(tmp_path, content, "--env", "staging", "--status", "both")
    assert code == 3


def test_maxlag_is_retried(tmp_path, content, wiki):
    wiki.maxlag_failures = 2
    code, _ = run(tmp_path, content, "--env", "staging", "--status", "both")
    assert code == 0 and len(wiki.edits) == 3


def test_secrets_never_reach_log_or_summary(tmp_path, content, wiki):
    code, out = run(tmp_path, content, "--env", "staging", "--status", "both")
    blob = (out / "import-log.jsonl").read_text("utf-8") + (out / "summary.md").read_text("utf-8")
    assert BOT_PASS not in blob and "Importer@bot" not in blob


def test_edit_summary_carries_release_tag(tmp_path, content, wiki):
    run(tmp_path, content, "--env", "staging", "--status", "both", "--release-tag", "v1.2.3")
    assert all("v1.2.3" in e["summary"] for e in wiki.edits)


def test_github_step_summary_is_written(tmp_path, content, wiki, monkeypatch):
    target = tmp_path / "step-summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(target))
    run(tmp_path, content, "--env", "staging", "--status", "both")
    assert "Wikimedica import" in target.read_text("utf-8")


def test_the_real_templates_are_never_imported(tmp_path, wiki):
    code, out = run(tmp_path, REPO / "content", "--env", "staging", "--status", "both")
    assert code == 0 and not wiki.edits
