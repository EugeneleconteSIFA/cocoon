# Déploiement Cocon sur le VPS

Guide pour l’**étape 6** du [ROADMAP](../ROADMAP.md). Stack : Ubuntu, Nginx, systemd, Certbot, SQLite.

## Prérequis

- VPS Ubuntu avec Nginx (Hostinger OK)
- **Avec domaine** : sous-domaine en DNS → IP du VPS (`jttof.tondomaine.fr`)
- **Sans domaine** : accès direct `http://IP:port/` — voir [Accès par IP seule](#accès-par-ip-seule-sans-domaine)
- Repo Git accessible depuis le VPS (GitHub, ou `rsync` depuis ta machine)
- Clés API dans `backend/.env` (TMDb + Google Places)
- **Google Maps** : restreindre la clé par **IP du VPS** dans Google Cloud Console

### Lieux : erreur 403 / 502 sur `/api/search/place`

Le backend appelle **Places API (New)** (`places.googleapis.com/v1`), pas l’ancienne « Places API ».

Dans [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services :

1. **Activer** : *Places API (New)* (et la facturation du projet).
2. **Credentials** → ta clé `GOOGLE_MAPS_API_KEY` :
   - *Application restrictions* → **IP addresses** → `168.231.85.64` (IPv4 du VPS).
   - Le VPS sort aussi en IPv6 (`2a02:4780:7:753::1`) — soit l’ajouter dans Google, soit laisser le backend forcer l’IPv4 (déjà le cas depuis `gplaces.py`).
   - *API restrictions* → inclure au minimum **Places API (New)**.
3. Sur le VPS : `grep GOOGLE_MAPS_API_KEY /opt/jttof/backend/.env` — la clé doit être celle du même projet.
4. Redémarrer : `sudo systemctl restart jttof`, puis tester :
   `curl -s "https://cocon.sbs/api/search/place?q=paris" | head -c 200`

## Accès par IP seule (sans domaine)

Pas de Certbot ni HTTPS pour l’instant — **HTTP uniquement** (mot de passe Basic Auth quand même).

**Choisir un port public** (ouvert dans le pare-feu Hostinger) :

```bash
ss -tlnp | grep -E ':80 |:8080 '   # voir ce qui est déjà pris
```

| Port | URL depuis le téléphone |
|------|-------------------------|
| `80` | `http://168.231.85.64/` |
| `8080` | `http://168.231.85.64:8080/` |

Sur le VPS (exemple port **80**) :

```bash
cd /opt/jttof && git pull

COCON_PORT=80   # ou 8080 si le 80 est occupé

sudo sed "s/COCON_PORT/${COCON_PORT}/g" deploy/nginx-jttof-ip.conf \
  | sudo tee /etc/nginx/sites-available/jttof
sudo ln -sf /etc/nginx/sites-available/jttof /etc/nginx/sites-enabled/jttof

# Retirer l'ancienne config cassée (443 sans certificat) si besoin
sudo rm -f /etc/nginx/sites-enabled/default   # seulement si tu n'as pas d'autre site sur ce VPS

sudo htpasswd -c /etc/nginx/.htpasswd-jttof cocon   # si pas déjà fait
sudo nginx -t && sudo systemctl reload nginx

sudo systemctl enable --now jttof
curl -s http://127.0.0.1:8765/api/health
```

Puis dans le **panneau Hostinger** : autoriser le port TCP choisi (80 ou 8080) pour le VPS.

> Quand tu auras un domaine plus tard : `deploy/nginx-jttof.conf` + `certbot --nginx`.

## 1. Cloner le projet

```bash
sudo mkdir -p /opt/jttof
sudo chown "$USER":"$USER" /opt/jttof   # ou clone direct en root puis chown jttof

cd /opt/jttof
git clone https://github.com/EugeneleconteSIFA/cocoon.git .
# ou depuis ton Mac :
# rsync -avz --exclude .venv --exclude data --exclude backend/.env \
#   "./JTTOF (just the two of us)/" user@vps:/opt/jttof/
```

## 2. Variables d’environnement

```bash
cp backend/.env.example backend/.env
nano backend/.env
```

Minimum en production :

```env
TMDB_API_KEY=...
TMDB_READ_TOKEN=...          # optionnel si clé seule suffit
GOOGLE_MAPS_API_KEY=...
APP_ENV=production
```

## 3. Installation automatique

```bash
cd /opt/jttof
chmod +x deploy/*.sh
sudo COCON_DOMAIN=jttof.tondomaine.fr bash deploy/setup-server.sh
```

Sans domaine dans la commande, le script installe Python/systemd/cron et affiche les étapes Nginx à faire à la main.

## 4. Basic Auth (vous deux)

```bash
sudo htpasswd -c /etc/nginx/.htpasswd-jttof cocon
# Ajouter un 2e utilisateur : sudo htpasswd /etc/nginx/.htpasswd-jttof copine
```

Le navigateur demandera identifiant / mot de passe avant d’afficher Cocon.

## 5. Nginx puis HTTPS (Certbot)

La config Nginx démarre en **HTTP seul** (pas de bloc `443` vide — sinon `nginx -t` échoue avant Certbot).

```bash
# Remplacer TON_VRAI_DOMAINE (pas le placeholder TONDOMAINE.fr)
sudo sed "s/COCON_DOMAIN/TON_VRAI_DOMAINE/g" /opt/jttof/deploy/nginx-jttof.conf | sudo tee /etc/nginx/sites-available/jttof
sudo ln -sf /etc/nginx/sites-available/jttof /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Certbot ajoute HTTPS tout seul
sudo certbot --nginx -d TON_VRAI_DOMAINE
```

## 6. Démarrer / vérifier

```bash
sudo systemctl start jttof
sudo systemctl status jttof
curl -s http://127.0.0.1:8765/api/health
```

Depuis ton téléphone : `https://jttof.tondomaine.fr/` (avec Basic Auth).

## Mises à jour

```bash
cd /opt/jttof
sudo bash deploy/update.sh
```

(`chown jttof` + `git pull` + `pip install` + `systemctl restart jttof`)

Si `Permission denied` sur `.git/` (clone fait en root) :

```bash
chown -R jttof:jttof /opt/jttof
git config --global --add safe.directory /opt/jttof
cd /opt/jttof && sudo bash deploy/update.sh
```

## Fichiers utiles

| Fichier | Rôle |
|---------|------|
| `deploy/jttof.service` | Service systemd |
| `deploy/nginx-jttof.conf` | Nginx + domaine + Certbot (plus tard) |
| `deploy/nginx-jttof-ip.conf` | Nginx + IP seule, HTTP, sans SSL |
| `deploy/backup-db.sh` | Sauvegarde SQLite (cron 3h) |
| `deploy/setup-server.sh` | Première install |
| `deploy/update.sh` | Mise à jour rapide |

## SSL : ERR_CERT_COMMON_NAME_INVALID sur cocon.sbs

Le certificat doit couvrir **cocon.sbs** et **www.cocon.sbs** :

```bash
sudo certbot certificates   # Domains: cocon.sbs www.cocon.sbs
sudo certbot --nginx -d cocon.sbs -d www.cocon.sbs --expand
sudo certbot install --cert-name www.cocon.sbs
sudo nginx -t && sudo systemctl reload nginx
```

Vérification :

```bash
echo | openssl s_client -connect cocon.sbs:443 -servername cocon.sbs 2>/dev/null \
  | openssl x509 -noout -ext subjectAltName
# → DNS:cocon.sbs, DNS:www.cocon.sbs
```

Si Certbot ne trouve pas le vhost, réappliquer la config du repo :

```bash
sudo sed "s/COCON_DOMAIN/cocon.sbs/g" /opt/jttof/deploy/nginx-jttof.conf \
  | sudo tee /etc/nginx/sites-available/jttof
sudo ln -sf /etc/nginx/sites-available/jttof /etc/nginx/sites-enabled/jttof
sudo nginx -t && sudo systemctl reload nginx
sudo certbot install --cert-name www.cocon.sbs
```

## Dépannage

```bash
sudo journalctl -u jttof -f          # logs app
sudo tail -f /var/log/nginx/jttof-error.log
ls -la /opt/jttof/data/jttof.db      # base SQLite
sudo -u jttof /opt/jttof/.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765
```

## Restaurer une sauvegarde

```bash
sudo systemctl stop jttof
cp /opt/jttof/backups/jttof-2026-05-16.db /opt/jttof/data/jttof.db
sudo chown jttof:jttof /opt/jttof/data/jttof.db
sudo systemctl start jttof
```
