# Cocon

> *Notre carnet à deux.*

Petite appli web personnelle pour deux personnes. Quatre piliers : films & séries à voir, lieux à visiter, activités à faire, recettes à cuisiner. Ajout en deux clics, données enrichies automatiquement depuis TMDb et Google Maps.

---

## Démarrer en local

Pré-requis : Python 3.10+, et un fichier `backend/.env` correctement rempli (copier depuis `backend/.env.example` et coller les clés API).

```bash
# 1. Créer le venv et installer les dépendances
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r backend/requirements.txt

# 2. Lancer le serveur (forme robuste, marche même avec Anaconda dans le PATH)
.venv/bin/python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8765
```

> ⚠️ Si tu as Anaconda/Miniconda installé, ne te contente pas de `source .venv/bin/activate`
> puis `uvicorn ...` : conda peut réinjecter son propre Python en tête du PATH et faire
> tourner le serveur avec ses dépendances obsolètes (SQLAlchemy < 2 notamment).
> La forme `.venv/bin/python -m uvicorn ...` bypass le PATH et garantit le bon interpréteur.

Une fois démarré :
- API : http://127.0.0.1:8765/api/health → `{"ok": true, "app": "cocon", ...}`
- Doc Swagger interactive : http://127.0.0.1:8765/docs
- Frontend (quand il existera) : http://127.0.0.1:8765/

La base SQLite est créée automatiquement dans `data/jttof.db` au premier démarrage.

---

## Arborescence

```
Cocon/
├── README.md             ← ce fichier
├── CLAUDE.md             ← instructions projet pour Claude
├── VISION.md             ← pourquoi on construit ça
├── FEATURES.md           ← les 4 piliers en détail
├── STACK.md              ← architecture technique
├── DA.md                 ← direction artistique (verrouillée)
├── ROADMAP.md            ← plan d'exécution
├── DA-OPTIONS.md         ← archive (les 3 propositions de DA)
├── bulle.html            ← archive (première tentative)
├── .gitignore
├── backend/
│   ├── main.py           ← entrée FastAPI
│   ├── database.py       ← engine SQLite + sessions
│   ├── models.py         ← modèles SQLAlchemy
│   ├── schemas.py        ← schémas Pydantic
│   ├── routers/
│   │   ├── culture.py    ← /api/culture
│   │   ├── lieux.py      ← /api/lieux
│   │   ├── activites.py  ← /api/activites
│   │   ├── cuisine.py    ← /api/cuisine
│   │   └── search.py     ← /api/search/{culture,place,url}
│   ├── services/
│   │   ├── tmdb.py       ← client TMDb
│   │   ├── gplaces.py    ← client Google Places
│   │   └── og_scraper.py ← parser Open Graph
│   ├── requirements.txt
│   ├── .env              ← clés API (gitignored)
│   └── .env.example
├── frontend/
│   ├── index.html        ← coquille mobile-first
│   ├── style.css         ← DA Cocon × vintage chic papier
│   └── app.js            ← routeur d'onglets vanilla
└── data/
    └── jttof.db          ← créée au premier démarrage
```

---

## État d'avancement

Voir [ROADMAP.md](ROADMAP.md) pour le détail des étapes.

- [x] Étape 0 — Cadrage (vision, DA, clés API, VPS)
- [x] Étape 1 — Backend minimal : FastAPI + SQLite + CRUD des 4 piliers
- [x] Étape 2 — Services externes (TMDb, Google Places, Open Graph)
- [x] Étape 3 — Frontend (HTML/CSS/JS, DA Cocon × vintage chic papier)
- [ ] Étape 4 — Premier pilier complet (Culture)
- [ ] Étape 5 — Les trois autres piliers
- [ ] Étape 6 — Déploiement sur le VPS
- [ ] Étape 7 — Polish

---

## Conventions

- **Soft delete partout** : `DELETE` met `archived=true`, jamais de hard delete en V1.
- **Champs partagés** par tous les piliers : `id`, `note`, `loved`, `archived`, `created_at`.
- **JSON pour les listes** (genres, acteurs, tags) — stocké en TEXT côté SQLite.
- **Dates en ISO 8601 UTC** stockées en TEXT.
- **Auth** : pas en V1, à brancher avant déploiement (Basic Auth Nginx ou token partagé).

---

## Endpoints disponibles (étape 1)

Pour chaque pilier (`culture`, `lieux`, `activites`, `cuisine`) :

| Méthode | Route                       | Effet                          |
|---------|-----------------------------|--------------------------------|
| GET     | `/api/{pilier}`             | Liste (filtre `archived=false` par défaut) |
| POST    | `/api/{pilier}`             | Crée une nouvelle entrée       |
| GET     | `/api/{pilier}/{id}`        | Récupère une entrée            |
| PATCH   | `/api/{pilier}/{id}`        | Met à jour partiellement       |
| DELETE  | `/api/{pilier}/{id}`        | Soft delete (archived=true)    |

Plus :
- `GET /api/health` — sanity check

La spécification OpenAPI complète est sur `/docs`.
