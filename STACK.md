# STACK.md

## Choix : simple, mais "vrai" backend

Backend Python **FastAPI** + base **SQLite**, frontend HTML/CSS/JS vanilla servi par FastAPI. Hébergement sur le **VPS d'Eugène**.

Pourquoi ce choix plutôt que tout-en-localStorage :
- Synchro automatique entre les deux téléphones / desktop (un seul backend, une seule base).
- Les clés API (TMDb, Google Places) restent **côté serveur** — pas exposées dans le navigateur.
- Pas de problèmes CORS pour parser des liens Marmiton / Instagram : c'est le backend qui fetch.
- SQLite suffit largement : 2 utilisateurs, quelques milliers de lignes max.

---

## Arborescence projet

```
JTTOF/
├── backend/
│   ├── main.py              ← entrée FastAPI
│   ├── database.py          ← connexion SQLite + init
│   ├── models.py            ← schémas SQLAlchemy
│   ├── schemas.py           ← schémas Pydantic
│   ├── routers/
│   │   ├── culture.py       ← /api/culture (films & séries)
│   │   ├── lieux.py         ← /api/lieux
│   │   ├── activites.py     ← /api/activites
│   │   ├── cuisine.py       ← /api/cuisine
│   │   └── search.py        ← /api/search (proxy TMDb + Google Places)
│   ├── services/
│   │   ├── tmdb.py          ← appels TMDb
│   │   ├── gplaces.py       ← appels Google Places
│   │   └── og_scraper.py    ← parser Open Graph (recettes)
│   ├── .env                 ← clés API (jamais commité)
│   └── requirements.txt
├── frontend/
│   ├── index.html           ← une seule page
│   ├── app.js               ← vanilla JS
│   ├── style.css
│   └── assets/              ← SVG, icônes, illustrations
├── data/
│   └── jttof.db             ← SQLite (créé au runtime)
├── CLAUDE.md
├── VISION.md
├── FEATURES.md
├── STACK.md
├── DA-OPTIONS.md
└── ROADMAP.md
```

---

## Backend — FastAPI

### Dépendances (minimales)
```
fastapi
uvicorn[standard]
sqlalchemy
pydantic
python-dotenv
httpx           # appels TMDb / Google Places
beautifulsoup4  # parsing Open Graph pour recettes
```

### Endpoints principaux

#### Recherche / proxy externe
- `GET /api/search/movie?q=...` → proxy TMDb `/search/multi`, renvoie une liste normalisée.
- `GET /api/search/place?q=...` → proxy Google Places Text Search, renvoie nom + adresse + photo URL + note.
- `POST /api/search/url` → reçoit `{ "url": "https://..." }`, fetch le HTML, parse les meta Open Graph, renvoie `{ title, image, description }`.

