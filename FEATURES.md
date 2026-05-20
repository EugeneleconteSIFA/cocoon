# FEATURES.md

Les 4 piliers, avec le détail du flux d'ajout. Le mot-clé partout : **AUTO**.

---

## 1. Culture — films & séries

### Flux d'ajout (le seul scénario qui compte)
1. L'utilisateur ouvre l'onglet **Culture** et clique sur un gros bouton « + ».
2. Une barre de recherche apparaît. Il tape `intere…`
3. Sous la barre, des **vignettes apparaissent en live** : *Interstellar*, *Interview*, *Intervention*… (réponse TMDb instantanée).
4. Il clique sur la bonne vignette.
5. **C'est ajouté.** Affiché dans la grille avec :
   - Poster (auto)
   - Titre (auto)
   - Année (auto)
   - Genre (auto, ex. Sci-Fi / Drama)
   - Note moyenne TMDb (auto, petit chiffre discret)
   - Top 3 acteurs (auto, si on tape sur la fiche)
   - Tag « film » ou « série » (auto)

**Pas de formulaire. Pas de champs à remplir.** Juste : recherche → clic → ajouté.

### Vue principale
- Grille de posters, façon « bibliothèque ». 2 colonnes sur mobile, 4 sur desktop.
- Filtres simples : Films / Séries / Tout
- Tri : Récent / Note / Aléatoire
- Sur chaque carte, un petit cœur pour marquer « déjà vu et adoré ».

### Actions sur une fiche (tap sur la carte)
- « Vu ensemble » → déplace dans une section *Vus* avec date
- « Pas pour nous » → retire de la liste (pas de "delete" agressif)
- Petite zone notes libre (« On l'a vu chez Sophie en novembre »)

### API
**TMDb** (The Movie Database) — gratuit, clé API à créer sur themoviedb.org. Endpoints :
- `/search/multi?query=...` — recherche films + séries
- `/movie/{id}` ou `/tv/{id}` — détails complets

---

## 2. Lieux — endroits où aller

### Trois sous-sections
- **Dans notre ville** (lieu de vie)
- **Autres villes** (week-ends, déplacements ponctuels)
- **Voyages** (idées plus larges, destinations à explorer)

L'utilisateur choisit la sous-section au moment de l'ajout, ou tag a posteriori.

### Flux d'ajout
1. Bouton « + » → barre de recherche.
2. Il tape `Le Chateaubri…`
3. **Suggestions Google Places** apparaissent avec photo miniature + adresse.
4. Il clique → ajouté avec :
   - Photo (auto, depuis Google)
   - Nom (auto)
   - Adresse complète (auto)
   - Catégorie (auto : restaurant / café / musée / bar…)
   - Note Google (auto, discrète)
   - Lien Maps (auto)
5. Choix rapide de la sous-section (3 boutons : *Notre ville* / *Autre ville* / *Voyage*).

### Cas voyage (destination floue)
Si l'utilisateur tape juste « Lisbonne » sans lieu précis, on accepte aussi : on stocke comme idée de destination, sans adresse. Photo récupérée via une recherche image générique de la ville (ou Unsplash en fallback).

### Vue principale
- Carte des cartes (jeu de mots, oui) : grille de vignettes avec photo + nom + ville.
- Filtre par sous-section.
- Bouton **« Tirer au sort »** : « On fait quoi ce soir ? » → propose un lieu random dans notre ville.

### API
**Google Places API** (New) — payant mais avec free tier généreux. Endpoints :
- `places:searchText` — autocomplétion avec photos
- `places/{placeId}` — détails

---

## 3. Activités — choses à faire à deux

### Pourquoi pas d'API
Une activité, c'est « faire du vélo », « aller à la patinoire », « tester l'escape game du 11e ». Pas d'API qui couvre ça proprement.

### Flux d'ajout (le plus simple des quatre)
1. Bouton « + »
2. Champ texte unique : « Quelle envie ? »
3. L'utilisateur tape, valide.
4. Optionnel (mais auto-suggéré) : une petite emoji-icône (l'app propose 3 émojis basés sur les mots-clés).
5. Ajouté. Une ligne dans la liste, c'est tout.

### Vue principale
- Liste verticale, façon "todo cocooning". Chaque ligne : emoji + texte + petit tag (intérieur/extérieur, gratuit/payant, calme/actif — choisis par 1 tap, optionnels).
- Bouton « Tirer au sort » en haut.
- Section « Déjà fait » qui archive avec une date.

---

## 4. Cuisine — trucs à cuisiner

### Flux d'ajout
1. Bouton « + »
2. Deux options :
   - **Coller un lien** (Marmiton, Instagram, blog) → l'app récupère titre + image preview via Open Graph tags.
   - **Saisie libre** : titre de la recette + photo optionnelle (drag & drop).
3. Ajouté avec : photo, titre, lien d'origine si applicable.

### Vue principale
- Grille de cartes, façon Pinterest light.
- Catégories souples (tags 1-tap) : *Salé / Sucré / Rapide / Long / Pour les amis*.
- Bouton « Tirer au sort » : « Qu'est-ce qu'on cuisine ce soir ? »

### API
- Aucune. Juste extraction Open Graph côté client (fetch + parse `<meta>` tags) ou ouverture du lien dans un nouvel onglet en fallback.

---

## Fonctionnalités transverses (toutes sections)

### Tirage au sort
Présent dans chaque onglet. Un gros bouton doux qui fait sortir une carte au hasard avec une mini animation (la carte se retourne ou apparaît dans un cercle rose).

### Recherche globale
En haut de l'app, une barre qui cherche dans les 4 piliers en même temps.

### Coche « ensemble »
Sur n'importe quel élément, on peut marquer « fait/vu/visité ensemble le [date] ». Construit une mini timeline accessible depuis un onglet **« Souvenirs »** (5e onglet implicite, en bonus si le temps le permet).

### Pas de comptes utilisateurs
Tout est en local (`localStorage`). Si on veut synchroniser plus tard entre 2 téléphones, on verra (export JSON en attendant).
