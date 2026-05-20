#!/usr/bin/env bash
# Diagnostic Google Places (New) — à lancer sur le VPS en root ou jttof.
# Usage : sudo bash deploy/diagnose-google.sh

set -euo pipefail
cd "$(dirname "$0")/.."
ENV_FILE="${ENV_FILE:-backend/.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "❌ $ENV_FILE introuvable"
  exit 1
fi

# shellcheck disable=SC1090
set -a
source "$ENV_FILE"
set +a

KEY="${GOOGLE_MAPS_API_KEY:-}"
if [[ -z "$KEY" ]]; then
  echo "❌ GOOGLE_MAPS_API_KEY vide dans $ENV_FILE"
  exit 1
fi

echo "✓ Clé présente (${#KEY} caractères)"
echo "→ IP publique du VPS (pour restriction Google) :"
curl -sS --max-time 5 https://api.ipify.org || echo "(ipify injoignable)"
echo ""

echo "→ Appel direct Places API (New)…"
RESP=$(curl -sS -w "\n__HTTP__%{http_code}" -X POST "https://places.googleapis.com/v1/places:searchText" \
  -H "Content-Type: application/json" \
  -H "X-Goog-Api-Key: ${KEY}" \
  -H "X-Goog-FieldMask: places.displayName,places.id" \
  -d '{"textQuery":"paris","languageCode":"fr"}')

HTTP=$(echo "$RESP" | sed -n 's/^__HTTP__//p')
BODY=$(echo "$RESP" | sed '/^__HTTP__/d')

echo "HTTP $HTTP"
echo "$BODY" | head -c 1200
echo ""

if [[ "$HTTP" == "200" ]]; then
  echo ""
  echo "✅ Google OK — si l'app échoue encore : sudo systemctl restart jttof"
  exit 0
fi

echo ""
echo "─── Pistes si 403 ───"
echo "1. Google Cloud → APIs : activer « Places API (New) » (pas seulement Places API legacy)"
echo "2. Facturation activée sur le projet"
echo "3. Credentials → clé → Restrictions API : inclure Places API (New)"
echo "4. Restrictions appli → IP : ajouter l'IP affichée ci-dessus (pas « sites web » seul)"
echo "5. Vérifier que la clé dans backend/.env est bien celle du même projet"
exit 1
