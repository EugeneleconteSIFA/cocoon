# DA.md — Direction artistique (verrouillée)

> Nom de l'app : **Cocon**
> Tagline : *Notre carnet à deux.*
> Vibe : **vintage chic papier**

C'est la référence pour tout le code à venir. Si une question se pose pendant le dev (taille, couleur, rayon, micro-copie), c'est ici qu'on tranche, pas dans `DA-OPTIONS.md` (archivé).

---

## 1. Esprit général

**Cocon** est un **carnet de papeterie rose**. Pas une app SaaS, pas un dashboard. Un objet personnel qu'on garde dans une poche, où l'on écrit deux mots, où l'on colle une photo. On doit sentir le papier, l'encre, le tampon, la fleur séchée.

Le nom est court, neutre, direct : « notre Cocon ». La DA, elle, joue à fond la carte vintage — typo serif romantique, ivoire et roses chauds, filets dorés, micro-ornements floraux. La combinaison donne quelque chose à la fois **simple à dire** et **précieux à regarder**.

### Trois mots-clés
- **Tendre** — chaque détail visuel doit respirer la douceur, jamais l'efficacité froide.
- **Précieux** — l'app est l'objet du couple ; un peu de cérémonie est bienvenue.
- **Lisible** — on doit pouvoir l'utiliser à 2h du matin sur le canapé sans plisser les yeux.

---

## 2. Palette de couleurs

| Rôle | Nom | Hex | Usage |
|---|---|---|---|
| **Fond principal** | Crème rosé | `#FAF1EB` | `body`, fond de toutes les vues |
| **Surface carte** | Ivoire | `#FDF8F3` | cartes, modales, panneaux |
| **Surface haute** | Blanc papier | `#FFFCF8` | éléments en évidence (carte sélectionnée) |
| **Rose principal** | Vieux rose | `#D89A9A` | accents, icônes actives, badges discrets |
| **Rose accent** | Pivoine profonde | `#B86578` | boutons primaires, CTA, états importants |
| **Doré (filet fin)** | Cuivre doux | `#C99878` | séparateurs 1px, ornements, hover states |
| **Doré (ombre)** | Or sourd | `#A57A52` | accents très discrets, état "vu/fait" |
| **Texte principal** | Bordeaux noirci | `#3E1F23` | titres, contenu principal |
| **Texte secondaire** | Mauve sourd | `#8E6A6E` | meta, dates, sous-titres |
| **Texte tertiaire** | Beige fumé | `#B59C95` | placeholders, états désactivés |
| **Erreur (douce)** | Brique passée | `#A85C4E` | erreurs, "Oublier" (la confirmation, jamais en accent) |

Variables CSS à coller directement :

```css
:root {
  --cream:        #FAF1EB;
  --ivory:        #FDF8F3;
  --paper:        #FFFCF8;
  --rose:         #D89A9A;
  --peony:        #B86578;
  --copper:       #C99878;
  --gold:         #A57A52;
  --ink:          #3E1F23;
  --ink-soft:     #8E6A6E;
  --ink-faint:    #B59C95;
  --brick:        #A85C4E;
}
```

---

## 3. Typographie

Deux familles seulement, pour rester cohérent.

### Titres → *DM Serif Display*
- Serif contrastée, romantique, légèrement théâtrale.
- Utilisée pour : logo `Cocon`, titres d'onglets, titres de cartes longs, états vides.
- Toujours en **regular** (pas de bold — la serif tient seule).
- Permet l'italique pour les tagline/citations.

### Texte courant → *Lora*
- Serif lisible, papier, sœur typographique de DM Serif sans la crier.
- Utilisée pour : contenu, boutons, listes, meta.
- Poids utilisés : `400` (normal) et `600` (semibold pour boutons et labels).

