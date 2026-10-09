"""backup.sh / restore.sh / restore-test.sh against a REAL MariaDB 10.11 (docker is faked, mysqldump/mysql are real)."""

from __future__ import annotations

import gzip
import json
import os
import shutil
import subprocess
import tarfile
import time
from pathlib import Path

import pytest

from deploylib import GOOD_ENV, make_env

pytestmark = pytest.mark.skipif(
    not (shutil.which("mariadbd") and shutil.which("mysqldump") and shutil.which("mariadb-install-db")),
    reason="MariaDB server and client are not installed")

ROOT_PW = "rootpw"
DB = "wikimedica"


def sql(sock: str, statement: str, db: str = DB) -> str:
    result = subprocess.run(["mysql", "-S", sock, "-uroot", f"-p{ROOT_PW}", "--batch", "--skip-column-names", db, "-e", statement],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


@pytest.fixture(scope="module")
def mariadb(tmp_path_factory):
    base = tmp_path_factory.mktemp("mariadb")
    data, sock = base / "data", str(base / "mysql.sock")
    subprocess.run(["mariadb-install-db", "--user=root", f"--datadir={data}", "--auth-root-authentication-method=normal",
                    "--skip-test-db"], check=True, capture_output=True)
    proc = subprocess.Popen(["mariadbd", "--user=root", f"--datadir={data}", f"--socket={sock}", "--skip-networking",
                             f"--pid-file={base / 'pid'}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(100):
        if os.path.exists(sock):
            break
        time.sleep(0.2)
    else:
        proc.kill()
        pytest.skip("MariaDB did not start in this environment")
    subprocess.run(["mysql", "-S", sock, "-uroot", "-e",
                    f"ALTER USER 'root'@'localhost' IDENTIFIED BY '{ROOT_PW}'; CREATE DATABASE {DB} CHARACTER SET binary;"],
                   check=True, capture_output=True)
    yield sock
    proc.terminate()
    proc.wait(timeout=30)


BINARY_BLOB = bytes(range(256)) * 4


@pytest.fixture
def wiki_db(mariadb):
    """A fresh 'wiki' with German text, binary data and a MediaWiki-like binary charset."""
    sql(mariadb, "DROP TABLE IF EXISTS page; DROP TABLE IF EXISTS text_blob;")
    sql(mariadb, "CREATE TABLE page (page_id INT PRIMARY KEY, page_title VARBINARY(255)) ENGINE=InnoDB DEFAULT CHARSET=binary;"
                 "CREATE TABLE text_blob (id INT PRIMARY KEY, body MEDIUMBLOB) ENGINE=InnoDB DEFAULT CHARSET=binary;")
    sql(mariadb, "INSERT INTO page VALUES (1, CONVERT('Ärzte & Größe: Übersicht' USING binary)), (2, 'Herzinsuffizienz'), (3, 'Gender-Medizin');"
                 f"INSERT INTO text_blob VALUES (1, UNHEX('{BINARY_BLOB.hex()}')), (2, CONVERT('Für Pflegefachpersonen — äöüß' USING binary));")
    return mariadb


def checksum(sock: str) -> str:
    return sql(sock, "SELECT (SELECT SUM(CRC32(CONCAT(page_id, page_title))) FROM page), "
                     "(SELECT SUM(CRC32(CONCAT(id, body))) FROM text_blob), (SELECT COUNT(*) FROM page)")


@pytest.fixture
def b(tmp_path, wiki_db):
    env = make_env(tmp_path)
    env.set_cfg(db_mode="real", db_socket=wiki_db)
    env.write_env(GOOD_ENV.replace("rootpw", ROOT_PW))
    (env.images_dir / "Logo.png").write_bytes(b"\x89PNG-test-bytes")
    (env.images_dir / "sub").mkdir()
    (env.images_dir / "sub" / "Skizze.svg").write_text("<svg/>")
    env.sock = wiki_db
    return env


def backup(b, *args, **env):
    return b.run("backup.sh", "--no-upload", *args, **env)


def newest_prefix(b) -> str:
    return sorted((b.root / "backups").glob("wikimedica_*.manifest.json"))[-1].name.split(".")[0]


# ---------------------------------------------------------------------------
# Backup
# ---------------------------------------------------------------------------

def test_backup_creates_a_complete_verified_set(b):
    proc = backup(b)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    prefix = newest_prefix(b)
    d = b.root / "backups"
    for suffix in ("_db.sql.gz", "_images.tar.gz", "_config.tar.gz", ".sha256", ".manifest.json"):
        assert (d / f"{prefix}{suffix}").exists(), suffix
    assert subprocess.run(["sha256sum", "-c", "--quiet", f"{prefix}.sha256"], cwd=d).returncode == 0
    status = json.loads((d / "last-backup.json").read_text())
    assert status["status"] == "ok" and status["prefix"] == prefix and status["offsite"] == "skipped"
    assert json.loads((d / f"{prefix}.manifest.json").read_text())["encrypted"] is False


def test_dump_contains_the_data_with_correct_encoding(b):
    backup(b)
    dump = gzip.open(b.root / "backups" / f"{newest_prefix(b)}_db.sql.gz").read()
    assert "Ärzte & Größe".encode() in dump or b"\xc3\x84rzte" in dump or "Ärzte".encode("latin-1") in dump
    assert b"-- Dump completed" in dump[-400:]


def test_backup_files_are_private(b):
    backup(b)
    d = b.root / "backups"
    assert oct(d.stat().st_mode & 0o777) == "0o700"
    assert all(oct(p.stat().st_mode & 0o777) == "0o600" for p in d.glob("wikimedica_*"))


def test_database_password_never_appears_on_a_command_line(b):
    backup(b)
    assert ROOT_PW not in "\n".join(b.docker_log())


def test_truncated_dump_is_detected_and_leaves_no_partial_set(b):
    b.set_cfg(db_mode="truncated")
    proc = backup(b)
    assert proc.returncode == 1 and "incomplete" in proc.stdout
    d = b.root / "backups"
    assert not list(d.glob("wikimedica_*"))
    status = json.loads((d / "last-backup.json").read_text())
    assert status["status"] == "failed"


def test_failing_database_container_fails_the_backup(b):
    b.set_cfg(fail={"exec wikimedica_db mysqldump": 2})
    assert backup(b).returncode == 1 and not list((b.root / "backups").glob("*.manifest.json"))


def test_config_archive_redacts_secrets(b):
    ls = b.deploy_dir / "infra" / "mediawiki" / "LocalSettings.php"
    ls.parent.mkdir(parents=True, exist_ok=True)
    ls.write_text("""<?php
$wgSitename = "Wikimedica";
$wgSecretKey = "SUPER-SECRET-KEY-12345";
$wgUpgradeKey = 'upgrade-key-abcdef';
$wgDBpassword = 'hunter2-db';
$wgReCaptchaSecretKey = "recaptcha-secret-xyz";
$wgSMTP = [ 'host' => 'smtp.example.org', 'username' => 'u', 'password' => 'smtp-pass-987' ];
$wgLanguageCode = "de";
""")
    backup(b)
    with tarfile.open(b.root / "backups" / f"{newest_prefix(b)}_config.tar.gz") as tar:
        text = tar.extractfile("./LocalSettings.redacted.php").read().decode()
    for secret in ("SUPER-SECRET-KEY-12345", "upgrade-key-abcdef", "hunter2-db", "recaptcha-secret-xyz", "smtp-pass-987"):
        assert secret not in text, secret
    assert 'Wikimedica' in text and 'smtp.example.org' in text and '"de"' in text   # the rest stays useful


def test_env_file_is_not_part_of_the_backup(b):
    backup(b)
    with tarfile.open(b.root / "backups" / f"{newest_prefix(b)}_config.tar.gz") as tar:
        assert not any(".env" in n for n in tar.getnames())


def test_backup_rotates_old_sets(b):
    d = b.root / "backups"
    d.mkdir(exist_ok=True)
    from datetime import datetime, timedelta, timezone
    for n in range(1, 40):
        stamp = (datetime.now(timezone.utc) - timedelta(days=n)).strftime("%Y%m%d_%H%M%S")
        for suffix in ("_db.sql.gz", ".manifest.json"):
            (d / f"wikimedica_{stamp}{suffix}").write_text("x")
    assert backup(b).returncode == 0
    sets = list(d.glob("wikimedica_*.manifest.json"))
    assert 8 <= len(sets) <= 15 and any(newest_prefix(b) in s.name for s in sets)


# ---------------------------------------------------------------------------
# Restore
# ---------------------------------------------------------------------------

def test_restore_brings_back_exactly_the_backed_up_state(b):
    before = checksum(b.sock)
    assert backup(b).returncode == 0
    prefix = newest_prefix(b)

    # disaster: data destroyed, upload deleted, garbage added
    sql(b.sock, "DELETE FROM page WHERE page_id IN (1,2); UPDATE text_blob SET body = 'kaputt'; INSERT INTO page VALUES (99, 'Vandalismus');")
    (b.images_dir / "Logo.png").unlink()
    shutil.rmtree(b.images_dir / "sub")
    assert checksum(b.sock) != before

    proc = b.run("restore.sh", "--prefix", prefix, "--yes-overwrite")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert checksum(b.sock) == before                                              # byte-exact
    assert (b.images_dir / "Logo.png").read_bytes() == b"\x89PNG-test-bytes"
    assert (b.images_dir / "sub" / "Skizze.svg").read_text() == "<svg/>"
    assert sql(b.sock, "SELECT CONVERT(page_title USING utf8mb4) FROM page WHERE page_id=1") == "Ärzte & Größe: Übersicht"
    assert sql(b.sock, "SELECT HEX(body) FROM text_blob WHERE id=1") == BINARY_BLOB.hex().upper()


def test_restore_takes_a_safety_dump_of_the_damaged_state_first(b):
    backup(b)
    sql(b.sock, "INSERT INTO page VALUES (77, 'Nach dem Backup entstanden')")
    proc = b.run("restore.sh", "--prefix", newest_prefix(b), "--yes-overwrite")
    safety = list((b.root / "backups").glob("prerestore_*_db.sql.gz"))
    assert proc.returncode == 0 and len(safety) == 1
    assert b"Nach dem Backup entstanden" in gzip.open(safety[0]).read()            # the restore is itself reversible
    assert "To undo this restore" in proc.stdout


def test_application_is_stopped_during_the_restore_and_started_afterwards(b):
    backup(b)
    b.run("restore.sh", "--prefix", newest_prefix(b), "--yes-overwrite")
    log = b.docker_log()
    stop = next(i for i, l in enumerate(log) if l == "stop wikimedica_app")
    imp = next(i for i, l in enumerate(log) if "mysql" in l and "exec wikimedica_db" in l and "mysqldump" not in l)
    start = next(i for i, l in enumerate(log) if l == "start wikimedica_app")
    assert stop < imp < start
    assert any("update --quick" in l for l in log[start:])                        # schema brought up to date


def test_restore_refuses_without_explicit_confirmation(b):
    backup(b)
    sql(b.sock, "DELETE FROM page")
    proc = b.run("restore.sh", "--prefix", newest_prefix(b))
    assert proc.returncode != 0 and "--yes-overwrite" in proc.stdout
    assert sql(b.sock, "SELECT COUNT(*) FROM page") == "0"                         # untouched
    assert not any(l.startswith("stop") for l in b.docker_log())


def test_restore_refuses_a_damaged_backup_before_changing_anything(b):
    backup(b)
    prefix = newest_prefix(b)
    dump = b.root / "backups" / f"{prefix}_db.sql.gz"
    raw = bytearray(dump.read_bytes())
    raw[len(raw) // 2] ^= 0xFF                                                      # flip one byte
    dump.write_bytes(bytes(raw))
    sql(b.sock, "INSERT INTO page VALUES (55, 'Live-Daten')")
    proc = b.run("restore.sh", "--prefix", prefix, "--yes-overwrite")
    assert proc.returncode != 0 and "checksum" in proc.stdout.lower()
    assert sql(b.sock, "SELECT COUNT(*) FROM page WHERE page_id=55") == "1"        # live data intact
    assert not any(l.startswith("stop") for l in b.docker_log())


def test_restore_refuses_an_incomplete_set(b):
    backup(b)
    prefix = newest_prefix(b)
    (b.root / "backups" / f"{prefix}.manifest.json").unlink()
    assert b.run("restore.sh", "--prefix", prefix, "--yes-overwrite").returncode != 0


@pytest.mark.parametrize("prefix", ["", "../etc/passwd", "wikimedica_2026", "x; rm -rf /", "wikimedica_20261009_020000"])
def test_restore_validates_the_prefix(b, prefix):
    args = ["--yes-overwrite"] + (["--prefix", prefix] if prefix else [])
    assert b.run("restore.sh", *args).returncode != 0


def test_restore_failure_restarts_the_application(b):
    backup(b)
    b.set_cfg(fail={"exec wikimedica_db mysql ": 1})
    proc = b.run("restore.sh", "--prefix", newest_prefix(b), "--yes-overwrite")
    assert proc.returncode != 0
    log = b.docker_log()
    assert log.index("stop wikimedica_app") < len(log) - 1 and "start wikimedica_app" in log


def test_db_only_and_images_only_restores_are_independent(b):
    backup(b)
    prefix = newest_prefix(b)
    sql(b.sock, "DELETE FROM page WHERE page_id=1")
    (b.images_dir / "Logo.png").unlink()
    assert b.run("restore.sh", "--prefix", prefix, "--yes-overwrite", "--images-only").returncode == 0
    assert (b.images_dir / "Logo.png").exists() and sql(b.sock, "SELECT COUNT(*) FROM page WHERE page_id=1") == "0"
    assert b.run("restore.sh", "--prefix", prefix, "--yes-overwrite", "--db-only").returncode == 0
    assert sql(b.sock, "SELECT COUNT(*) FROM page WHERE page_id=1") == "1"


def test_list_shows_complete_sets_only(b):
    backup(b)
    prefix = newest_prefix(b)
    (b.root / "backups" / "wikimedica_20200101_000000_db.sql.gz").write_text("x")      # incomplete: no manifest
    proc = b.run("restore.sh", "--list")
    assert prefix in proc.stdout and "20200101" not in proc.stdout


# ---------------------------------------------------------------------------
# Encryption and offsite upload
# ---------------------------------------------------------------------------

@pytest.fixture
def gpg_home(tmp_path):
    if not shutil.which("gpg"):
        pytest.skip("gpg not installed")
    home = tmp_path / "gnupg"
    home.mkdir(mode=0o700)
    env = {**os.environ, "GNUPGHOME": str(home)}
    subprocess.run(["gpg", "--batch", "--pinentry-mode", "loopback", "--passphrase", "", "--quick-generate-key",
                    "backup@test.example", "default", "default", "never"], env=env, check=True, capture_output=True)
    return home


def test_encrypted_backup_roundtrip(b, gpg_home):
    env = {"GNUPGHOME": gpg_home, "BACKUP_GPG_RECIPIENT": "backup@test.example"}
    b.write_env(GOOD_ENV.replace("rootpw", ROOT_PW) + "BACKUP_GPG_RECIPIENT=backup@test.example\n")
    before = checksum(b.sock)
    assert backup(b, **env).returncode == 0
    d = b.root / "backups"
    prefix = newest_prefix(b)
    assert (d / f"{prefix}_db.sql.gz.gpg").exists() and not (d / f"{prefix}_db.sql.gz").exists()   # no plaintext left
    assert b"Dump completed" not in (d / f"{prefix}_db.sql.gz.gpg").read_bytes()
    assert ".gpg" in (d / f"{prefix}.sha256").read_text()
    assert json.loads((d / f"{prefix}.manifest.json").read_text())["encrypted"] is True

    sql(b.sock, "DELETE FROM page")
    proc = b.run("restore.sh", "--prefix", prefix, "--yes-overwrite", **env)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert checksum(b.sock) == before


def test_encrypted_backup_cannot_be_restored_without_the_key(b, gpg_home, tmp_path):
    env = {"GNUPGHOME": gpg_home, "BACKUP_GPG_RECIPIENT": "backup@test.example"}
    b.write_env(GOOD_ENV.replace("rootpw", ROOT_PW) + "BACKUP_GPG_RECIPIENT=backup@test.example\n")
    backup(b, **env)
    stranger = tmp_path / "other-gnupg"
    stranger.mkdir(mode=0o700)
    sql(b.sock, "INSERT INTO page VALUES (66, 'bleibt')")
    proc = b.run("restore.sh", "--prefix", newest_prefix(b), "--yes-overwrite", GNUPGHOME=stranger)
    assert proc.returncode != 0 and sql(b.sock, "SELECT COUNT(*) FROM page WHERE page_id=66") == "1"


def _shim(bin_dir: Path, name: str, exit_code: int) -> Path:
    log = bin_dir / f"{name}.log"
    script = bin_dir / name
    script.write_text(f"#!/bin/sh\necho \"$@\" >> {log}\nexit {exit_code}\n")
    script.chmod(0o755)
    return log


def test_offsite_upload_of_unencrypted_dumps_is_refused(b):
    b.write_env(GOOD_ENV.replace("rootpw", ROOT_PW) + "BACKUP_SFTP_HOST=backup.example.org\nBACKUP_SFTP_USER=wm\n")
    rsync_log = _shim(b.bin_dir, "rsync", 0)
    proc = b.run("backup.sh")
    assert proc.returncode == 3 and "not encrypted" in proc.stdout
    assert not rsync_log.exists()                                                   # nothing left the server
    status = json.loads((b.root / "backups" / "last-backup.json").read_text())
    assert status["status"] == "ok" and status["offsite"] == "refused-unencrypted"
    assert list((b.root / "backups").glob("*.manifest.json"))                      # local backup is still valid


def test_encrypted_offsite_upload_succeeds(b, gpg_home):
    env = {"GNUPGHOME": gpg_home}
    b.write_env(GOOD_ENV.replace("rootpw", ROOT_PW) + "BACKUP_GPG_RECIPIENT=backup@test.example\n"
                "BACKUP_SFTP_HOST=backup.example.org\nBACKUP_SFTP_USER=wm\n")
    rsync_log = _shim(b.bin_dir, "rsync", 0)
    proc = b.run("backup.sh", **env)
    assert proc.returncode == 0, proc.stdout
    uploaded = rsync_log.read_text()
    assert ".gpg" in uploaded and "wm@backup.example.org" in uploaded and "manifest.json" in uploaded
    assert json.loads((b.root / "backups" / "last-backup.json").read_text())["offsite"] == "ok"


def test_failed_upload_is_reported_but_keeps_the_local_backup(b, gpg_home):
    env = {"GNUPGHOME": gpg_home}
    b.write_env(GOOD_ENV.replace("rootpw", ROOT_PW) + "BACKUP_GPG_RECIPIENT=backup@test.example\n"
                "BACKUP_SFTP_HOST=backup.example.org\nBACKUP_SFTP_USER=wm\n")
    _shim(b.bin_dir, "rsync", 23)
    proc = b.run("backup.sh", **env)
    assert proc.returncode == 3
    assert json.loads((b.root / "backups" / "last-backup.json").read_text())["offsite"] == "failed"
    assert list((b.root / "backups").glob("*.manifest.json"))


# ---------------------------------------------------------------------------
# Monthly restore test
# ---------------------------------------------------------------------------

def test_restore_test_refuses_to_run_on_production(b):
    proc = b.run("restore-test.sh", "--from", str(b.root / "backups"), DEPLOY_ENV="production")
    assert proc.returncode != 0 and "only runs on staging" in proc.stdout


def test_restore_test_restores_the_newest_production_backup_into_staging(b, tmp_path):
    before = checksum(b.sock)
    backup(b)
    prod_dir = b.root / "backups"
    sql(b.sock, "DELETE FROM page")
    proc = b.run("restore-test.sh", "--from", str(prod_dir), DEPLOY_ENV="staging", BACKUP_LOCAL_DIR=tmp_path / "staging-backups")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    result = json.loads((tmp_path / "staging-backups" / "last-restore-test.json").read_text())
    assert result["status"] == "ok" and result["set"] == newest_prefix(b) and int(result["pages"]) == 3
    assert checksum(b.sock) == before


def test_restore_test_fails_loudly_when_the_backup_is_empty(b, tmp_path):
    """A restore that 'succeeds' into an empty wiki must not count as a passed test."""
    sql(b.sock, "DELETE FROM page; DELETE FROM text_blob;")
    backup(b)
    proc = b.run("restore-test.sh", "--from", str(b.root / "backups"), DEPLOY_ENV="staging",
                 BACKUP_LOCAL_DIR=tmp_path / "staging-backups")
    assert proc.returncode != 0
    assert json.loads((tmp_path / "staging-backups" / "last-restore-test.json").read_text())["status"] == "failed"
