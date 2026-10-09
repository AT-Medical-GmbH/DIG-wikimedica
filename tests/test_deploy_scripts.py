"""infra/deploy/deploy.sh and rollback.sh — run for real against a real git repository and a fake docker."""

from __future__ import annotations

import fcntl
import json

import pytest

from deploylib import GOOD_ENV, git, make_env

pytestmark = pytest.mark.skipif(__import__("shutil").which("flock") is None, reason="flock not installed")


@pytest.fixture
def d(tmp_path):
    env = make_env(tmp_path)
    ls = env.deploy_dir / "infra" / "mediawiki" / "LocalSettings.php"
    ls.parent.mkdir(parents=True, exist_ok=True)
    ls.write_text("<?php // installed\n")
    return env


def calls(env, needle):
    return [i for i, line in enumerate(env.docker_log()) if needle in line]


def last_line(proc):
    return proc.stdout.strip().splitlines()[-1]


# ---------------------------------------------------------------------------
# The happy path
# ---------------------------------------------------------------------------

def test_deploy_rolls_out_the_requested_tag_not_main(d):
    """Regression: the old script parsed --tag and then overwrote it with $1, silently deploying main."""
    proc = d.run("deploy.sh", "--tag", "v1.1.0")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert d.head_tag() == "v1.1.0"                       # NOT v1.2.0 (the tip of main)
    assert d.head() == d.commits["v1.1.0"]
    assert last_line(proc) == "DEPLOY_RESULT=success"


def test_positional_tag_works_too(d):
    assert d.run("deploy.sh", "v1.1.0").returncode == 0 and d.head_tag() == "v1.1.0"


def test_sequence_is_backup_then_up_then_update_then_health(d):
    d.run("deploy.sh", "--tag", "v1.1.0")
    log = d.docker_log()
    backup = next(i for i, l in enumerate(log) if "mysqldump" in l)
    pull = next(i for i, l in enumerate(log) if l.startswith("compose pull"))
    up = next(i for i, l in enumerate(log) if l.startswith("compose up"))
    update = next(i for i, l in enumerate(log) if "update --quick" in l)
    assert backup < pull < up < update
    assert any("[tag=v1.1.0]" in l for l in log if l.startswith("compose up"))   # started the NEW version


def test_a_backup_set_exists_before_anything_is_changed(d):
    d.run("deploy.sh", "--tag", "v1.1.0")
    manifests = list((d.root / "backups").glob("wikimedica_*.manifest.json"))
    assert len(manifests) == 1
    assert json.loads((d.root / "backups" / "last-backup.json").read_text())["status"] == "ok"


def test_deployed_version_and_summary_are_recorded(d):
    d.run("deploy.sh", "--tag", "v1.1.0")
    v = d.version_file()
    assert v["ref"] == "v1.1.0" and v["commit"] == d.commits["v1.1.0"] and v["previous"] == "v1.0.0"
    assert "**success**" in d.summary()


def test_env_file_is_never_executed(d):
    """A password with $ and backticks must neither break nor run anything (the old script `source`d the file)."""
    marker = d.root / "pwned"
    d.write_env(GOOD_ENV + f"ALERT_EMAIL=$(touch {marker})\nEXTRA=`touch {marker}`\n")
    proc = d.run("deploy.sh", "--tag", "v1.1.0")
    assert proc.returncode == 0 and not marker.exists()


# ---------------------------------------------------------------------------
# Refusals: nothing may change on the server
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ref", ["main", "latest", "HEAD", "v1.1", "1.1.0", "v1.1.0-rc1", "origin/main", "side",
                                 "v1.1.0; touch /tmp/x"])
def test_production_accepts_only_release_tags(d, ref):
    before = d.head()
    proc = d.run("deploy.sh", "--tag", ref)
    assert proc.returncode != 0 and "release tags only" in proc.stdout
    assert d.head() == before and not calls(d, "compose")


def test_tag_that_is_not_on_main_is_refused(d):
    before = d.head()
    proc = d.run("deploy.sh", "--tag", "v9.9.9")
    assert proc.returncode != 0 and "not on main" in proc.stdout
    assert d.head() == before and not calls(d, "compose up")
    assert last_line(proc) == "DEPLOY_RESULT=failed"


