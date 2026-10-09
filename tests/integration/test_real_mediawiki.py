"""
Integration test against a REAL MediaWiki (not a simulator).

Boots MediaWiki 1.43 (tarball pinned by SHA-256) with SQLite and the PHP built-in
server, loads the repository's infra/mediawiki/LocalSettings.example.php, creates one
account per role and then proves:

  * the example configuration actually loads on MediaWiki 1.43
  * the role/permission model behaves as docs/editorial/roles-and-permissions.md promises
  * the importer works end-to-end through a real bot-password login
  * the real parser renders the pages without transcluding templates
  * core Parsoid serves VisualEditor without an external service

It was written because simulators and syntax checks missed real defects
(TemplateStyles not bundled, custom right missing from the bot grants, bot password
format). Opt-in, needs network access and ~300 MB:

    WM_REAL_MW=1 python -m pytest tests/integration -v

Set WM_MW_CACHE to a directory to keep the downloaded tarball between runs.
"""

from __future__ import annotations

import hashlib
import http.cookiejar
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from conftest import FIXTURES, REPO, load_script  # noqa: E402

MW_VERSION = "1.43.11"
MW_SHA256 = "86a5b8e2fb7ca10228d66c8b2659a0a692958e5c520fd023c78bd713a68142f0"
MW_URL = f"https://releases.wikimedia.org/mediawiki/1.43/mediawiki-{MW_VERSION}.tar.gz"
ADMIN_PASS = "Test-Admin-Pass-12345"

pytestmark = pytest.mark.skipif(os.environ.get("WM_REAL_MW") != "1",
                                reason="opt-in: set WM_REAL_MW=1 (downloads MediaWiki)")

imp = load_script("scripts/publishing/import_to_mediawiki.py", "import_to_mediawiki")


# ---------------------------------------------------------------------------
# A running MediaWiki
# ---------------------------------------------------------------------------

