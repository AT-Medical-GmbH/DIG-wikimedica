#!/usr/bin/env python3
"""
Test double for the `docker` CLI, used by the deploy-script tests.

It does not start containers. It answers exactly what the Wikimedica scripts ask, is
steered by a JSON file (env FAKE_DOCKER_CFG) and logs every call to cfg["log"].

cfg keys
  log            path of the call log
  deploy_dir     the git checkout (the health of the app can depend on the checked-out tag)
  containers     {name: {"running": bool, "health": "healthy"|"starting"|"none", "image": str}}
  fail           {"<command prefix>": exit code}   e.g. {"compose pull": 1, "exec app update": 1}
  api_ok         bool | {"<tag>": bool}            does the MediaWiki API answer?
  db_mode        "fake" | "truncated" | "real"     mysqldump behaviour (real = local MariaDB)
  db_socket      unix socket of the local MariaDB (db_mode real)
  images_dir     directory standing in for /var/www/html/images and the images volume
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

CFG_PATH = os.environ["FAKE_DOCKER_CFG"]
CFG = json.load(open(CFG_PATH, encoding="utf-8"))
ARGS = sys.argv[1:]


def log(line: str) -> None:
    with open(CFG["log"], "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def forced_failure(command: str) -> None:
    for prefix, code in CFG.get("fail", {}).items():
        if command.startswith(prefix):
            log(f"  -> forced failure ({code}) for '{prefix}'")
            sys.exit(code)


def current_tag() -> str:
    out = subprocess.run(["git", "-C", CFG["deploy_dir"], "describe", "--tags", "--exact-match", "HEAD"],
                         capture_output=True, text=True)
    return out.stdout.strip()


def api_ok() -> bool:
    value = CFG.get("api_ok", True)
    if isinstance(value, dict):
        return bool(value.get(current_tag(), value.get("*", True)))
    return bool(value)


def container(name: str) -> dict | None:
    return CFG.get("containers", {}).get(name)


def save() -> None:
    json.dump(CFG, open(CFG_PATH, "w", encoding="utf-8"))


def main() -> int:
    if not ARGS:
        return 0
    sub = ARGS[0]

    if sub == "compose":
        rest = ARGS[1:]
        i = 0
        while i < len(rest) and rest[i].startswith("-"):
            i += 2  # --project-name X, --env-file F, -f F
        words = rest[i:]
        command = "compose " + " ".join(words)
        log(command + f"   [tag={current_tag() or 'none'}]")
        forced_failure(command)
        if words[:1] == ["up"] and CFG.get("after_up"):       # first deployment: containers appear now
            CFG.setdefault("containers", {}).update(CFG["after_up"])
            save()
        return 0

    if sub == "inspect":
        name = ARGS[-1]
        fmt = ARGS[ARGS.index("-f") + 1] if "-f" in ARGS else ""
        c = container(name)
        if not c:
            return 1
        if not fmt:
            print("[]")
            return 0
        if ".State.Status" in fmt:
            print(f"{'running' if c['running'] else 'exited'} {c.get('health', 'none')}")
        elif ".State.Running" in fmt:
            print("true" if c["running"] else "false")
        elif ".Config.Image" in fmt:
            print(c.get("image", "mediawiki:1.43"))
        return 0

    if sub in ("stop", "start"):
        name = ARGS[1]
        log(f"{sub} {name}")
        forced_failure(f"{sub} {name}")
        if container(name):
            container(name)["running"] = sub == "start"
            save()
        return 0

    if sub == "logs":
        print("fake log line")
        return 0

    if sub == "run":
        # docker run --rm -i -v VOL:/volume --entrypoint sh IMAGE -c 'script'
        script = ARGS[ARGS.index("-c") + 1].replace("/volume", CFG["images_dir"])
        log("run " + script)
        forced_failure("run")
        return subprocess.run(["sh", "-c", script]).returncode

    if sub == "exec":
        rest = ARGS[1:]
        while rest and rest[0] in ("-i", "-t", "-e"):
            rest = rest[2:] if rest[0] == "-e" else rest[1:]
        name, cmd = rest[0], rest[1:]
        command = f"exec {name} " + " ".join(cmd)
        log(command)
        forced_failure(command)
        db = name == "wikimedica_db" or name.endswith("_db") or name.endswith("_db_staging")
        if db:
            return exec_db(cmd)
        return exec_app(cmd)

    log("unhandled: " + " ".join(ARGS))
    return 0


def exec_db(cmd: list[str]) -> int:
    tool = cmd[0]
    if tool == "healthcheck.sh":
        return 0 if CFG.get("db_healthy", True) else 1
    mode = CFG.get("db_mode", "fake")
    if mode == "real":
        # explicit --socket: the distro client config would otherwise win over MYSQL_UNIX_PORT
        return subprocess.run([cmd[0], f"--socket={CFG['db_socket']}", *cmd[1:]]).returncode
    if tool == "mysqldump":
        sys.stdout.write("-- fake dump\nCREATE TABLE page (id INT);\n")
        if mode == "fake":
            sys.stdout.write("-- Dump completed on 2026-01-01\n")
        return 0
    if tool == "mysql":
        data = sys.stdin.buffer.read() if not sys.stdin.isatty() else b""
        if "-e" in cmd:
            print(CFG.get("page_count", 42))
        else:
            log(f"  mysql import: {len(data)} bytes")
        return 0
    return 0


def exec_app(cmd: list[str]) -> int:
    if cmd[:1] == ["php"] and "-r" in cmd:
        if api_ok():
            print('{"batchcomplete":true,"query":{"general":{"generator":"MediaWiki 1.43.11"}}}')
        return 0
    if cmd[:2] == ["php", "maintenance/run.php"] and cmd[2:3] == ["showJobs"]:
        print(CFG.get("jobs", 0))
        return 0
    if cmd[:1] == ["tar"]:
        return subprocess.run(["tar", "czf", "-", "-C", CFG["images_dir"], "."]).returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