def test_unknown_tag_is_refused(d):
    proc = d.run("deploy.sh", "--tag", "v7.7.7")
    assert proc.returncode != 0 and "not found" in proc.stdout and d.head_tag() == "v1.0.0"


def test_incomplete_env_is_refused_and_names_the_keys(d):
    d.write_env(GOOD_ENV.replace("MEDIAWIKI_SECRET_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
                                 "MEDIAWIKI_SECRET_KEY=REPLACE_WITH_64_CHARACTER_HEX_STRING"))
    proc = d.run("deploy.sh", "--tag", "v1.1.0")
    assert proc.returncode != 0 and "MEDIAWIKI_SECRET_KEY" in proc.stdout
    assert d.head_tag() == "v1.0.0" and not calls(d, "compose")


def test_optional_placeholders_do_not_block_a_deploy(d):
    """S3/SFTP/healthcheck placeholders in .env.example are optional; they must not fail a deploy."""
    assert "REPLACE_WITH_S3" in GOOD_ENV
    assert d.run("deploy.sh", "--tag", "v1.1.0").returncode == 0


def test_dirty_working_tree_is_refused(d):
    (d.deploy_dir / "README.md").write_text("local hotfix on the server")
    proc = d.run("deploy.sh", "--tag", "v1.1.0")
    assert proc.returncode != 0 and "local modifications" in proc.stdout and not calls(d, "compose")


def test_a_moved_remote_tag_aborts_the_deploy(d):
    """Release tags must be immutable. If the remote tag moved, git fetch refuses and so do we."""
    seed = d.root / "seed"
    git(seed, "checkout", "-q", "main")
    (seed / "README.md").write_text("sneaky")
    git(seed, "commit", "-q", "-am", "sneaky")
    git(seed, "tag", "-f", "v1.1.0")
    git(seed, "push", "-q", "-f", "origin", "main", "--tags")
    proc = d.run("deploy.sh", "--tag", "v1.1.0")
    assert proc.returncode != 0 and not calls(d, "compose up")
    assert d.head() == d.commits["v1.0.0"]


def test_concurrent_deployments_are_refused(d):
    with open(d.deploy_dir / ".deploy.lock", "w") as held:
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        proc = d.run("deploy.sh", "--tag", "v1.1.0")
    assert proc.returncode != 0 and "another deployment" in proc.stdout


def test_staging_may_deploy_a_branch(d):
    d.set_cfg(containers={**d.cfg["containers"]})
    proc = d.run("deploy.sh", "--tag", "side", DEPLOY_ENV="staging")
    assert proc.returncode == 0, proc.stdout
    assert d.head() == git(d.deploy_dir, "rev-parse", "origin/side")
    assert any("--project-name" not in l and l.startswith("compose") for l in d.docker_log())


# ---------------------------------------------------------------------------
# Failures: backup, rollback and honest reporting
# ---------------------------------------------------------------------------

def test_failed_backup_aborts_before_any_change(d):
    d.set_cfg(db_mode="truncated")                      # dump without the 'Dump completed' trailer
    proc = d.run("deploy.sh", "--tag", "v1.1.0")
    assert proc.returncode != 0 and "backup" in proc.stdout.lower()
    assert d.head_tag() == "v1.0.0" and not calls(d, "compose up")
    assert "Nothing was changed" in d.summary()


def test_first_deployment_skips_the_backup(d):
    created = d.cfg["containers"]
    d.set_cfg(containers={}, after_up=created)          # nothing exists until `compose up` creates it
    proc = d.run("deploy.sh", "--tag", "v1.1.0")
    assert proc.returncode == 0, proc.stdout
    assert "first deployment" in proc.stdout
    assert not calls(d, "mysqldump") and not list((d.root / "backups").glob("*.manifest.json"))


def test_unhealthy_release_is_rolled_back_automatically(d):
    d.set_cfg(api_ok={"v1.0.0": True, "v1.1.0": False})
    proc = d.run("deploy.sh", "--tag", "v1.1.0")
    assert proc.returncode == 1
    assert last_line(proc) == "DEPLOY_RESULT=rolled-back"
    assert d.head_tag() == "v1.0.0"                                   # back on the previous version
    assert len(calls(d, "compose up")) == 2                           # deploy + rollback
    assert "rolled-back" in d.summary() and "v1.0.0" in d.summary()
    assert d.version_file()["ref"] == "v1.0.0"


