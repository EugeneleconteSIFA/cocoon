# CLAUDE.md — Instructions projet

## Contexte
Petite appli web personnelle pour Eugène et sa copine, baptisée **Cocon** (*notre carnet à deux*). Quatre piliers de vie partagée :
1. **Culture** — films & séries à voir ensemble
2. **Lieux** — endroits où aller (par ville, dans notre ville, idées de voyage)
3. **Activités** — choses à faire à deux
4. **Cuisine** — recettes / trucs à cuisiner

## Tentative précédente
Une première version a été tentée avec Sonnet 4.6 (`bulle.html`) : trop de formulaires, DA trop terracotta/sage, pas assez cocooning. **On repart sur de meilleures bases.**

## Principes directeurs (NON négociables)

### 1. Hyper intuitif
- L'utilisateur ne doit JAMAIS remplir un formulaire avec 10 champs.
- Maximum 1-2 actions pour ajouter quelque chose.
- L'app doit deviner / récupérer les infos automatiquement.

### 2. Automatisé
- **Films/Séries** → API TMDb. L'utilisateur tape 3 lettres, voit les vignettes, clique, c'est ajouté avec titre/poster/genre/acteurs/synopsis.
- **Lieux** → Google Places API. L'utilisateur tape un nom, voit la suggestion avec photo/adresse/note, clique, c'est ajouté.
- **Activités / Cuisine** → saisie libre courte (pas besoin d'API), mais avec suggestions intelligentes.

### 3. Chaleureux & cocooning, tons roses
- DA verrouillée dans `DA.md` : **Cocon × vintage chic papier**. C'est LA référence visuelle.
- `DA-OPTIONS.md` est archivé (historique des 3 options présentées) — ne plus s'y référer.
- **Pas de terracotta, pas de sage, pas de couleurs froides.** Crème rosé, ivoire, vieux rose, pivoine, cuivre.
- Typographie 100 % serif (DM Serif Display + Lora), arrondis généreux, ombres invisibles, filets dorés discrets, tampons rotatifs pour les états "vu/fait ensemble".

### 4. Stack simple mais "vraie"
- Backend **FastAPI** + **SQLite**, hébergé sur le VPS d'Eugène.
- Frontend **vanilla JS** (un seul `index.html`), servi par FastAPI.
- Clés API (TMDb, Google Places) côté serveur, jamais exposées au navigateur.

## Stack
Voir `STACK.md`. TL;DR : FastAPI/SQLite côté serveur, HTML/CSS/JS vanilla côté client, déployé sur le VPS via systemd + Nginx.

## Ordre de bataille
Voir `ROADMAP.md`.

## Workflow avec Claude
- Toujours lire les .md d'abord pour se remettre dans le contexte (`VISION.md`, `FEATURES.md`, `STACK.md`, `DA.md`, `ROADMAP.md`).
- La DA est verrouillée dans `DA.md`. Toute déviation doit être justifiée explicitement ou corrigée.
- Tout livrable final va dans le dossier projet, accessible via `computer://`.
- Ne jamais ressortir l'ancien `bulle.html` ni `DA-OPTIONS.md` — archives de pistes abandonnées.
