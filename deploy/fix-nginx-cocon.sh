#!/usr/bin/env bash
# Réinstalle le vhost Nginx Cocon (cocon.sbs + www) avec le certificat Let's Encrypt.
# Usage : cd /opt/jttof && sudo bash deploy/fix-nginx-cocon.sh

set -euo pipefail

DOMAIN="${COCON_DOMAIN:-cocon.sbs}"
INSTALL_DIR="${JTTOF_DIR:-/opt/jttof}"
CONF_SRC="$INSTALL_DIR/deploy/nginx-jttof.conf"
CONF_DST="/etc/nginx/sites-available/jttof"

if [[ ! -f "$CONF_SRC" ]]; then
  echo "Fichier introuvable : $CONF_SRC" >&2
  exit 1
fi

if [[ ! -f "/etc/letsencrypt/live/www.${DOMAIN}/fullchain.pem" ]]; then
  echo "Certificat absent : /etc/letsencrypt/live/www.${DOMAIN}/fullchain.pem" >&2
  echo "Lance d'abord : sudo certbot --nginx -d ${DOMAIN} -d www.${DOMAIN} --expand" >&2
  exit 1
fi

if [[ -f "$CONF_DST" ]]; then
  cp -a "$CONF_DST" "${CONF_DST}.bak.$(date +%Y%m%d%H%M%S)"
fi

sed "s/COCON_DOMAIN/${DOMAIN}/g" "$CONF_SRC" > "$CONF_DST"
ln -sf "$CONF_DST" /etc/nginx/sites-enabled/jttof

echo "=== server_name dans jttof ==="
grep -E 'server_name|ssl_certificate' "$CONF_DST" || true

nginx -t
systemctl reload nginx

echo ""
echo "OK — Nginx utilise le certificat www.${DOMAIN} (SAN : ${DOMAIN} + www.${DOMAIN})"
echo "Test : curl -sI https://${DOMAIN}/api/health | head -3"
