#!/usr/bin/env bash
# Mise à jour après git pull
# Usage : cd /opt/jttof && sudo bash deploy/update.sh

set -euo pipefail

INSTALL_DIR="${JTTOF_DIR:-/opt/jttof}"

cd "$INSTALL_DIR"

if [[ -d .git ]]; then
  sudo -u jttof git pull --ff-only
fi

sudo -u jttof "$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/backend/requirements.txt" -q

systemctl restart jttof
sleep 1
curl -sf "http://127.0.0.1:8765/api/health" | head -c 200
echo ""
echo "$(date -Is) — jttof redémarré OK"
