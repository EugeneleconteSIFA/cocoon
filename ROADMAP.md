# ROADMAP.md — Ordre de bataille

Étapes en séquence. On ne passe pas à la suivante avant d'avoir validé la précédente.

---

## Étape 0 — Cadrage ✅
- [x] Lire `CLAUDE.md`, `VISION.md`, `FEATURES.md`, `STACK.md`.
- [x] Lire `DA-OPTIONS.md`.
- [x] **Nom + DA choisis** : *Cocon* × vintage chic papier (verrouillé dans `DA.md`).
- [x] Clés API TMDb (key + read token) stockées dans `backend/.env`.
- [x] Clé Google Maps Platform stockée dans `backend/.env` (à restreindre par IP avant déploiement).
- [x] VPS Hostinger validé : Ubuntu, Nginx 1.24, Python 3.12, accès root SSH.
- [x] `.gitignore` en place, `.env` exclu.

**Sortie de l'étape 0 :** ✅ Tout est prêt pour bâtir le backend.

---

## Étape 1 — Backend minimal qui tourne en local ✅
- [x] Arborescence `backend/` créée (main, database, models, schemas, routers/).
- [x] `requirements.txt` (FastAPI, SQLAlchemy 2.0, Pydantic v2, httpx, BS4, dotenv).
- [x] `main.py` : FastAPI + lifespan `init_db` + CORS + montage du frontend static.
- [x] `database.py` : engine SQLite, base auto-créée dans `<root>/data/jttof.db`.
- [x] `models.py` : `CocoonMixin` (id/note/loved/archived/created_at) + Culture, Lieu, Activite, Recette.
- [x] `schemas.py` : Create / Update / Read pour les 4 piliers, validation Pydantic (regex sur type, section).
- [x] CRUD complet pour chaque pilier (GET liste avec filtres, POST, GET unique, PATCH, DELETE soft).
- [x] Vérifié en sandbox via TestClient : health, create, patch, soft delete, filtre archived, filtre section lieux, validation 422, not-found 404.

**Sortie :** ✅ Backend qui démarre, base qui s'auto-init, 21 routes opérationnelles. `GET /docs` génère la spec Swagger automatiquement.

---

## Étape 2 — Connexion aux APIs externes ✅
- [x] `services/tmdb.py` : `search_multi(query)` (filtre persons + entrées sans poster) + `get_details(type, id)` (ajoute genres et top 3 acteurs).
- [x] `services/gplaces.py` : `search_text(query)` light + `get_details(place_id)` avec photo (photoUri googleusercontent.com — **clé jamais exposée au navigateur**).
- [x] `services/og_scraper.py` : `parse_url(url)` avec fallback og → twitter → `<title>` / `meta name="description"`, résolution des URLs d'image relatives.
- [x] Endpoints `/api/search/culture`, `/api/search/culture/{type}/{id}`, `/api/search/place`, `/api/search/place/{place_id}`, `/api/search/url`.
- [x] `.env` rempli (TMDb + Google Maps), `.gitignore` exclut `.env` et `data/`.
- [x] Tests : 9 scénarios passés via `httpx.MockTransport` (parsing, filtrage, mapping catégorie/ville, photo sans clé, validation FastAPI 422).

**Sortie :** ✅ Depuis Swagger ou `curl`, on peut chercher "Interstellar" et récupérer un JSON `{type, tmdb_id, title, year, poster_url, genres, actors, ...}` directement POSTable sur `/api/culture`.

---

## Étape 3 — Frontend, structure et DA ✅
- [x] `frontend/index.html` : structure mobile-first, topbar sticky avec logo `Cocon` + pivoine ornement, tabbar sticky bas, 6 icônes SVG inline (4 onglets + plus + recherche), 4 vues avec kicker + titre + état vide cocooning.
- [x] `frontend/style.css` : DA appliquée à la lettre — variables CSS (crème rosé, ivoire, pivoine, cuivre), DM Serif Display + Lora, texture papier SVG noise opacity 0.04, filets dorés tabbar, focus visibles, `prefers-reduced-motion` respecté.
- [x] `frontend/app.js` : routeur d'onglets vanilla — hash URL synchronisé, `localStorage` `cocon:lastTab` pour persistance entre rechargements, `hashchange` câblé pour back/forward, délégation d'événements propre.
- [x] FastAPI sert `/`, `/style.css`, `/app.js` via le mount static (déjà câblé en étape 1).
- [x] Vérifié via TestClient : 5 GET passent, `/api/*` toujours accessible.