#### CRUD par pilier
Chaque pilier a le même schéma d'endpoints :
- `GET /api/{pilier}` → liste tout
- `POST /api/{pilier}` → ajoute (le frontend envoie l'objet déjà enrichi par /api/search)
- `PATCH /api/{pilier}/{id}` → édite (cocher "vu ensemble", changer une note…)
- `DELETE /api/{pilier}/{id}` → archive (soft delete, on garde en base avec un flag)

Piliers : `culture`, `lieux`, `activites`, `cuisine`.

### Authentification
Pour la V1, l'app est sur le VPS d'Eugène, derrière un sous-domaine (`jttof.eugene.tld`). Deux options :
1. **Basic Auth** au niveau Nginx (utilisateur/mdp partagé entre les deux). Suffisant.
2. **Token simple** stocké en variable d'env, à passer en header. Un peu plus propre, à peine plus de code.

Pas d'inscription, pas de mot de passe oublié, pas de session compliquée.

---

## Base de données — SQLite

### Schéma (simplifié)

Une table par pilier, plus une table commune `souvenirs` pour les éléments "vus/faits ensemble" avec date.

#### `culture`
```sql
id INTEGER PK
type TEXT          -- 'movie' | 'tv'
tmdb_id INTEGER
title TEXT
year INTEGER
poster_url TEXT
genres TEXT        -- JSON array
actors TEXT        -- JSON array (top 3)
overview TEXT
rating REAL        -- note TMDb
note TEXT          -- note perso
seen_at TEXT       -- date "vu ensemble" (null si pas encore vu)
loved INTEGER      -- 0 | 1
archived INTEGER   -- 0 | 1
created_at TEXT
```

#### `lieux`
```sql
id INTEGER PK
gplaces_id TEXT
name TEXT
address TEXT
city TEXT
section TEXT       -- 'ville' | 'autre_ville' | 'voyage'
category TEXT      -- 'restaurant' | 'cafe' | 'musée'...
photo_url TEXT
rating REAL
maps_url TEXT
note TEXT
visited_at TEXT
loved INTEGER
archived INTEGER
created_at TEXT
```

#### `activites`
```sql
id INTEGER PK
title TEXT
emoji TEXT
tags TEXT          -- JSON array : 'intérieur', 'gratuit'…
note TEXT
done_at TEXT
loved INTEGER
archived INTEGER
created_at TEXT
```

#### `cuisine`
```sql
id INTEGER PK
title TEXT
source_url TEXT
image_url TEXT
tags TEXT          -- JSON array
note TEXT
cooked_at TEXT
loved INTEGER
archived INTEGER
created_at TEXT
```

### Sauvegardes
- SQLite = un seul fichier (`data/jttof.db`).
- Cron quotidien sur le VPS : `cp jttof.db backups/jttof-$(date +%F).db` + rotation 30 jours.
- Bouton "Exporter tout en JSON" dans l'app pour download manuel.

---

## Frontend — toujours vanilla

Le choix de tout passer côté serveur ne change pas le front : **un seul `index.html`** + un `app.js` qui consomme l'API REST. Pas de framework.

### Pourquoi pas un framework
- C'est une app à 4 onglets et ~5 vues. Vanilla suffit.
- Aucune envie de gérer un build, du tooling, des dépendances qui périment.
- La DA cocooning passe par du CSS soigné, plus que par de la logique d'interface complexe.

---

## APIs externes (côté backend uniquement)

### TMDb
- Clé API gratuite : https://www.themoviedb.org/settings/api
- Stockée dans `backend/.env` (`TMDB_API_KEY=...`)
- Appels via `httpx` dans `services/tmdb.py`.
- Posters servis directement depuis `image.tmdb.org` (pas besoin de proxy).

### Google Places API
- Free tier suffisant pour 2 utilisateurs.
- Restreindre la clé par IP (celle du VPS) côté Google Cloud Console.
- Stockée dans `backend/.env` (`GOOGLE_MAPS_API_KEY=...`)
- **Fallback** si la facturation Google fait peur : Nominatim (OpenStreetMap, gratuit, sans clé) + photo via Unsplash Source.

### Open Graph (recettes)
- Le backend fait le fetch + parse avec BeautifulSoup → renvoie au front un JSON propre.
- Pas de CORS à gérer puisque c'est server-to-server.

---

## Déploiement sur le VPS

### Stack VPS supposée
- Ubuntu/Debian, Nginx en reverse-proxy, Python 3.11+, systemd pour les services.
- Domaine : sous-domaine type `jttof.{domaine-eugene}`.

### Setup une fois
1. Clone du repo dans `/opt/jttof/`.
2. `python -m venv .venv` + `pip install -r backend/requirements.txt`.
3. Service systemd `jttof.service` qui lance `uvicorn backend.main:app --host 127.0.0.1 --port 8765`.
4. Bloc Nginx qui :
   - Sert `/frontend/` en static.
   - Proxy `/api/*` vers `http://127.0.0.1:8765`.
   - Bascule sur HTTPS via Certbot (Let's Encrypt).
   - Basic Auth global (htpasswd) si on choisit cette option.
5. Cron de backup SQLite.

### Mises à jour
`git pull` + `systemctl restart jttof`. C'est tout.

---

## Compatibilité visée
- Safari iOS (priorité 1, 90 % de l'usage).
- Chrome desktop (priorité 2).
- Pas de support legacy.

## Ce qu'on NE met PAS (V1)
- Pas de React/Vue.
- Pas de Docker (le VPS roule directement).
- Pas de migrations Alembic — SQLite gère un schéma simple, on edite à la main si besoin.
- Pas de PWA / service worker — à envisager si l'usage prend.
- Pas de tests automatisés pour la V1 — c'est un projet perso à 2 utilisateurs, le coût/bénéfice ne le justifie pas.