class Wiki:
    def __init__(self, root: Path, data: Path, port: int, bot_password: str):
        self.root, self.data, self.port, self.bot_password = root, data, port, bot_password
        self.base = f"http://127.0.0.1:{port}"
        self.api = f"{self.base}/api.php"

    def php(self, *args: str, stdin: str | None = None) -> str:
        result = subprocess.run(["php", "maintenance/run.php", *args], cwd=self.root, input=stdin,
                                capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            raise RuntimeError(f"php maintenance/run.php {' '.join(args)} failed:\n{result.stdout}\n{result.stderr}")
        return result.stdout

    def session(self) -> "Session":
        return Session(self.api)


class Session:
    def __init__(self, api: str):
        self.api = api
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def call(self, post: bool = False, **params) -> dict:
        params.update(format="json", formatversion="2")
        data = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(self.api, data=data) if post else urllib.request.Request(f"{self.api}?{data.decode()}")
        return json.loads(self.opener.open(req, timeout=60).read())

    def login(self, user: str, password: str) -> "Session":
        token = self.call(action="query", meta="tokens", type="login")["query"]["tokens"]["logintoken"]
        result = self.call(True, action="login", lgname=user, lgpassword=password, lgtoken=token)
        assert result["login"]["result"] == "Success", (user, result)
        return self

    def edit(self, title: str, text: str = "x") -> str:
        token = self.call(action="query", meta="tokens")["query"]["tokens"]["csrftoken"]
        result = self.call(True, action="edit", title=title, text=text, token=token, summary="integration test")
        return "ok" if result.get("edit", {}).get("result") == "Success" else result.get("error", {}).get("code", str(result))

    def rights(self) -> set[str]:
        return set(self.call(action="query", meta="userinfo", uiprop="rights")["query"]["userinfo"]["rights"])

    def groups_of(self, user: str) -> list[str]:
        return self.call(action="query", list="users", ususers=user, usprop="groups")["query"]["users"][0].get("groups", [])


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _download(dest: Path) -> None:
    if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest() == MW_SHA256:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(MW_URL, timeout=300) as resp:
        dest.write_bytes(resp.read())
    digest = hashlib.sha256(dest.read_bytes()).hexdigest()
    assert digest == MW_SHA256, f"tarball checksum mismatch: {digest}"


@pytest.fixture(scope="module")
def wiki(tmp_path_factory):
    work = tmp_path_factory.mktemp("realmw")
    cache = Path(os.environ.get("WM_MW_CACHE", work / "cache"))
    tarball = cache / f"mediawiki-{MW_VERSION}.tar.gz"
    _download(tarball)

    root, data = work / "mw", work / "data"
    root.mkdir()
    data.mkdir()
    with tarfile.open(tarball) as tar:
        tar.extractall(root, filter="data")
    top = next(root.iterdir())
    for item in top.iterdir():
        shutil.move(str(item), root / item.name)
    top.rmdir()

    port = _free_port()
    bot_password = "".join(secrets.choice("0123456789abcdefghijklmnopqrstuvw") for _ in range(40))
    w = Wiki(root, data, port, bot_password)

    w.php("install", "--dbtype", "sqlite", "--dbpath", str(data), "--dbname", "wikimedica",
          "--server", w.base, "--scriptpath", "", "--lang", "de", "--pass", ADMIN_PASS,
          "--skins", "Vector,MinervaNeue", "Wikimedica", "Admin")
    (root / "LocalSettings.php").rename(root / "LocalSettings.generated.php")
    (root / "LocalSettings.php").write_text(f"""<?php
require __DIR__ . '/LocalSettings.generated.php';
$keep = [];
foreach (['wgServer','wgDBtype','wgDBserver','wgDBname','wgDBuser','wgDBpassword','wgDBprefix',
          'wgDBTableOptions','wgSQLiteDataDir','wgSecretKey','wgUpgradeKey','wgScriptPath'] as $v) {{
    $keep[$v] = $GLOBALS[$v] ?? null;
}}
require {json.dumps(str(REPO / "infra/mediawiki/LocalSettings.example.php"))};
foreach ($keep as $k => $v) {{ $GLOBALS[$k] = $v; }}
$wgUploadDirectory = __DIR__ . '/images';
""", encoding="utf-8")
    w.php("update", "--quick")

    for name, group, password in [("ImporterBot", "importbot", "Bot-Konto-Passwort-12345-abc"),
                                  ("RedakteurIn", "wm-editor", "Redaktion-Passwort-12345"),
                                  ("PlainUser", None, "Plain-Passwort-12345-abc")]:
        args = ["createAndPromote", *(["--custom-groups", group] if group else []), name, password]
        w.php(*args)
    w.php("createAndPromote", "--bureaucrat", "Buero", "Buero-Passwort-12345-abc")
    w.php("createBotPassword", "ImporterBot", bot_password, "--appid", "wmimport",
          "--grants", "basic,highvolume,editpage,createeditmovepage")

    # E-mail confirmation is required to edit (policy); confirm the test accounts the supported way.
    script = work / "confirm.php"
    script.write_text(f"""<?php
require_once {json.dumps(str(root / "maintenance/Maintenance.php"))};
class ConfirmMails extends Maintenance {{
  public function execute() {{
    foreach (['Admin','ImporterBot','RedakteurIn','PlainUser','Buero'] as $n) {{
      $u = MediaWiki\\User\\User::newFromName($n);
      $u->setEmail(strtolower($n) . '@example.org'); $u->confirmEmail(); $u->saveSettings();
    }}
  }}
}}
$maintClass = ConfirmMails::class;
require_once RUN_MAINTENANCE_IF_MAIN;
""", encoding="utf-8")
    w.php(str(script))

    server = subprocess.Popen(["php", "-S", f"127.0.0.1:{port}", "-t", str(root)],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(w.api + "?action=query&meta=siteinfo&format=json", timeout=2)
                break
            except (urllib.error.URLError, OSError):
                time.sleep(0.5)
        else:
            raise RuntimeError("MediaWiki did not start")
        yield w
    finally:
        server.terminate()
        server.wait(timeout=10)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_runs_the_pinned_lts_version(wiki):
    info = wiki.session().call(action="query", meta="siteinfo")["query"]["general"]
    assert info["generator"] == f"MediaWiki {MW_VERSION}"
    assert info["lang"] == "de"


def test_configured_extensions_are_loaded(wiki):
    names = {e["name"] for e in wiki.session().call(action="query", meta="siteinfo", siprop="extensions")["query"]["extensions"]}
    assert {"VisualEditor", "WikiEditor", "Cite", "ParserFunctions", "CategoryTree",
            "SyntaxHighlight", "Echo", "TitleBlacklist", "ConfirmEdit"} <= names
    assert "TemplateStyles" not in names   # not bundled in 1.43; loading it is a fatal error


def test_core_parsoid_needs_no_external_service(wiki):
    with urllib.request.urlopen(f"{wiki.base}/rest.php/v1/page/Hauptseite/html", timeout=30) as resp:
        body = resp.read().decode()
    assert resp.status == 200 and ('typeof="mw:' in body or "data-mw" in body)


def test_permission_model(wiki):
    forbidden = {"permissiondenied", "protectednamespace", "noedit", "noedit-anon", "readapidenied"}
    anon = wiki.session()
    plain = wiki.session().login("PlainUser", "Plain-Passwort-12345-abc")
    editor = wiki.session().login("RedakteurIn", "Redaktion-Passwort-12345")
    bureau = wiki.session().login("Buero", "Buero-Passwort-12345-abc")
    bot = wiki.session().login("ImporterBot@wmimport", wiki.bot_password)

    assert anon.edit("Anon-Test") in forbidden
    assert "createaccount" not in anon.rights()
    assert plain.edit("Plain-Test") in forbidden and plain.edit("Diskussion:Plain-Test") in forbidden
    assert "upload" not in plain.rights()

    admin = wiki.session().login("Admin", ADMIN_PASS)
    assert admin.edit("Admin-Test-Hauptnamensraum", "Inhalt") == "ok"            # sysop must keep working rights
    assert admin.edit("Kategorie:Admin-Test", "Inhalt") == "ok"
    assert editor.edit("Diskussion:Redaktion-Test", "Feedback") == "ok"          # talk pages: allowed
    for protected in ("Redaktions-Hauptseite", "Vorlage:Evil", "Kategorie:Evil", "Hilfe:Evil"):
        assert editor.edit(protected) in forbidden, protected                    # content namespaces: denied
    assert "upload" not in editor.rights()

    assert "userrights" not in bureau.rights()
    token = bureau.call(action="query", meta="tokens", type="userrights")["query"]["tokens"]["userrightstoken"]
    bureau.call(True, action="userrights", user="PlainUser", add="sysop|bureaucrat", token=token)
    assert not {"sysop", "bureaucrat"} & set(bureau.groups_of("PlainUser"))     # silently dropped
    bureau.call(True, action="userrights", user="PlainUser", add="wm-uploader", token=token)
    assert "wm-uploader" in bureau.groups_of("PlainUser")
    bureau.call(True, action="userrights", user="PlainUser", remove="wm-uploader", token=token)
    assert "wm-uploader" not in bureau.groups_of("PlainUser")

    assert "wm-edit-content" in bot.rights()                                     # needs the grant mapping
    assert bot.edit("Bot-Testseite", "Inhalt") == "ok"
    assert "upload" not in bot.rights()


def test_a_non_mediawiki_bot_password_fails_misleadingly(wiki):
    """Documents WHY the importer checks the format up front."""
    s = wiki.session()
    token = s.call(action="query", meta="tokens", type="login")["query"]["tokens"]["logintoken"]
    result = s.call(True, action="login", lgname="ImporterBot@wmimport", lgtoken=token,
                    lgpassword="Bot-Passwort-0123456789-abcdefghijklmnopqrstuvwxyz")
    assert result["login"]["result"] == "Failed" and "Incorrect username or password" in result["login"]["reason"]


# -- system pages (bootstrap) ---------------------------------------------------

@pytest.fixture(scope="module")
def bootstrapped(wiki):
    """Run infra/deploy/bootstrap-wiki.sh against the test wiki (edit.php, no API credentials)."""
    env = {**os.environ, "EDIT_CMD": "php maintenance/run.php edit"}
    result = subprocess.run(["bash", str(REPO / "infra/deploy/bootstrap-wiki.sh"), "--env", "staging"],
                            cwd=wiki.root, env=env, capture_output=True, text=True, timeout=600)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def page_text(wiki, title):
    pages = wiki.session().call(action="query", prop="revisions", titles=title, rvprop="content",
                                rvslots="main")["query"]["pages"][0]
    return None if pages.get("missing") else pages["revisions"][0]["slots"]["main"]["content"]


def test_bootstrap_creates_all_system_pages(wiki, bootstrapped):
    assert "bootstrap complete" in bootstrapped
    for title in ("Category:Gender-Medizin", "Category:Endokrinologie/Diabetologie", "Category:Risikoklasse: hoch",
                  "MediaWiki:Common.css", "Wikimedica:Haftungsausschluss", "Wikimedica:Impressum", "Hauptseite"):
        assert page_text(wiki, title), title
    assert "Im Notfall" in page_text(wiki, "Hauptseite")


def test_footer_links_and_css_are_served(wiki, bootstrapped):
    with urllib.request.urlopen(f"{wiki.base}/index.php?title=Hauptseite", timeout=30) as resp:
        html = resp.read().decode()
    for target in ("Wikimedica:Impressum", "Wikimedica:Datenschutz", "Wikimedica:Haftungsausschluss"):
        assert target in html, target
    css_url = f"{wiki.base}/load.php?lang=de&modules=site.styles&only=styles&skin=vector-2022"
    with urllib.request.urlopen(css_url, timeout=30) as resp:
        assert ".wm-notice" in resp.read().decode()


def test_disclaimer_page_is_generated_from_the_approved_source(wiki, bootstrapped):
    import yaml
    data = yaml.safe_load((REPO / "data/legal/disclaimers.yaml").read_text("utf-8"))
    text = page_text(wiki, "Wikimedica:Haftungsausschluss")
    assert data["blocks"]["emergency"]["text"].split(".")[0] in text and "116 117" in text


def test_bootstrap_is_idempotent(wiki, bootstrapped):
    env = {**os.environ, "EDIT_CMD": "php maintenance/run.php edit"}
    again = subprocess.run(["bash", str(REPO / "infra/deploy/bootstrap-wiki.sh"), "--env", "staging"],
                           cwd=wiki.root, env=env, capture_output=True, text=True, timeout=600)
    assert again.returncode == 0


def test_bootstrap_for_production_is_refused_until_legal_has_approved(wiki):
    env = {**os.environ, "EDIT_CMD": "false"}          # would fail loudly if it were ever reached
    result = subprocess.run(["bash", str(REPO / "infra/deploy/bootstrap-wiki.sh"), "--env", "production"],
                            cwd=wiki.root, env=env, capture_output=True, text=True)
    assert result.returncode != 0 and "GATE" in result.stderr


# -- importer end to end ------------------------------------------------------

@pytest.fixture
def content(tmp_path):
    root = tmp_path / "content"
    for sub, name in [("specialties/innere-medizin", "testartikel-professional.md"), ("patient-info", "testartikel-patient.md"),
                      ("pharmaka", "testartikel-pharmaka.md"), ("consent-modules", "testmodul-aufklaerung.md")]:
        (root / sub).mkdir(parents=True)
        shutil.copy(FIXTURES / name, root / sub / name)
    return root


def run_import(wiki, content, out, monkeypatch, *extra):
    monkeypatch.setenv("WIKI_STAGING_API_URL", wiki.api)
    monkeypatch.setenv("WIKI_STAGING_BOT_USER", "ImporterBot@wmimport")
    monkeypatch.setenv("WIKI_STAGING_BOT_PASSWORD", wiki.bot_password)
    return imp.main(["--env", "staging", "--status", "both", "--content-dir", str(content),
                     "--output-dir", str(out), *extra])


def parse(wiki, title):
    return wiki.session().call(action="parse", page=title, prop="text|categories|templates|sections|parsewarnings")["parse"]


PRO = "Testartikel Professional (Fixture)"
PAT = "Testartikel für Patientinnen und Patienten (Fixture)"
PHA = "Testartikel Pharmaka (Fixture)"


def test_import_end_to_end_and_idempotent(wiki, content, tmp_path, monkeypatch):
    assert run_import(wiki, content, tmp_path / "o1", monkeypatch) == 0
    first = [json.loads(l)["result"] for l in (tmp_path / "o1/import-log.jsonl").read_text().splitlines()]
    assert sorted(first) == ["created", "created", "created", "skipped"] or "unchanged" in first   # created now or earlier

    assert run_import(wiki, content, tmp_path / "o2", monkeypatch) == 0
    second = {json.loads(l)["slug"]: json.loads(l)["result"] for l in (tmp_path / "o2/import-log.jsonl").read_text().splitlines()}
    assert second["testartikel-professional"] == second["testartikel-patient"] == second["testartikel-pharmaka"] == "unchanged"


def test_real_parser_output_is_safe_and_complete(wiki, bootstrapped, content, tmp_path, monkeypatch):
    run_import(wiki, content, tmp_path / "o", monkeypatch)
    for title in (PRO, PAT, PHA):
        p = parse(wiki, title)
        assert p["templates"] == [], title                       # nothing transcluded
        assert 'class="new"' not in p["text"], f"red link on {title} (missing category page?)"
        assert "<script" not in p["text"] and not p["parsewarnings"]
    assert {c["category"] for c in parse(wiki, PRO)["categories"]} == {"Innere_Medizin", "Artikeltyp:_Fachartikel"}
    assert "Gender-Medizin" in {c["category"] for c in parse(wiki, PHA)["categories"]}
    pat = parse(wiki, PAT)["text"]
    assert pat.index("Im Notfall") < pat.index("Wichtiger Hinweis") and "112" in pat
    assert "Hinweis zu Dosierungen" in parse(wiki, PHA)["text"]


def test_hostile_markdown_cannot_reach_the_wiki(wiki, content, tmp_path, monkeypatch):
    path = content / "specialties/innere-medizin/testartikel-professional.md"
    path.write_text(path.read_text("utf-8") + "\n## Böse\n\n{{Vorlage:Evil}} [[Category:Hack]] <script>alert(1)</script> __NOTOC__\n", "utf-8")
    run_import(wiki, content, tmp_path / "o", monkeypatch)
    p = parse(wiki, PRO)
    assert p["templates"] == [] and "<script" not in p["text"]
    assert "Hack" not in {c["category"] for c in p["categories"]}


def test_safety_hold_removes_content_from_the_live_wiki(wiki, content, tmp_path, monkeypatch):
    run_import(wiki, content, tmp_path / "o1", monkeypatch)
    assert "Was ist das?" in [s["line"] for s in parse(wiki, PAT)["sections"]]
    path = content / "patient-info/testartikel-patient.md"
    path.write_text(path.read_text("utf-8").replace("safety_hold: false", "safety_hold: true"), "utf-8")
    assert run_import(wiki, content, tmp_path / "o2", monkeypatch) == 0
    p = parse(wiki, PAT)
    assert "Sicherheitsprüfung" in p["text"] and "Was ist das?" not in [s["line"] for s in p["sections"]]
    assert "112" in p["text"]


def test_unmanaged_page_is_protected_on_the_real_wiki(wiki, content, tmp_path, monkeypatch):
    admin = wiki.session().login("Admin", ADMIN_PASS)
    assert admin.edit(PRO, "Handgeschriebene Seite") == "ok"
    assert run_import(wiki, content, tmp_path / "o", monkeypatch) == 1
    text = wiki.session().call(action="query", prop="revisions", titles=PRO, rvprop="content", rvslots="main")["query"]["pages"][0]["revisions"][0]["slots"]["main"]["content"]
    assert text == "Handgeschriebene Seite"


def test_visualeditor_loads_for_authorised_accounts(wiki):
    admin = wiki.session().login("Admin", ADMIN_PASS)
    r = admin.call(action="visualeditor", paction="parse", page="Hauptseite")
    assert "error" not in r and "mw:htmlVersion" in r["visualeditor"]["content"]     # Parsoid output
    assert "permissions-error" not in r["visualeditor"].get("notices", {})           # and the admin may edit
    anon = wiki.session().call(action="visualeditor", paction="parse", page="Hauptseite")
    assert anon.get("error", {}).get("code") == "rest-permission-error"        # anonymous cannot edit by design