### Imports
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Lora:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
```

### Échelle typo
| Élément | Famille | Taille | Line-height | Notes |
|---|---|---|---|---|
| Logo | DM Serif Display | 28 px | 1 | letter-spacing -0.5px |
| Titre d'onglet (h1) | DM Serif Display | 32 px | 1.1 | |
| Titre de carte | DM Serif Display | 18 px | 1.25 | |
| Section (h2) | Lora 600 | 14 px | 1.3 | uppercase, letter-spacing 0.08em, couleur `--copper` |
| Texte courant | Lora 400 | 15 px | 1.55 | |
| Bouton | Lora 600 | 15 px | 1 | |
| Meta / date | Lora 400 italic | 13 px | 1.4 | couleur `--ink-soft` |
| Micro / tag | Lora 600 | 11 px | 1 | uppercase, letter-spacing 0.1em |

---

## 4. Espace, rayon, ombre

### Espacements (échelle de 4)
```css
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 24px;
--space-6: 32px;
--space-7: 48px;
--space-8: 64px;
```

### Rayons
```css
--radius-sm: 10px;   /* tags, petits boutons */
--radius:    16px;   /* cartes, inputs */
--radius-lg: 24px;   /* modales, bottom sheets */
--radius-pill: 999px; /* boutons d'action principale */
```

### Ombres (toutes très discrètes, chaudes)
```css
--shadow-1: 0 1px 2px rgba(62, 31, 35, 0.04);
--shadow-2: 0 4px 12px rgba(62, 31, 35, 0.06);
--shadow-3: 0 12px 32px rgba(62, 31, 35, 0.10);
```

Jamais de glow, jamais d'ombre bleue/froide. La lumière de Cocon vient toujours d'une bougie, pas d'un néon.

---

## 5. Composants clés

### Bouton primaire (« CTA »)
- Fond `--peony` (pivoine profonde), texte ivoire `#FDF8F3`.
- Padding `12px 24px`, rayon `--radius-pill`.
- Lora 600 15px.
- Hover : assombrit de 6%, ombre `--shadow-2`.

### Bouton secondaire / ghost
- Fond transparent, bordure 1px `--copper`, texte `--ink`.
- Hover : fond `--ivory`.

### Carte de contenu
- Fond `--ivory`, rayon `--radius`, ombre `--shadow-1`.
- Padding intérieur `--space-5`.
- Image (poster, photo de lieu) en haut, full-width, rayon haut respecté.
- Filet doré 1px (`--copper`, opacity 0.5) entre l'image et le contenu.

### Onglets de navigation (bas d'écran, mobile-first)
- Barre fixe en bas, fond `--paper`, bord supérieur 1px `--copper` opacity 0.3.
- 4 icônes : une mini illustration SVG par pilier (pas d'emojis ici, on dessine — voir §7).
- Onglet actif : icône en `--peony`, label en `--ink`.
- Onglet inactif : icône en `--ink-faint`, label en `--ink-soft`.

### Champ de recherche
- Fond `--paper`, bordure 1px `--copper` opacity 0.4, rayon `--radius`.
- Padding `12px 16px`.
- Focus : bordure passe à `--peony`, ombre `--shadow-1`.
- Placeholder en `--ink-faint` italique.

### Bottom sheet (détail d'un élément)
- Fond `--paper`, rayon `--radius-lg` (haut seulement).
- Glisseur (small bar) 36px × 4px, `--copper` opacity 0.5, centré tout en haut.
- Padding `--space-6`.
- Ombre `--shadow-3`.

### Tampon « Vu ensemble » / « Fait ensemble » / « Visité »
- Pseudo-tampon rotatif (-3°), bordure 2px `--peony` opacity 0.7, texte `--peony` opacity 0.7.
- Lora 600 11px uppercase letter-spacing 0.15em.
- Apparaît en overlay sur le coin haut-droit de la carte quand l'élément est coché.
- C'est la **signature visuelle de l'app** — un tampon de carnet, pas une checkbox.

---

## 6. Texture & ornements

### Grain papier (très très subtil)
Un SVG noise en `background-image` du `body`, opacity max **0.025**. Doit être quasi invisible mais perceptible sur grand écran.

### Filets dorés
Séparateurs entre sections : `1px solid var(--copper)` avec `opacity: 0.4`. Toujours fins, jamais épais.

### Ornements floraux
Mini SVG d'une pivoine stylisée (très simple, contour seul, 16×16 ou 24×24) en `--copper` opacity 0.3, posée :
- En filigrane dans le coin bas-droit des cartes "spéciales" (favoris).
- À gauche du logo dans le header.
- Comme séparateur central dans les écrans vides : un filet — fleur — filet.

L'ornement est **discret**, jamais décoratif au point d'encombrer.

---

## 7. Iconographie

### Onglets (4 illustrations SVG custom à dessiner)
Style : trait seul, 1.5px, coin arrondi, géométrie simple. Couleur = couleur d'onglet (état dépendant).

- **Culture** → une petite bobine de pellicule + un livre sous (peut être stylisé en une seule forme).
- **Lieux** → un trait de carte + un pin façon broche.
- **Activités** → deux silhouettes côte à côte, ou un cœur dans un cercle.
- **Cuisine** → une casserole avec deux volutes de fumée.

### Icônes d'action (ajout, recherche, tirage)
- Lucide icons (lucide.dev) en `--copper` ou `--peony` selon contexte.
- Stroke 1.5px, jamais filled.

---

## 8. Micro-copie (ton de voix)

Toujours en français, à la première personne du pluriel (« on », « nous »), tendre, jamais corporate.

| Contexte | À DIRE | À NE PAS DIRE |
|---|---|---|
| Bouton ajouter | « Ajouter au carnet » | « Submit », « + Ajouter » |
| Recherche | « Qu'est-ce qu'on cherche ? » | « Rechercher » |
| État vide général | « Le carnet est tout neuf. » | « Aucun résultat » |
| État vide film | « Aucun film n'attend encore. Cherchez-en un. » | « 0 items » |
| Confirmation suppression | « On l'oublie ? » | « Confirmer la suppression » |
| Action suppression | « Oublier » | « Supprimer », « Delete » |
| Action archivage | « Mettre de côté » | « Archive » |
| Tampon « vu » | « Vu ensemble · 14 mars » | « Watched » |
| Tirage au sort | « Tirer au sort » | « Random », « Suggest » |
| Header tirage | « Et si on regardait… » / « Et si on cuisinait… » / « Et si on sortait… » | — |
| Erreur réseau | « Connexion fragile, on réessaie ? » | « Error 500 » |
| Sauvegarde | « C'est gardé. » | « Saved successfully » |

Toujours **dire moins** plutôt que plus. Une phrase claire vaut mieux qu'une phrase mignonne mais bavarde.

---

## 9. Animations

Toutes les animations en `cubic-bezier(0.4, 0, 0.2, 1)` (ease-out doux), durée par défaut `220ms`.

- Apparition de carte ajoutée : fade-in + translateY de 8px.
- Tampon « vu » : scale de 1.15 → 1 + rotation finale -3°, duration 320ms.
- Tirage au sort : la carte sélectionnée fait un léger pulse (1 → 1.04 → 1), 600ms.
- Bottom sheet : slide-up depuis le bas, 280ms.

Pas d'animation de chargement spectaculaire. Un simple skeleton ivoire suffit.

---

## 10. Layout & responsive

### Mobile (priorité 1 — la cible)
- `max-width: 480px` centré.
- Padding latéral `--space-5`.
- Header sticky en haut (logo + recherche globale), barre d'onglets sticky en bas.
- Grilles : 2 colonnes pour les posters films, 1 colonne pour les lieux/activités/recettes longs.

### Desktop (priorité 2)
- `max-width: 720px` centré (on ne fait pas une app desktop large — on garde le format carnet).
- Mêmes proportions, juste plus d'air autour.
- Barre d'onglets : peut passer à gauche en vertical, ou rester en bas (à décider à l'implémentation, voir ce qui paraît juste).

