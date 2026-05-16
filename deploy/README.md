# Déploiement Cocon sur le VPS

Guide pour l’**étape 6** du [ROADMAP](../ROADMAP.md). Stack : Ubuntu, Nginx, systemd, Certbot, SQLite.

## Prérequis

- VPS Ubuntu avec Nginx (Hostinger OK)
- Sous-domaine pointant vers le VPS (`jttof.tondomaine.fr`)
- Repo Git accessible depuis le VPS (GitHub, ou `rsync` depuis ta machine)
- Clés API dans `backend/.env` (TMDb + Google Places)
- **Google Maps** : restreindre la clé par **IP du VPS** dans Google Cloud Console

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

(`git pull` + `pip install` + `systemctl restart jttof`)

## Fichiers utiles

| Fichier | Rôle |
|---------|------|
| `deploy/jttof.service` | Service systemd |
| `deploy/nginx-jttof.conf` | Modèle Nginx + Basic Auth |
| `deploy/backup-db.sh` | Sauvegarde SQLite (cron 3h) |
| `deploy/setup-server.sh` | Première install |
| `deploy/update.sh` | Mise à jour rapide |

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
