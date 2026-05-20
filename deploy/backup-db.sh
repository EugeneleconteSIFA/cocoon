#!/usr/bin/env bash
# Sauvegarde quotidienne SQLite + rotation 30 jours
# Cron : 0 3 * * * /opt/jttof/deploy/backup-db.sh >> /var/log/jttof-backup.log 2>&1

set -euo pipefail

INSTALL_DIR="${JTTOF_DIR:-/opt/jttof}"
DB="${INSTALL_DIR}/data/jttof.db"
BACKUP_DIR="${INSTALL_DIR}/backups"

if [[ ! -f "$DB" ]]; then
  echo "$(date -Is) — pas de base à sauvegarder ($DB)"
  exit 0
fi

mkdir -p "$BACKUP_DIR"
DEST="${BACKUP_DIR}/jttof-$(date +%F).db"
cp "$DB" "$DEST"
echo "$(date -Is) — sauvegarde OK → $DEST"

# Rotation : supprimer les backups de plus de 30 jours
find "$BACKUP_DIR" -name 'jttof-*.db' -type f -mtime +30 -delete