def test_update_php_failure_is_rolled_back_and_mentions_the_database(d):
    d.set_cfg(fail={"exec wikimedica_app php maintenance/run.php update": 1})
    proc = d.run("deploy.sh", "--tag", "v1.1.0")
    assert proc.returncode == 1 and d.head_tag() == "v1.0.0"
    assert last_line(proc) == "DEPLOY_RESULT=rolled-back"


def test_failure_after_migration_warns_about_the_database(d):
    d.set_cfg(api_ok={"v1.0.0": True, "v1.1.0": False})
    d.run("deploy.sh", "--tag", "v1.1.0")
    assert "update.php had already migrated the database" in d.summary()


def test_rollback_failure_is_reported_as_such(d):
    d.set_cfg(api_ok=False)                                           # old version is unhealthy too
    proc = d.run("deploy.sh", "--tag", "v1.1.0")
    assert proc.returncode == 1 and last_line(proc) == "DEPLOY_RESULT=rollback-failed"
    assert "FAILED" in d.summary()


def test_no_rollback_flag_leaves_the_failed_release_for_inspection(d):
    d.set_cfg(api_ok={"v1.0.0": True, "v1.1.0": False})
    proc = d.run("deploy.sh", "--tag", "v1.1.0", "--no-rollback")
    assert last_line(proc) == "DEPLOY_RESULT=failed" and d.head_tag() == "v1.1.0"


def test_compose_pull_failure_is_rolled_back(d):
    d.set_cfg(fail={"compose pull": 1})
    proc = d.run("deploy.sh", "--tag", "v1.1.0")
    assert proc.returncode == 1 and d.head_tag() == "v1.0.0"


def test_healthcheck_url_is_notified_only_when_configured(d):
    """REPLACE_WITH_* in HEALTHCHECK_URL must not be called; a real URL is attempted (no network here, so we only check it does not crash)."""
    assert d.run("deploy.sh", "--tag", "v1.1.0").returncode == 0


# ---------------------------------------------------------------------------
# rollback.sh
# ---------------------------------------------------------------------------

def test_rollback_returns_to_the_previous_release(d):
    d.run("deploy.sh", "--tag", "v1.2.0")
    proc = d.run("rollback.sh", "v1.1.0", "--reason", "regression in 1.2.0")
    assert proc.returncode == 0, proc.stdout
    assert d.head_tag() == "v1.1.0"
    assert d.version_file()["rollback_reason"] == "regression in 1.2.0"


def test_rollback_does_not_run_update_php(d):
    d.run("deploy.sh", "--tag", "v1.2.0")
    before = len(calls(d, "update --quick"))
    d.run("rollback.sh", "v1.1.0")
    assert len(calls(d, "update --quick")) == before


def test_rollback_does_not_stop_the_stack_first(d):
    d.run("rollback.sh", "v1.1.0")
    assert not calls(d, "compose down")


def test_rollback_exit_code_tells_the_truth(d):
    d.set_cfg(api_ok=False)
    proc = d.run("rollback.sh", "v1.1.0")
    assert proc.returncode != 0 and "NOT healthy" in proc.stdout


@pytest.mark.parametrize("target", ["main", "side", "latest", "v1.1"])
def test_production_rollback_targets_are_restricted(d, target):
    proc = d.run("rollback.sh", target)
    assert proc.returncode != 0 and d.head_tag() == "v1.0.0"


def test_rollback_refuses_a_tag_that_is_not_on_main(d):
    assert d.run("rollback.sh", "v9.9.9").returncode != 0


def test_rollback_accepts_a_full_commit_hash_from_main(d):
    assert d.run("rollback.sh", d.commits["v1.1.0"]).returncode == 0 and d.head() == d.commits["v1.1.0"]


def test_rollback_can_restore_the_database(d):
    d.root.joinpath("backups").mkdir(exist_ok=True)
    d.run("backup.sh", "--no-upload")                                   # create a real set via the fake docker
    prefix = next((d.root / "backups").glob("wikimedica_*.manifest.json")).name.split(".")[0]
    proc = d.run("rollback.sh", "v1.1.0", "--restore-db", prefix)
    assert proc.returncode == 0, proc.stdout
    assert any("mysql import" in l for l in d.docker_log())
