#!/usr/bin/env bash
# Mise à jour après git pull
# Usage : cd /opt/jttof && sudo bash deploy/update.sh

set -euo pipefail

INSTALL_DIR="${JTTOF_DIR:-/opt/jttof}"
JTTOF_USER="${JTTOF_USER:-jttof}"

cd "$INSTALL_DIR"

# Corrige les droits si le clone a été fait en root
if [[ $EUID -eq 0 ]] && id -u "$JTTOF_USER" &>/dev/null; then
  chown -R "${JTTOF_USER}:${JTTOF_USER}" "$INSTALL_DIR"
  sudo -u "$JTTOF_USER" git config --global --add safe.directory "$INSTALL_DIR" 2>/dev/null || true
fi

if [[ -d .git ]]; then
  if id -u "$JTTOF_USER" &>/dev/null; then
    sudo -u "$JTTOF_USER" git -C "$INSTALL_DIR" pull --ff-only
  else
    git pull --ff-only
  fi
fi

if id -u "$JTTOF_USER" &>/dev/null; then
  sudo -u "$JTTOF_USER" "$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/backend/requirements.txt" -q
else
  "$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/backend/requirements.txt" -q
fi

systemctl restart jttof
sleep 1
curl -sf "http://127.0.0.1:8765/api/health" | head -c 200
echo ""
echo "$(date -Is) — jttof redémarré OK"