**Sortie :** ✅ Coquille de l'app prête. Au prochain `uvicorn`, http://127.0.0.1:8765/ affiche un Cocon navigable, 4 onglets, états vides chaleureux, aucune logique métier — exactement comme prévu.

---

## Étape 4 — Pilier Culture (premier flux complet) ✅
- [x] Onglet Culture : grille vide + bouton « + » (état vide + FAB quand la grille est remplie).
- [x] Clic sur « + » → ouvre la barre de recherche.
- [x] Recherche live : debounce 300ms, appel `/api/search/culture?q=...`, vignettes cliquables.
- [x] Clic sur une vignette → détails TMDb → POST `/api/culture` → recharge la grille.
- [x] Tap sur une carte → bottom sheet : « Vu ensemble », « Pas pour nous », cœur adoré, notes.
- [x] Filtres Films / Séries / Tout + bouton « Tirer au sort » (overlay + pulse sur la carte).

**Sortie :** ✅ Flux Culture end-to-end en local. Prochaine étape : dupliquer la mécanique sur Lieux, Activités, Cuisine.

---

## Étape 5 — Les trois autres piliers ✅
On clone la mécanique du pilier Culture, en l'adaptant :
- [x] **Lieux** : recherche Google Places (debounce) + choix section à l'ajout + filtres + sheet + tirage au sort.
- [x] **Activités** : champ libre + emojis suggérés + tags 1-tap + liste verticale + sheet + tirage.
- [x] **Cuisine** : lien → `/api/search/url` OU titre + photo (drag&drop) + grille + tags en fiche + tirage.

**Sortie :** ✅ Les 4 piliers fonctionnent en local. Prochaine étape : déploiement VPS (§6).

---

## Étape 6 — Déploiement sur le VPS
- [x] Fichiers prêts dans `deploy/` : `jttof.service`, `nginx-jttof.conf`, `setup-server.sh`, `update.sh`, `backup-db.sh`, `README.md`.
- [ ] **Sur le VPS** : cloner le repo dans `/opt/jttof/`.
- [ ] **Sur le VPS** : `backend/.env` (clés API, `APP_ENV=production`), Google Maps restreint par IP VPS.
- [ ] **Sur le VPS** : `sudo COCON_DOMAIN=jttof.tondomaine.fr bash deploy/setup-server.sh`
- [ ] **Sur le VPS** : `htpasswd` (Basic Auth) + `certbot --nginx` + `systemctl start jttof`.

**Sortie :** l'app est joignable sur `https://jttof.{ton-domaine}/`, depuis le téléphone de la copine aussi.

> Guide pas à pas : [deploy/README.md](deploy/README.md)

---

## Étape 7 — Polish & quality of life
Une fois que ça tourne, et seulement après :
- [ ] État vides soignés (illustration douce, micro-copie).
- [ ] Animations légères (apparition de carte, tirage au sort).
- [ ] Onglet/section **Souvenirs** (timeline des éléments cochés "ensemble").
- [ ] Bouton export JSON + import JSON.
- [ ] Mode sombre ? (optionnel, à juger une fois la version claire stable).
- [ ] PWA / icône d'app sur écran d'accueil iOS.

---

## Ce qu'on ne fait PAS (encore)
- Authentification fine (login/mdp par utilisateur, profils).
- Synchronisation multi-base.
- Notifications push.
- Stats / analytics.
- Versions iOS/Android natives.

Tout ça revient potentiellement en V2, jamais en V1.

---

## Définition de "fait" (V1)
- On utilise l'app à deux pendant 2 semaines.
- Au moins 10 films, 10 lieux, 5 activités, 5 recettes ajoutés.
- Aucun bug bloquant.
- Aucune envie de revenir au système précédent (notes vocales et captures d'écran).

Le jour où ce score est atteint, V1 est livrée. Le reste, c'est V2.
