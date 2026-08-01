# Tous les prompts utilisés dans le projet

Chaque prompt est copié tel qu'il apparaît dans le code (f-strings résolues
symboliquement), avec le fichier source et le rôle. Aucune contrainte de
brièveté n'est imposée nulle part -- le LLM a toujours tout le temps de
réflexion nécessaire (`max_tokens` large), et chaque prompt explique le
contexte d'usage (à quoi sert la réponse, ce qui se passe si elle est
fausse).

## Point d'insertion 1 — Ordonner les nœuds à explorer

Fichier : `Algorithmes/Points_d_insertion_LLM/Ordonner_noeuds_a_explorer/ordonner_noeuds.py`

### `departager_llm` — départage sur vraie égalité de f (`max_tokens=2000`)

```
Contexte : tu aides une recherche A* à choisir quel état explorer en
premier parmi plusieurs qui semblent aussi prometteurs (même valeur f =
coût + heuristique). Ton choix ne peut jamais faire manquer la solution
optimale -- il influence seulement l'ordre d'exploration, donc la rapidité
de la recherche. Prends tout le temps de réflexion nécessaire.

Voici {N} états parmi lesquels choisir lequel explorer en premier. Termine
par exactement une ligne 'REPONSE: <numéro de l'option choisie>'.

--- Option 1 ---
{description de l'état 1}

--- Option 2 ---
{description de l'état 2}
...
```

## Point d'insertion 2 — Calculer l'heuristique d'un nœud

Fichier : `Algorithmes/Points_d_insertion_LLM/Calculer_Heuristique_d_un_noeud/heuristique_llm.py`

### `heuristique_llm` — un état à la fois (`max_tokens=1500`)

```
Contexte : ton estimation sert d'heuristique dans une recherche A* -- si
tu surestimes le vrai coût restant, la recherche peut manquer la solution
optimale. Sous-estimer coûte juste un peu de temps de recherche en plus.
Prends tout le temps de réflexion nécessaire pour être le plus précis
possible, sans jamais dépasser le vrai coût restant.

Estime le nombre minimal de coups restants pour résoudre ce puzzle depuis
cet état. Termine par exactement une ligne 'REPONSE: <nombre>'.

{description de l'état}
```

### `heuristique_llm_lot` — tous les voisins nouveaux d'un nœud, en un appel (`max_tokens=3000`)

```
Contexte : tes estimations servent d'heuristique dans une recherche A* --
si tu surestimes le vrai coût restant d'un état, la recherche peut manquer
la solution optimale. Sous-estimer coûte juste un peu de temps de
recherche en plus. Prends tout le temps de réflexion nécessaire pour être
le plus précis possible, sans jamais dépasser le vrai coût restant.

Voici {N} états d'un même puzzle. Pour CHACUN, estime le nombre minimal de
coups restants pour le résoudre. Termine par exactement une ligne par
état, au format 'REPONSE i: <nombre>' (une ligne par numéro).

--- Option 1 ---
{description de l'état 1}
...
```

## Point d'insertion 3 — Élaguer les états

Fichier : `Algorithmes/Points_d_insertion_LLM/Elaguer_les_etats/elaguer_llm.py`

`expliquer_objectif=True` par défaut désormais (le préfixe contexte
ci-dessous est donc toujours inclus, sauf désactivation explicite).

### Préfixe contexte (toujours inclus par défaut)

```
Contexte : ta réponse sert de filtre dans un algorithme de recherche A* --
si tu réponds 'oui' à tort, cet état sera supprimé pour toujours de la
recherche, ce qui peut faire rater le seul chemin gagnant ou la seule
solution qui existe. Un 'non' à tort ne coûte qu'un peu de temps de
recherche en plus, alors qu'un 'oui' à tort casse le résultat : sois donc
prudent, ne réponds 'oui' que si tu es certain à 100%.
```

### Jugement libre (`raisonnement_guide=False`, réglage par défaut) (`max_tokens=2000`)

