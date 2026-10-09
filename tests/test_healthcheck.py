from __future__ import annotations

import json

from deploylib import make_env


def hc(env, *args, **kw):
    return env.run("healthcheck.sh", "--only", "core", *args, **kw)


def test_healthy_stack_passes(tmp_path):
    env = make_env(tmp_path)
    proc = hc(env)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "FAIL" not in proc.stdout


def test_missing_app_api_answer_fails(tmp_path):
    env = make_env(tmp_path)
    env.set_cfg(api_ok=False)
    proc = hc(env)
    assert proc.returncode == 1
    assert "app_api" in proc.stdout


def test_stopped_app_container_fails(tmp_path):
    env = make_env(tmp_path)
    cfg = env.cfg
    cfg["containers"]["wikimedica_app"]["running"] = False
    env.cfg_path.write_text(json.dumps(cfg))
    assert hc(env).returncode == 1


def test_unhealthy_database_fails(tmp_path):
    env = make_env(tmp_path)
    env.set_cfg(db_healthy=False)
    proc = hc(env)
    assert proc.returncode == 1 and "database" in proc.stdout


def test_json_output_is_valid(tmp_path):
    env = make_env(tmp_path)
    proc = hc(env, "--json")
    assert proc.returncode == 0
    data = json.loads(proc.stdout[proc.stdout.index("{"):])
    assert data
