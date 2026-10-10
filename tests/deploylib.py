"""Helpers to run the real deploy scripts against a real git repository and a fake docker."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "infra" / "deploy"

GOOD_ENV = """\
DOMAIN=wiki.example.test
MEDIAWIKI_DB_HOST=mariadb
MEDIAWIKI_DB_NAME=wikimedica
MEDIAWIKI_DB_USER=wikimedica_app
MEDIAWIKI_DB_PASSWORD=app-pw-with-$dollar-and-`tick`
MEDIAWIKI_DB_ROOT_PASSWORD=rootpw
MEDIAWIKI_SECRET_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
MEDIAWIKI_UPGRADE_KEY=0123456789abcdef
TRAEFIK_ACME_EMAIL=ops@example.test
CLOUDFLARE_API_TOKEN=cf-token
BACKUP_S3_ENDPOINT=REPLACE_WITH_S3_ENDPOINT_URL
BACKUP_S3_BUCKET=REPLACE_WITH_BACKUP_BUCKET_NAME
BACKUP_SFTP_HOST=REPLACE_WITH_SFTP_HOST
HEALTHCHECK_URL=REPLACE_WITH_HEALTHCHECK_PING_URL
ALERT_EMAIL=ops@example.test
"""


def git(cwd: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout.strip()


@dataclass
class DeployEnv:
    root: Path
    origin: Path
    deploy_dir: Path
    bin_dir: Path
    cfg_path: Path
    log_path: Path
    images_dir: Path
    commits: dict[str, str] = field(default_factory=dict)

    # -- configuration of the fake docker ------------------------------------
    @property
    def cfg(self) -> dict:
        return json.loads(self.cfg_path.read_text())

    def set_cfg(self, **changes) -> None:
        cfg = self.cfg
        cfg.update(changes)
        self.cfg_path.write_text(json.dumps(cfg))

    def docker_log(self) -> list[str]:
        return self.log_path.read_text().splitlines() if self.log_path.exists() else []

    def write_env(self, text: str = GOOD_ENV) -> None:
        env_file = self.deploy_dir / "infra" / "env" / ".env"
        env_file.parent.mkdir(parents=True, exist_ok=True)
        env_file.write_text(text)

    # -- running the scripts -----------------------------------------------------
    def env(self, **extra) -> dict:
        base = {k: v for k, v in os.environ.items() if not k.startswith(("WM_", "DEPLOY_", "BACKUP_"))}
        base.update(
            PATH=f"{self.bin_dir}:{base['PATH']}", DEPLOY_DIR=str(self.deploy_dir),
            FAKE_DOCKER_CFG=str(self.cfg_path), HEALTH_SLEEP_SECONDS="0", HEALTH_WAIT_SECONDS="0",
            LOG_FILE=str(self.root / "deploy.log"), BACKUP_LOCAL_DIR=str(self.root / "backups"),
        )
        base.update({k: str(v) for k, v in extra.items()})
        return base

    def run(self, script: str, *args: str, **env) -> subprocess.CompletedProcess:
        return subprocess.run([str(SCRIPTS / script), *args], env=self.env(**env), capture_output=True,
                              text=True, timeout=120)

    def head(self) -> str:
        return git(self.deploy_dir, "rev-parse", "HEAD")

    def head_tag(self) -> str:
        return git(self.deploy_dir, "describe", "--tags", "--exact-match", "HEAD", check=False)

    def summary(self) -> str:
        path = self.deploy_dir / "deploy-summary.md"
        return path.read_text() if path.exists() else ""

    def version_file(self) -> dict:
        path = self.deploy_dir / "deployed-version"
        return dict(l.split("=", 1) for l in path.read_text().splitlines()) if path.exists() else {}


def make_env(tmp_path: Path) -> DeployEnv:
    root = tmp_path
    origin, deploy_dir = root / "origin.git", root / "wikimedica"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)

    seed = root / "seed"
    seed.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(seed)], check=True)
    for k, v in (("user.email", "t@example.org"), ("user.name", "Test")):
        git(seed, "config", k, v)
    git(seed, "remote", "add", "origin", str(origin))
    (seed / "infra" / "mediawiki").mkdir(parents=True)
    (seed / "README.md").write_text("v1.0.0")
    git(seed, "add", "-A"); git(seed, "commit", "-q", "-m", "release 1.0.0"); git(seed, "tag", "v1.0.0")
    (seed / "README.md").write_text("v1.1.0")
    git(seed, "commit", "-q", "-am", "release 1.1.0"); git(seed, "tag", "v1.1.0")
    (seed / "README.md").write_text("v1.2.0")
    git(seed, "commit", "-q", "-am", "release 1.2.0"); git(seed, "tag", "v1.2.0")
    git(seed, "push", "-q", "origin", "main", "--tags")
    # a tag that is NOT on main
    git(seed, "checkout", "-q", "-b", "side", "v1.0.0")
    (seed / "README.md").write_text("side")
    git(seed, "commit", "-q", "-am", "unreviewed work"); git(seed, "tag", "v9.9.9")
    git(seed, "push", "-q", "origin", "side", "--tags")
    commits = {t: git(seed, "rev-parse", t) for t in ("v1.0.0", "v1.1.0", "v1.2.0", "v9.9.9")}

    subprocess.run(["git", "clone", "-q", str(origin), str(deploy_dir)], check=True)
    for k, v in (("user.email", "t@example.org"), ("user.name", "Test")):
        git(deploy_dir, "config", k, v)
    git(deploy_dir, "checkout", "-q", "--detach", "v1.0.0")

    bin_dir = root / "bin"
    bin_dir.mkdir()
    shim = bin_dir / "docker"
    shim.write_text(f"#!{sys.executable}\nimport runpy,sys\nsys.argv[0]={str(REPO / 'tests' / 'fake_docker.py')!r}\n"
                    f"runpy.run_path({str(REPO / 'tests' / 'fake_docker.py')!r}, run_name='__main__')\n")
    shim.chmod(shim.stat().st_mode | stat.S_IEXEC)

    images = root / "images"
    images.mkdir()
    cfg_path, log_path = root / "docker-cfg.json", root / "docker.log"
    cfg_path.write_text(json.dumps({
        "log": str(log_path), "deploy_dir": str(deploy_dir), "images_dir": str(images),
        "containers": {"wikimedica_app": {"running": True, "health": "healthy", "image": "mediawiki:1.43"},
                       "wikimedica_db": {"running": True, "health": "healthy"},
                       "wikimedica_app_staging": {"running": True, "health": "healthy"},
                       "wikimedica_db_staging": {"running": True, "health": "healthy"}},
        "api_ok": True, "db_mode": "fake", "fail": {},
    }))
    env = DeployEnv(root, origin, deploy_dir, bin_dir, cfg_path, log_path, images, commits)
    env.write_env()
    return env