```
[préfixe contexte ci-dessus]

Cet état de puzzle est-il définitivement impossible à résoudre (un
cul-de-sac dont on ne peut plus jamais atteindre le but, quels que soient
les coups joués ensuite) ? Prends tout le temps de réflexion nécessaire,
puis termine par exactement une ligne 'REPONSE: oui' ou 'REPONSE: non'.

{description de l'état}
```

### Raisonnement guidé (`raisonnement_guide=True`) (`max_tokens=2500`)

```
[préfixe contexte ci-dessus]

Cet état de Sokoban est-il définitivement impossible à résoudre ? Une
caisse est bloquée à jamais si, pour CHACUNE de ses 4 directions de
poussée (haut/bas/gauche/droite), la poussée est impossible : soit la
case où irait la caisse est un mur ou une autre caisse, soit la case où
devrait se tenir le joueur (côté opposé) est un mur ou une autre caisse.
Vérifie CHAQUE caisse une par une, en énumérant explicitement ses 4
directions une à une. Termine par exactement une ligne 'REPONSE: oui' ou
'REPONSE: non'.

{description de l'état}
```

## LLM-A* du papier (waypoints) — Pathfinding (`max_tokens=2000`)

Fichier : `Jeux/Recherche_de_chemin/waypoints_llm_a_etoile.py`

```
Grille {largeur}x{hauteur} pour un problème de recherche de chemin.
Coordonnées (x, y) : x = colonne (0 à gauche), y = ligne (0 en haut,
augmente vers le bas).
'A' = départ, 'D' = but, '#' = mur, '.' = case libre :
{grille ASCII}

Départ : {etat_initial}
But : {but}

Contexte : cette séquence de points de passage va guider une recherche A*
-- un bon itinéraire réduit fortement le nombre d'états explorés, un
mauvais peut la ralentir ou l'égarer. Prends tout le temps de réflexion
nécessaire.

Propose une séquence de 3 à 6 points de passage (waypoints) du départ au
but, en évitant les murs, qui te semble un bon itinéraire global. Termine
par exactement une ligne 'REPONSE: (x1,y1) (x2,y2) ...' avec le départ en
premier point et le but en dernier point.
```

## LLM-A* du papier (dispositions complètes) — Taquin, adapté (`max_tokens=3000`)

Fichier : `Jeux/Taquin/waypoints_llm_a_etoile.py`

Contrairement à la première version (ordre de verrouillage des tuiles une
par une), la version retenue demande des **plateaux complets**
intermédiaires -- généralise Pathfinding (où un waypoint est déjà un état
complet, une coordonnée) au lieu de sous-objectifs partiels :

```
Taquin {n}x{n} ('_' = case vide).
Plateau de départ :
{grille}

Plateau but :
{grille}

Contexte : ces dispositions intermédiaires vont guider une recherche A* --
de bonnes dispositions réduisent fortement le nombre d'états explorés, de
mauvaises peuvent la ralentir. Prends tout le temps de réflexion
nécessaire.

En partant du plateau de départ et en allant vers le plateau but, donne 2
ou 3 dispositions COMPLÈTES intermédiaires plausibles du plateau (chaque
chiffre de 1 à {n²-1} et la case vide, chacun une seule fois). Termine par
exactement une ligne par disposition, au format 'DISPOSITION i: v1 v2 v3
...' (les {n²} valeurs lues ligne par ligne, 0 pour la case vide).
```

Le plateau but n'est jamais inventé par le LLM -- toujours celui fourni
par le problème, garanti valide (comme le waypoint final pour Pathfinding).

## LLM-A* du papier (dispositions) — Sokoban, trois variantes

Fichier : `Jeux/Sokoban/waypoints_llm_a_etoile.py`

