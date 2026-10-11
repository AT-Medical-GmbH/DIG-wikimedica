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

if [ -f "$ENV_FILE" ]; then
  echo "Using existing $ENV_FILE (not replacing secrets)."
else
  API_URL="https://wikimedica.info/api.php"
  printf 'Production MediaWiki API URL [%s]: ' "$API_URL"
  read -r input_api
  [ -z "$input_api" ] || API_URL="$input_api"
  [[ "$API_URL" == https://* ]] || { echo "HTTPS API URL required" >&2; exit 1; }
  printf 'MediaWiki BotPassword username (Account@BotName): '
  read -r BOT_USER
  [[ "$BOT_USER" == *@* ]] || { echo "Use the BotPassword login in Account@BotName format" >&2; exit 1; }
  printf 'MediaWiki BotPassword token (hidden): '
  read -r -s BOT_PASS
  printf '\n'
  [[ "$BOT_PASS" =~ ^[0-9a-w]{32,}$ ]] || {
    echo "BotPassword token must contain 32+ characters from [0-9a-w]" >&2; exit 1;
  }
  # Avoid shell-interpreting the secret: systemd EnvironmentFile is not sourced as code.
  # Restrict the accepted API URL and bot name to safe printable characters.
  [[ "$API_URL" =~ ^https://[A-Za-z0-9._:/?-]+$ ]] || {
    echo "Unexpected characters in API URL" >&2; exit 1;
  }
  [[ "$BOT_USER" =~ ^[A-Za-z0-9_.@-]+$ ]] || {
    echo "Unexpected characters in BotPassword username" >&2; exit 1;
  }
  printf 'WIKIMEDICA_SOURCE_DIR=%s\nWIKIMEDICA_OUTPUT_DIR=%s\nWIKIMEDICA_GIT_URL=%s\nWIKI_PRODUCTION_API_URL=%s\nWIKI_PRODUCTION_BOT_USER=%s\nWIKI_PRODUCTION_BOT_PASSWORD=%s\n' \
    "$SOURCE_DIR" /var/lib/wikimedica-pull "$REPO_URL" \
    "$API_URL" "$BOT_USER" "$BOT_PASS" > "$ENV_FILE"
  chmod 0600 "$ENV_FILE"
  unset BOT_PASS
fi

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
EnvironmentFile=/etc/wikimedica/github-pull.env
WorkingDirectory=/opt/wikimedica-source
ExecStart=/bin/bash /opt/wikimedica-source/infra/deploy/pull-content-from-github.sh --env production --mode beta-import
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
set -a
# Contains only validated BotPassword credentials and fixed source directory.
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
/bin/bash "$SOURCE_DIR/infra/deploy/pull-content-from-github.sh" \
  --env production --mode beta-import --only arterielle-hypertonie

echo
echo "Success. Check the article at https://wikimedica.info/index.php?title=Arterielle_Hypertonie"
echo "Future schedules: systemctl list-timers wikimedica-beta-sync.timer"
echo "Logs: journalctl -u wikimedica-beta-sync.service --no-pager -n 80"