Pas de version tablette dédiée. Le mobile s'étire jusqu'à 720px, point.

---

## 11. Ce qu'on évite absolument

- ❌ Couleurs froides, bleues, vertes (sauf erreur exceptionnelle, en très petite touche).
- ❌ Boutons rectangulaires à coins droits.
- ❌ Police géométrique (Helvetica, Inter, Roboto) — Cocon n'est pas un produit SaaS.
- ❌ Glassmorphism, néons, glows.
- ❌ Emojis comme éléments décoratifs principaux (acceptables pour les sélections rapides de tags, mais pas dans la nav).
- ❌ Dégradés bandes-dessinées roses → mauves saturés. Si dégradé, il doit être imperceptible (`#FDF8F3` → `#FAF1EB`, par exemple).
- ❌ Tonalité corporate dans la micro-copie (« veuillez », « soumettre », « envoyer »).
- ❌ Animations punchy ou rebondies. Tout est lent, posé, papier qui se tourne.

---

## 12. Logo

Logo texte simple : **`Cocon`** en *DM Serif Display* 28px, couleur `--ink`, suivi d'une mini pivoine ornement en `--copper` (12px, opacity 0.5) en exposant à droite.

Pas de symbole graphique séparé pour l'instant. Si on veut un favicon plus tard : la pivoine seule, 32×32, en `--peony` sur fond `--cream`.

---

## 13. Récap : la "feuille de style" en 5 secondes

> Fond crème rosé. Cartes ivoire. Roses chauds (vieux rose, pivoine) en accent. Filets et ornements cuivre. Tout en serif (*DM Serif Display* pour les titres, *Lora* pour le texte). Rayons généreux mais pas extrêmes. Ombres invisibles ou presque. Tampons rotatifs pour les états "vu/fait ensemble". Micro-copie tendre, jamais corporate.

**Tout code qui dévie de ça doit être justifié explicitement, ou corrigé.**
