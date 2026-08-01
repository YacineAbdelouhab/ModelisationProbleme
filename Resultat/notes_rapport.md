# Notes pour le rapport

Observations et constats faits en cours de route, à réutiliser pour la rédaction.
Pas le rapport lui-même — juste la matière brute, dans l'ordre où on l'a trouvée.

## Heuristique de Recherche_de_chemin : Manhattan ignore les obstacles

`heuristique()` (probleme_recherche_de_chemin.py) utilise la distance de Manhattan,
qui ignore complètement les murs — elle sous-estime donc parfois beaucoup le vrai
coût (ex: niveau3_difficile, 343 états visités pour un chemin de 44 seulement,
signe d'une heuristique peu informative dans les zones ouvertes avec obstacles).

On peut faire strictement mieux avec une heuristique "parfaite" précalculée (BFS
depuis le but, une fois pour toutes) — mais le calcul de cette heuristique coûte
alors autant qu'une recherche complète. Ça ne paie que si on **réutilise** le
précalcul pour plusieurs recherches sur la même carte (même but, départs
différents) — sinon aucun gain.

**Lien direct avec le cours** : c'est exactement l'idée de l'heuristique ALT
("précalculer les distances d'un point donné à tous les autres points") et des
bases de patterns du taquin : precalcul coûteux une fois, réutilisé énormément
de fois ensuite (many queries, même but/état but fixe). Le gain d'A* vs recherche
naïve n'existe que dans ce régime "beaucoup de requêtes, précalcul amorti" — pas
pour une requête unique.

## IDA* vs A* : les transpositions plombent IDA* sur Sokoban

Mesure sur nos 3 jeux (ratio = appels totaux à chercher() / états distincts
explorés, sur une instance de difficulté "moyenne" de chaque jeu) :

| Domaine | États distincts | Appels totaux | Redondance |
|---|---|---|---|
| Recherche de chemin | 53 | 908 | 17x |
| Taquin | 43 | 119 | 2.8x |
| Sokoban | 1425 | 252305 | **177x** |

**Pourquoi** : IDA* n'a aucune mémoire globale des états déjà vus (seulement
`sur_le_chemin`, qui évite les boucles sur la branche courante). Dès qu'un même
état est atteint par deux chemins différents (une transposition), IDA* refait
tout le travail depuis cet état à chaque fois. A* évite ça nativement via
`fermes`/`cout_g`.

Sokoban est un cas extrême de transpositions : le joueur peut se déplacer
librement autour des caisses sans les toucher, donc des dizaines de trajets
différents (sans pousser aucune caisse) mènent à la même configuration exacte.
Au taquin, presque chaque coup change réellement l'état → peu de transpositions.

**Conclusion** : IDA* n'est avantageux (mémoire) que sur les domaines à faible
taux de transposition. Sur Sokoban, il est nettement moins efficace que A* en
pratique malgré une garantie d'optimalité identique — "le meilleur algorithme
dépend du domaine", pas un choix universel.

## Sokoban : le vrai niveau 1 (1988) est intraitable pour notre A* de base

Même avec détection d'interblocage de coin, le vrai niveau 1 original (Thinking
Rabbit, 1988, 6 caisses) n'est pas résolu après 3 millions d'états explorés
(111s). Cohérent avec la réputation du jeu ("le Go des puzzles", cours). D'où
l'usage de Microban (Skinner) comme set de travail — mêmes vrais niveaux Sokoban,
mais conçus pour rester abordables.

## Sokoban : pourquoi le pruning (détection d'interblocage) prime sur l'heuristique

La difficulté de Sokoban vient surtout du fait que la majorité des configurations
explorées sont déjà des impasses insolubles, pas d'une heuristique trop faible.
Éliminer ces impasses plus tôt (pruning / élagage) paie donc plus qu'affiner
l'estimation de coût (heuristique) -- point à développer pour motiver pourquoi le
hook LLM "Élaguer les états" est probablement le plus impactant sur ce jeu
spécifiquement, contrairement à Recherche_de_chemin/Taquin où heuristique et
pruning s'étaient montrés comparables dans l'autre projet.

