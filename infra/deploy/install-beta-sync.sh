#!/usr/bin/env bash
# One-time setup on the WikiMedica SERVER after this PR is merged.
# Requires sudo/root, systemd, Docker/MediaWiki already installed.
# Creates a daily 06:30 Europe/Berlin timer independent of GitHub Actions.
set -Eeuo pipefail
umask 077
[ "$(id -u)" -eq 0 ] || { echo "Run with sudo" >&2; exit 1; }
command -v systemctl >/dev/null || { echo "systemd is required" >&2; exit 1; }
command -v git >/dev/null || { echo "git is required" >&2; exit 1; }
python3 -c 'import yaml' || { echo "Install PyYAML: apt-get install -y python3-yaml" >&2; exit 1; }

ENV_DIR=/etc/wikimedica
ENV_FILE=$ENV_DIR/github-pull.env
SOURCE_DIR=/opt/wikimedica-source
REPO_URL=https://github.com/AT-Medical-GmbH/DIG-wikimedica.git
mkdir -p -m 0700 "$ENV_DIR" /var/lib/wikimedica-pull
chmod 0700 "$ENV_DIR" /var/lib/wikimedica-pull

# The local maintenance importer runs inside the existing production container.
# It does NOT require API credentials. Keep any older BotPassword file untouched.
if [ -f "$ENV_FILE" ]; then
  echo "Existing configuration retained in $ENV_FILE (not used for local CLI access)."
fi
docker inspect --format '{{.State.Running}}' wikimedica_app | grep -qx true ||
  { echo "Production MediaWiki container wikimedica_app is not running" >&2; exit 1; }

if [ ! -d "$SOURCE_DIR/.git" ]; then
  [ ! -e "$SOURCE_DIR" ] || { echo "$SOURCE_DIR exists but is not a repository" >&2; exit 1; }
  git clone --branch main "$REPO_URL" "$SOURCE_DIR"
fi

cat >/etc/systemd/system/wikimedica-beta-sync.service <<'UNIT'
[Unit]
Description=WikiMedica BETA articles: GitHub main -> MediaWiki
Wants=network-online.target
After=network-online.target
[Service]
Type=oneshot
User=root
Group=root
UMask=0077
EnvironmentFile=-/etc/wikimedica/github-pull.env
WorkingDirectory=/opt/wikimedica-source
ExecStart=/bin/bash /opt/wikimedica-source/infra/deploy/pull-content-from-github.sh --env production --mode beta-local
TimeoutStartSec=1800
NoNewPrivileges=true
ProtectHome=true
PrivateTmp=true
UNIT

cat >/etc/systemd/system/wikimedica-beta-sync.timer <<'UNIT'
[Unit]
Description=Daily WikiMedica GitHub-to-MediaWiki BETA sync
[Timer]
OnCalendar=*-*-* 06:30:00 Europe/Berlin
Persistent=true
AccuracySec=1min
Unit=wikimedica-beta-sync.service
[Install]
WantedBy=timers.target
UNIT

systemctl daemon-reload
systemctl enable --now wikimedica-beta-sync.timer

echo
echo "Timer installed. First run imports only the hypertension pilot from merged main:"
/bin/bash "$SOURCE_DIR/infra/deploy/pull-content-from-github.sh" \
  --env production --mode beta-local --only arterielle-hypertonie

echo
echo "First local import finished. Confirm page in browser: https://wikimedica.info/index.php?title=Arterielle_Hypertonie"
echo "Future schedules: systemctl list-timers wikimedica-beta-sync.timer"
echo "Logs: journalctl -u wikimedica-beta-sync.service --no-pager -n 80"