Trois mécanismes coexistent dans le code (gardés en parallèle pour
comparaison), tous montrent au LLM l'affectation caisse -> cible calculée
classiquement par l'algorithme hongrois (`scipy.optimize.linear_sum_assignment`)
comme repère -- jamais comme substitut au jugement du LLM. La disposition
finale n'est jamais inventée : c'est toujours le résultat hongrois,
garanti valide.

### Version incrémentale (`choisir_prochaine_cible_llm`, une cible à la fois) (`max_tokens=2000`)

```
Voici une carte de Sokoban et l'affectation caisse -> cible la plus courte
au total (calculée sans tenir compte de l'ordre) :
Caisse en {c1} -> cible en {t1}
Caisse en {c2} -> cible en {t2}
...

{description de l'état, grille + légende}

Contexte : ce choix guide une recherche A* incrémentale -- prioriser la
bonne cible réduit le nombre d'états explorés, un mauvais choix peut faire
tourner la recherche en rond ou bloquer d'autres caisses. Prends tout le
temps de réflexion nécessaire.

Parmi les cibles pas encore occupées, laquelle faudrait-il remplir en
PREMIER maintenant ? Une caisse posée trop tôt peut en bloquer une autre.
Termine par exactement une ligne 'REPONSE: (x,y)' avec la cible choisie.
Cibles non remplies : {liste}
```

### Version classique par lot, dispositions de caisses seules (`generer_dispositions_llm`) (`max_tokens=3000`)

Un seul appel, comme Pathfinding/Taquin, au lieu de redemander une cible à
chaque fois -- compromis inverse : moins d'appels, mais un plan figé à
l'avance.

```
Voici une carte de Sokoban et l'affectation caisse -> cible la plus courte
au total (calculée sans tenir compte de l'ordre) :
Caisse en {c1} -> cible en {t1}
...

{description de l'état initial, grille + légende}

Contexte : ces dispositions vont guider une recherche A* -- de bonnes
dispositions intermédiaires réduisent fortement le nombre d'états
explorés, de mauvaises peuvent bloquer des caisses ou ralentir la
recherche. Prends tout le temps de réflexion nécessaire.

En partant de la disposition actuelle des caisses et en allant vers la
disposition finale (chaque caisse sur sa cible assignée), donne 2 ou 3
dispositions INTERMÉDIAIRES plausibles (uniquement les positions des
caisses, pas le joueur). Termine par exactement une ligne par
disposition, au format 'DISPOSITION i: (x,y) (x,y) ...'
```

### Version avec position du joueur (`generer_dispositions_llm_avec_joueur`) (`max_tokens=3000`)

Même principe, mais le LLM précise aussi où doit être le joueur à chaque
étape (pas juste les caisses) -- plus fidèle à la vraie difficulté de
Sokoban (il faut être du bon côté d'une caisse pour la pousser), au prix
d'un prompt/parsing plus complexe. Position du joueur ignorée sur la
disposition finale (le but réel ne contraint pas le joueur).

```
Voici une carte de Sokoban et l'affectation caisse -> cible la plus courte
au total (calculée sans tenir compte de l'ordre) :
Caisse en {c1} -> cible en {t1}
...

{description de l'état initial, grille + légende}

Contexte : ces dispositions vont guider une recherche A* -- de bonnes
dispositions intermédiaires réduisent fortement le nombre d'états
explorés, de mauvaises peuvent bloquer des caisses ou ralentir la
recherche. La position du joueur compte : il doit être du bon côté d'une
caisse pour pouvoir la pousser dans la direction voulue. Prends tout le
temps de réflexion nécessaire.

En partant de la disposition actuelle et en allant vers la disposition
finale (chaque caisse sur sa cible assignée), donne 2 ou 3 dispositions
INTERMÉDIAIRES plausibles, en précisant à chaque fois la position du
JOUEUR et celle des CAISSES. Termine par exactement une ligne par
disposition, au format 'DISPOSITION i: JOUEUR (x,y) CAISSES (x,y) (x,y) ...'
```