Règles classiques au-delà du coin mort (déjà implémenté) :
1. Caisse gelée contre un mur sans aucune cible sur toute la ligne (plus générale
   que le coin -- le coin est le cas particulier où la ligne fait 1 case).
2. Deux caisses gelées l'une contre l'autre contre un mur (pas encore fait).

## Résultat de la règle 1 (couloirs morts) sur Microban

Implémentée dans `_calculer_couloirs_morts` (probleme_sokoban.py), en union avec
les coins (`_calculer_coins_mortels`). Vérifié que le coût optimal ne change pas
sur les 4 niveaux (donc pas de faux positif qui casserait une solution existante),
seul le nombre d'états explorés change :

| Niveau | Avant (coin seul) | Après (+ couloirs) | Réduction |
|---|---|---|---|
| niveau1_facile | 1438 | 1088 | -24% |
| niveau2_moyen | 9908 | 1761 | **-82%** |
| niveau3_difficile | 32287 | 13428 | -58% |
| niveau4_tres_difficile | 144749 | 56240 | -61% |

Sur le vrai niveau 1 original (1988), même avec cette règle en plus (23 cases
mortes détectées contre 18 avant), toujours pas résolu après 3 millions d'états
(111s) -- confirme qu'il faut des techniques encore plus spécifiques (tables
d'interblocages par analyse rétrograde, propres à la géométrie du niveau) pour
ce niveau précis, pas juste des règles génériques de coin/couloir.

## Hook LLM "Ordonner les nœuds" : premiers résultats réels (Claude)

Implémenté comme départage pur (`cle_ordre`, dans `a_etoile.py`) : n'influence
jamais quel f est le plus petit, donc l'optimalité est garantie par construction
-- vérifié empiriquement aussi (coût LLM = coût baseline partout).

Sur `Recherche_de_chemin/niveau1_facile/carte1` (baseline : 33 états visités) :

| Config | Visites | Appels API |
|---|---|---|
| Baseline (sans LLM) | 33 | 0 |
| `cle_ordre` (1 appel par état généré) | 11 | ~1 par état |
| `cle_ordre_lot` (1 appel par expansion, plusieurs états à la fois) | 13 | ~1 par expansion |

Les deux réduisent nettement l'exploration (33 -> 11-13) tout en gardant
l'optimalité -- confirme la garantie théorique en pratique, sur un vrai LLM.

**Piège rencontré avec `cle_ordre_lot`** : le modèle a un bloc de "réflexion"
interne (`thinking`) qui consomme une partie du budget `max_tokens` avant même
le texte visible. Avec 600 tokens et plusieurs états à noter d'un coup, la
réponse a été tronquée à 41 caractères (`stop_reason: max_tokens`, 172 tokens
partis dans le bloc thinking) -- résultat : notes manquantes remplacées par la
valeur neutre (50), départage bien moins informatif (30 visites au lieu de 11-13).
Correction : monter `max_tokens` (600 -> 1500 pour le lot) règle le problème.
**Leçon générale** : plus la réponse demandée est longue/complexe (plusieurs
candidats à noter), plus il faut de marge de tokens, à cause de ce coût caché
du raisonnement interne du modèle.

## `cle_ordre`/`cle_ordre_lot` sur les 3 jeux : effet variable

| Jeu | Baseline | Avec LLM (lot) | Réduction |
|---|---|---|---|
| Recherche de chemin | 33 | 13 | -61% |
| Sokoban | 92 | 67 | -27% |
| Taquin | 55 | 53 | -4% (quasi nul) |

Optimalité préservée dans les 3 cas (garantie théorique confirmée en pratique).
Effet très inégal en revanche. Hypothèse (pas encore vérifiée en comptant les
égalités de f réellement rencontrées) : `cle_ordre` ne sert QUE de départage
entre états à f égal -- si le taquin a peu d'égalités de f (Manhattan y est déjà
assez discriminante), le LLM a peu d'occasions d'agir, même s'il juge bien.

## Littérature : ce qui existe déjà sur LLM + Sokoban/recherche heuristique

