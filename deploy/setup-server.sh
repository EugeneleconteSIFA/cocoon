#!/usr/bin/env bash
# Première installation sur le VPS Ubuntu (root ou sudo)
# Usage : depuis le repo cloné dans /opt/jttof
#   cd /opt/jttof && sudo bash deploy/setup-server.sh

set -euo pipefail

INSTALL_DIR="${JTTOF_DIR:-/opt/jttof}"
DOMAIN="${COCON_DOMAIN:-}"

echo "==> Cocon — setup serveur (${INSTALL_DIR})"

if [[ $EUID -ne 0 ]]; then
  echo "Lance ce script avec sudo."
  exit 1
fi

# Paquets système
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip nginx apache2-utils certbot python3-certbot-nginx git

# Utilisateur dédié
if ! id -u jttof &>/dev/null; then
  useradd --system --home "$INSTALL_DIR" --shell /usr/sbin/nologin jttof
fi

mkdir -p "$INSTALL_DIR/data" "$INSTALL_DIR/backups"
chown -R jttof:jttof "$INSTALL_DIR"

# Venv + dépendances
if [[ ! -d "$INSTALL_DIR/.venv" ]]; then
  sudo -u jttof python3 -m venv "$INSTALL_DIR/.venv"
fi
sudo -u jttof "$INSTALL_DIR/.venv/bin/pip" install --upgrade pip -q
sudo -u jttof "$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/backend/requirements.txt" -q

# .env production
if [[ ! -f "$INSTALL_DIR/backend/.env" ]]; then
  cp "$INSTALL_DIR/backend/.env.example" "$INSTALL_DIR/backend/.env"
  sed -i 's/^APP_ENV=.*/APP_ENV=production/' "$INSTALL_DIR/backend/.env"
  chown jttof:jttof "$INSTALL_DIR/backend/.env"
  chmod 600 "$INSTALL_DIR/backend/.env"
  echo ""
  echo "⚠️  Édite $INSTALL_DIR/backend/.env (clés TMDb, Google) avant de démarrer :"
  echo "    sudo nano $INSTALL_DIR/backend/.env"
  echo ""
fi

# systemd
cp "$INSTALL_DIR/deploy/jttof.service" /etc/systemd/system/jttof.service
systemctl daemon-reload
systemctl enable jttof

# Backup cron (3h du matin, rotation 30 jours)
chmod +x "$INSTALL_DIR/deploy/backup-db.sh" "$INSTALL_DIR/deploy/update.sh"
CRON_LINE="0 3 * * * ${INSTALL_DIR}/deploy/backup-db.sh >> /var/log/jttof-backup.log 2>&1"
if ! crontab -u root -l 2>/dev/null | grep -qF "backup-db.sh"; then
  (crontab -u root -l 2>/dev/null; echo "$CRON_LINE") | crontab -u root -
fi

# Nginx
if [[ -z "$DOMAIN" ]]; then
  echo ""
  echo "Pour Nginx + HTTPS, relance avec le domaine :"
  echo "  COCON_DOMAIN=jttof.tondomaine.fr sudo bash deploy/setup-server.sh"
  echo ""
  echo "Puis manuellement :"
  echo "  sudo sed 's/COCON_DOMAIN/jttof.tondomaine.fr/g' deploy/nginx-jttof.conf | sudo tee /etc/nginx/sites-available/jttof"
  echo "  sudo ln -sf /etc/nginx/sites-available/jttof /etc/nginx/sites-enabled/"
  echo "  sudo htpasswd -c /etc/nginx/.htpasswd-jttof cocon"
  echo "  sudo certbot --nginx -d jttof.tondomaine.fr"
else
  sed "s/COCON_DOMAIN/${DOMAIN}/g" "$INSTALL_DIR/deploy/nginx-jttof.conf" > /etc/nginx/sites-available/jttof
  ln -sf /etc/nginx/sites-available/jttof /etc/nginx/sites-enabled/jttof
  if [[ ! -f /etc/nginx/.htpasswd-jttof ]]; then
    echo "Crée le mot de passe Basic Auth (vous deux) :"
    htpasswd -c /etc/nginx/.htpasswd-jttof cocon
  fi
  nginx -t
  systemctl reload nginx
  echo "Lance Certbot si pas encore fait : sudo certbot --nginx -d ${DOMAIN}"
fi

echo ""
echo "==> Démarrer l'app : sudo systemctl start jttof"
echo "    Logs         : sudo journalctl -u jttof -f"
echo "    Santé local  : curl -s http://127.0.0.1:8765/api/health"