Trois papiers directement pertinents trouvés par recherche web (juillet 2026) :

1. **[SokoBench](https://arxiv.org/pdf/2601.20856)** (2026) -- teste des LLM en
   prompting direct (génèrent toute la solution, pas de recherche derrière) sur
   Sokoban. ~10-12% de réussite (o1-preview seul), ~43% avec un setup
   "LLM-Modulo" (LLM propose, planificateur externe vérifie/exécute). Catégories
   d'échecs qu'ils rapportent : *"deadlock failures: inability to recognize
   unsolvable states"* et *"spatial reasoning mistakes: incorrect box/player
   position tracking"* -- correspond exactement à ce qu'on a observé nous-mêmes
   (confusion d'axes du pruning Sokoban en v2). Confirme que ce n'est pas une
   malchance de notre côté mais une faiblesse documentée des LLM sur ce jeu
   précis.

2. **[A Training Data Recipe to Accelerate A* Search with Language Models](https://arxiv.org/abs/2407.09985)**
   (EMNLP 2024) -- même sujet que notre hook heuristique (LLM comme heuristique
   pour A* sur labyrinthe/Sokoban/taquin), mais méthode différente : ils
   **entraînent/fine-tunent** le LLM comme heuristique (données de coût réel),
   nous on **prompt** un modèle déjà entraîné, sans fine-tuning. Résultats
   annoncés : jusqu'à 15x moins d'itérations, 5x plus rapide -- mais avec toute
   l'infrastructure d'entraînement en plus. Bon point de discussion
   fine-tuning-vs-prompting pour le rapport.

3. **[GVGAI-LLM](https://arxiv.org/html/2508.08501)** (2025) -- teste 9 LLM
   généraux (GPT-4o-mini, o3-mini, Gemini, Llama, DeepSeek -- **pas Claude**) en
   zero-shot, en train de jouer directement à Sokoban (pas comme composant dans
   A*). Résultats sur 5 niveaux Sokoban : Gemini-3-flash 68%, DeepSeek-r3.2 56%,
   o3-mini 52%, Gemini-2.5-pro 28%, **tous les autres modèles : 0%**. Conclusion
   clé : *"reasoning models substantially outperform standard models"* --
   confirme indépendamment notre découverte du premier projet (prompt sans
   espace de raisonnement = catastrophe, avec raisonnement = ça marche), mais à
   l'échelle de familles de modèles entières, pas juste d'un réglage de prompt.
   Catégorie d'échec qu'ils nomment : *"spatial grounding errors (coordinate
   confusion)"* -- encore une fois, notre incident d'axes confondus.

**Limite de cette littérature, à noter dans le rapport** : aucun des papiers
trouvés ne teste Claude sur Sokoban. Nos propres résultats (avec Claude comme
modèle principal) sont donc une donnée que la littérature existante n'a pas
encore -- pas juste une reproduction, un point de comparaison original.

## Toutes les briques codées (objectif : finir le code avant l'expérimentation complète)

Recentrage du projet vu la deadline : d'abord coder chaque brique et valider
qu'elle fonctionne (test minimal, pas une campagne complète), l'expérimentation
systématique sur les 3 jeux étant repoussée à plus tard. État à ce stade :

| Brique | Fichier(s) | Statut |
|---|---|---|
| Ordonner (par état) | `Algorithmes/LLM_A_etoile/Ordonner_noeuds_a_explorer/ordonner_noeuds.py` (`cle_ordre_llm`) | ✅ testé sur les 3 jeux |
| Ordonner (par lot) | idem (`cle_ordre_lot_llm`) | ✅ testé sur les 3 jeux |
| Calculer l'heuristique | `Algorithmes/LLM_A_etoile/Calculer_Heuristique_d_un_noeud/heuristique_llm.py` | ✅ codé, `a_etoile()` accepte `heuristique_llm=` |
| Élaguer les états | `Algorithmes/LLM_A_etoile/Elaguer_les_etats/elaguer_llm.py` | ✅ codé + validé sur cas trivial, `a_etoile()` accepte `elaguer_llm=` |
| LLM-A* (papier, waypoints) | `Algorithmes/LLM_A_etoile_papier/llm_a_etoile_papier.py` + `Jeux/Recherche_de_chemin/waypoints_llm_a_etoile.py` | ✅ codé + validé (cout=10=baseline, 14 visites vs 33) |

Chaque hook de `a_etoile()` documente sa propre garantie théorique dans le
docstring (voir le fichier) : `cle_ordre`/`cle_ordre_lot` ne peuvent jamais
casser l'optimalité (pur départage à f égal) ; `heuristique_llm` et
`elaguer_llm` le peuvent (remplacent respectivement h et filtrent les
ouverts) ; LLM-A* papier n'a structurellement aucune garantie.

(Note : ToT (Tree of Thoughts) avait aussi été codé à ce stade du projet,
mais retiré depuis -- hors scope du rapport final.)

## Le budget de tokens "mangé par le raisonnement" touche aussi DeepSeek

Pas spécifique à Claude : `deepseek-v4-flash` a un champ séparé
`reasoning_content` (au lieu d'un bloc `thinking` mélangé au contenu comme
Claude), mais le symptôme est identique -- avec `max_tokens=50`, 46 tokens
sont partis dans `reasoning_content` et `message.content` est resté vide.
Passer à `max_tokens=600` (notre valeur par défaut) règle le problème. Un
modèle "raisonneur" (peu importe le fournisseur) consomme son budget de
sortie sur le raisonnement invisible avant même de produire la réponse
visible -- toujours prévoir large.

## Refonte du point d'insertion 1 : départage seulement sur vraie égalité de f

En creusant `cle_ordre_lot` (qui appelle le LLM à chaque expansion, sur les
voisins fraîchement générés), on a identifié que ce n'est qu'une
approximation pratique -- ça n'attend pas de vraie égalité de `f` dans les
ouverts pour appeler le LLM, contrairement à l'idée d'origine du point
d'insertion 1. Beaucoup plus d'appels API que nécessaire.

Nouvelle version : `a_etoile()` détecte une vraie égalité de `f` *au moment
de dépiler* (`heapq` permet de regarder le sommet du tas sans le retirer via
`ouverts[0]`, donc on peut vérifier `ouverts[0][0] == f` avant de rappeler
le LLM), et n'appelle le LLM que dans ce cas précis -- les états non
choisis sont remis dans le tas. `cle_ordre`/`cle_ordre_lot` sont retirés,
remplacés par un unique paramètre `departager_llm`.

**Effet mesuré du changement** (`Recherche_de_chemin/niveau1_facile/carte1`,
baseline 33 états visités, coût optimal 10 dans tous les cas) :

| Version | Visites | Quand le LLM est appelé |
|---|---|---|
| `cle_ordre_lot` (ancienne, par expansion) | 13 | à chaque expansion, sur les voisins frais |
| `departager_llm` (nouvelle, vraie égalité) | 29 | seulement si vraie égalité de f détectée |

**Compromis à retenir pour le rapport** : la version "fidèle" (vraie égalité
seulement) fait moins d'appels API par construction, mais a aussi moins
d'occasions d'influencer la recherche -- elle n'intervient que quand une
égalité se présente réellement, ce qui est plus rare que "à chaque
expansion". Résultat : gain plus modeste (33->29) que l'approximation
"par lot à chaque expansion" (33->13). Ni l'une ni l'autre n'est "fausse" --
elles répondent à des définitions différentes de ce qu'on autorise le LLM à
influencer, avec un vrai arbitrage coût (appels API) / bénéfice (réduction
d'exploration).

## Point d'insertion 2 (heuristique) : admissible ne suffit pas, il faut consistant -- preuve chiffrée

Rappel des définitions :
- **Admissible** : `h(état) <= vrai coût restant`, jamais de surestimation.
- **Consistante** (plus forte) : pour tout voisin, `h(état) <= coût(état, voisin) + h(voisin)`.
  Consistante implique admissible, l'inverse est faux.

**Pourquoi ça compte spécifiquement pour notre code** : `a_etoile.py` ne
rouvre jamais un état une fois dans `fermes` (`if etat_suivant in fermes:
continue`). Cette simplification standard n'est prouvée correcte que sous
l'hypothèse de **consistance** -- avec une heuristique seulement admissible
(mais pas consistante), un état peut être fermé avec un `g` non optimal, et
un chemin moins cher découvert ensuite est purement ignoré.

**Contre-exemple construit et vérifié par le code** (pas juste théorique) :
graphe `S -> Y (1), S -> X (3, direct mais gaspilleur), Y -> X (1), X -> Z
(1), Z -> G (1)`. Vrai optimum : `S -> Y -> X -> Z -> G` = 4. Heuristique
`h = {S:4, Y:3, X:0, Z:1, G:0}` -- vérifiée admissible partout (`h <= vrai
reste` pour chaque état), mais inconsistante sur l'arête `Y -> X`
(`h(Y)=3 > coût(Y,X) + h(X) = 1 + 0 = 1`).

Résultat réel de `a_etoile()` sur ce graphe : **coût = 5, pas 4**. `X` est
fermé via le chemin direct coûteux (`g=3`) avant que `Y` révèle le chemin à
`g=2` -- et comme `X` est déjà dans `fermes`, cette amélioration est
silencieusement ignorée.

**Conséquence pour `heuristique_llm`** : même dans l'hypothèse optimiste où
le LLM resterait toujours admissible (déjà pas garanti), il resterait un
second risque distinct et plus sournois -- rien ne garantit la consistance
de ses estimations d'un état à son voisin. Deux façons indépendantes de
casser l'optimalité, pas une seule, et la seconde est invisible si on ne
vérifie que "est-ce que h dépasse le vrai coût ?" sur des états isolés.

## Deux parades, testées séparément puis ensemble -- aucune ne suffit seule

**Parade 1 : `min(h_llm, h_classique)`** -- protège l'admissibilité,
mathématiquement garanti (min de deux valeurs dont une est déjà `<= vérité`
reste `<= vérité`). Mais ne protège pas la consistance : sur le contre-exemple
ci-dessus, `min` sélectionne `h(X)=0` (du LLM) ET `h(Y)=3` (du classique)
indépendamment à chaque état -- exactement la même paire incohérente que sans
protection. Résultat : toujours `cout=5`, pas 4.

**Parade 2 : `pathmax`** -- à chaque pas parent->voisin, force
`h(voisin) = max(h_brut(voisin), h(parent) - coût_du_pas)`. Ça revient à
imposer l'inégalité de consistance directement, en corrigeant à la volée
plutôt qu'en espérant qu'elle soit déjà vraie. Corrige bien le contre-exemple
ci-dessus (cout=4). Mais `max()` ne peut jamais **réduire** une valeur --
sur un second contre-exemple où le LLM surestime carrément sur la branche
gagnante (graphe `S->P->G` coût 2 vs `S->Q->G` coût 4, avec `h_llm(P)=5`
alors que le vrai reste est 1), pathmax seul renvoie encore `cout=4` au lieu
de 2 -- il ne corrige jamais une surestimation de départ.

**Les deux ensemble (implémenté)** : `min` dans `heuristique_llm.py` (avant
de renvoyer la valeur au moteur), `pathmax` dans `a_etoile.py` (dans le
calcul de `h()`, automatique et sans effet sur une heuristique déjà
consistante -- vérifié : aucune régression sur les 3 jeux avec heuristique
classique). Vérifié sur les deux contre-exemples via le vrai code intégré
(pas juste des scripts de test) : `cout=4` et `cout=2`, les deux corrects.

**À retenir pour le rapport** : admissibilité et consistance sont deux
propriétés indépendantes qui cassent l'optimalité de façons différentes, et
qui demandent donc deux parades différentes et complémentaires -- aucune
protection unique ne couvre les deux failles.

**Protections rendues activables/désactivables** (`proteger_consistance` dans
`a_etoile()`, `proteger_admissibilite` dans `heuristique_llm()`), pour pouvoir
mesurer le comportement brut du LLM sans les parades, à volonté :

| Consistance | Admissibilité | Coût obtenu (contre-exemple) |
|---|---|---|
| Off | Off | 5 (le bug d'origine, reproduit à la demande) |
| On | Off | 4 |
| Off | On | 4 |
| On | On | 4 (défaut, sûr) |

## Point d'insertion 2 : version par lot -- mêmes garanties, moins d'appels

`heuristique_llm_lot` reprend le même principe de notation par lot : au lieu d'un appel API par état, un seul
appel note **tous les voisins nouveaux d'un même nœud** en une fois
(`REPONSE i: <nombre>` par candidat), avant que la boucle de `a_etoile()` ne
les traite un par un comme d'habitude. Le `min`/pathmax s'appliquent
identiquement, valeur par valeur, une fois le lot reçu -- aucune différence
de comportement.

Vérifié avec un faux LLM (renvoie la valeur classique, pour isoler la
logique du reste) sur `Recherche_de_chemin/niveau1_facile/carte1` :

| Version | Coût | Appels API | Visites |
|---|---|---|---|
| `heuristique_llm` (un par un) | 10 | 55 | 33 |
| `heuristique_llm_lot` (par lot) | 10 | 33 | 33 |

Même chemin, même coût, même nombre d'états visités -- seul le nombre
d'appels change (un par nœud exploré au lieu d'un par état nouvellement
découvert). Les deux versions sont gardées en parallèle (pas l'une à la
place de l'autre) précisément pour permettre cette comparaison coût/qualité
pendant l'expérimentation.

## Point d'insertion 3 (élaguer) : pourquoi aucun garde-fou combiné n'est possible

Contrairement aux points 1 et 2, `elaguer_llm` n'a **aucune protection
disponible**, et ce n'est pas un manque de temps -- c'est démontrable en
lisant le code existant. Sokoban a déjà une règle classique certaine (coins
et couloirs morts, `_coins_mortels` dans `probleme_sokoban.py`), exposée
comme `Probleme.est_impossible(etat)` (ajouté au contrat abstrait,
`False` par défaut pour les jeux sans notion de cul-de-sac certain). Mais
cette règle est déjà appliquée **à l'intérieur de `voisins()`**, avant même
qu'un état candidat n'atteigne `elaguer_llm` :

```python
if (bx, by) in self._coins_mortels:
    continue  # la caisse serait bloquée à jamais -- jamais proposé comme voisin
```

Donc tout état qui arrive jusqu'à `elaguer_llm` a, par construction, déjà
passé la règle classique -- un "ET" entre le LLM et le classique
renverrait donc **toujours faux** à ce stade, neutralisant complètement
l'apport du LLM sans rien apporter en échange (le classique agit déjà seul,
plus tôt). Contrairement à `min(h_llm, h_classique)` pour le point 2 (qui
laisse le LLM influencer le résultat tout en le bornant), il n'existe pas
d'équivalent "gratuit" ici : soit on fait confiance à une règle certaine
(le LLM n'ajoute rien), soit on fait confiance au LLM seul (risque brut,
sans filet). Limite acceptée et documentée dans le code -- à mesurer
empiriquement, pas à corriger.

## `elaguer_llm` en pratique : un cas trivial raté, puis corrigé

Batterie de 4 états Sokoban à vérité connue, construits à la main (pas de
recherche lancée, juste `elaguer_llm(etat)` appelé directement) :
- **A. coin mort certain** (2 murs perpendiculaires, pas de cible) -- vérité = impossible.
- **B. caisse déjà sur sa cible** -- vérité = pas impossible.
- **C. bloc 2x2 de 4 caisses en pleine salle ouverte** (freeze deadlock -- chaque
  caisse bloque les 3 autres, aucun mur nécessaire) -- vérité = impossible,
  mais **non couvert par la règle classique** (aucun mur à proximité).
- **D. caisse seule en pleine salle** -- vérité = pas impossible.

| Variante (Claude) | A (coin) | B (cible) | C (freeze) | D (normal) | Score |
|---|---|---|---|---|---|
| Jugement libre | **Faux (raté)** | Correct | Faux (raté) | Correct | 2/4 |
| Raisonnement guidé (vérifie les 4 directions de poussée une par une, par caisse) | **Correct** | Correct | Faux (raté) | Correct | 3/4 |

Le jugement libre rate même le cas le plus trivial possible (un coin,
indiscutable) -- pas juste le cas dur (freeze deadlock, jamais attendu).
Forcer une vérification explicite direction par direction corrige le cas
trivial sans introduire de faux positif sur B/D, mais ne suffit pas pour le
freeze deadlock (qui demande de raisonner sur l'interaction entre
plusieurs caisses, pas juste une caisse isolée).

**Testé et écarté comme explication** : le format de description de l'état
(grille détaillée + listes de coordonnées explicites vs grille seule,
minimale) donne **exactement le même résultat** dans les deux cas (2/4 en
jugement libre, identique avec grille minimale). Le raté n'est donc pas un
problème de présentation/verbosité du prompt -- c'est un vrai manque de
vérification systématique de la mécanique de poussée, corrigé par le
raisonnement guidé, pas par la mise en forme.

**Piste non testée (implémentée mais pas mesurée)** : `expliquer_objectif`
(paramètre de `elaguer_llm`) ajoute un paragraphe expliquant au LLM que sa
réponse sert de filtre dans une recherche A*, et qu'un faux "oui" est bien
plus coûteux (supprime définitivement un état, potentiellement le seul
chemin gagnant) qu'un faux "non" (juste un peu de temps de recherche en
plus). Codé, jamais exécuté sur la batterie complète (écarté du plan final
d'expérimentation pour rester dans un budget d'appels raisonnable) -- piste
à tester plus tard si le temps le permet.

## Avant de tout faire tourner : jusqu'où va l'espace d'états par niveau ?

Sweep gratuit (A* classique, sans LLM, `max_etats_explores=200000`) sur
**tous** les fichiers d'exemple des 3 jeux, pour savoir lesquels sont
seulement envisageables avec un hook LLM (un appel API par état) :

| Jeu | niveau1 | niveau2 | niveau3 | niveau4 |
|---|---|---|---|---|
| Recherche de chemin | ~30-33 | ~82-110 | ~147-343 | ~82-158 |
| Taquin | 4-17 | 34-83 | 18-68 | **12 061-14 606** |
| Sokoban (microban) | 1 (trivial) / 1088 | 1761 | 13 428 | **56 240** |
| Sokoban (original, 1988) | **≥200 000, n'aboutit même pas classiquement** | — | — | — |

Conclusion directe : tester un hook LLM sur Taquin niveau4 ou Sokoban
niveau3/4 coûterait plusieurs milliers à dizaines de milliers d'appels API
**pour une seule instance, une seule variante**. Sokoban "original" ne se
résout même pas en A* classique sous 200 000 états -- un hook LLM n'y
changera rien, le tester ne serait pas informatif (baseline et hooks
échoueraient identiquement). D'où la décision : expérimentation limitée à
niveau1-niveau3 (niveau4 et Sokoban original exclus), avec un cap
`max_etats_explores` (200 dans la version courante) pour borner le pire cas
même dans cette plage réduite -- Sokoban microban niveau1-3 dépasse déjà
largement ce cap en A* classique (1088 à 13 428 états).

## Grande expérimentation : baseline vs les 3 points d'insertion, niveau1 à niveau3

Design retenu (`Resultat/lancer_experimentation.py`) : 21 instances (3
niveaux x 3 cartes pour Recherche_de_chemin/Taquin, 3 niveaux x 1 fichier
pour Sokoban microban), cap à 200 états, DeepSeek comme fournisseur. Pour
Sokoban spécifiquement, chaque instance est testée deux fois (description
détaillée vs minimale) pour vérifier si l'effet de format observé sur
`elaguer_llm` (aucun effet) se généralise aux autres hooks. Axes secondaires
gardés volontairement sur une seule instance chacun (mécanismes génériques,
pas spécifiques à un jeu ni à une difficulté) : protections du point 2 (sur
les 3 jeux, niveau1 uniquement), lot vs un-par-un (Recherche_de_chemin,
niveau1 à niveau3).

*Résultats à compléter une fois le run terminé.*
