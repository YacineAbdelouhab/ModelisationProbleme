# Un LLM dans l'algorithme A* sans forcément casser les garanties théoriques ?

M2 IASD App - Projet Modélisation de Problèmes
ABDELOUHAB Yacine et JANIN Paul

Le rapport complet (méthode, preuves, résultats) est dans [`Rapport/main.pdf`](Rapport/main.pdf).
Ce README ne sert qu'à faire tourner le code.

## Installation

```bash
pip install anthropic openai python-dotenv numpy scipy matplotlib
```

Créer un fichier `.env` à la racine avec les clés API :

```
ANTHROPIC_API_KEY=...
DEEPSEEK_API_KEY=...
```

Seul `ANTHROPIC_API_KEY` est nécessaire pour utiliser Claude (fournisseur par défaut).
`DEEPSEEK_API_KEY` n'est utile que pour comparer avec DeepSeek (`--fournisseur deepseek`).

## Lancer une expérience (outil principal)

`Resultat/outils/lancer_partie.py` fait tourner l'algorithme de son choix sur un niveau
donné et affiche le coût, le nombre d'états visités et le chemin trouvé.

```bash
python Resultat/outils/lancer_partie.py --jeu pathfinding --niveau niveau2_moyen --carte carte1 --mecanisme astar
python Resultat/outils/lancer_partie.py --jeu taquin --niveau niveau1_facile --carte carte2 --mecanisme llm_a_etoile
python Resultat/outils/lancer_partie.py --jeu sokoban --niveau microban/niveau2_moyen --mecanisme point3_elaguer
```

- `--jeu` : `pathfinding`, `taquin` ou `sokoban`
- `--niveau`/`--carte` : pathfinding/taquin utilisent les deux (dossier + fichier, ex. `niveau2_moyen`/`carte1`) ;
  sokoban n'utilise que `--niveau`, avec le chemin complet (ex. `microban/niveau2_moyen`)
- `--mecanisme` : `astar` (baseline, défaut), `point1_departager`, `point2_heuristique`,
  `point3_elaguer` (sokoban uniquement), ou `llm_a_etoile` (reproduction du mécanisme du papier,
  sans garantie d'optimalité)
- `--fournisseur` : `claude` (défaut) ou `deepseek`, ignoré pour `astar`

`python Resultat/outils/lancer_partie.py --help` détaille toutes les options.

## Structure du code

```
Algorithmes/
  A_etoile/                      A* générique (probleme.py = interface abstraite)
  Points_d_insertion_LLM/        les 3 points d'insertion : départager, heuristique, élaguer
  LLM_A_etoile_papier/           reproduction du mécanisme du papier (waypoints/dispositions)
Jeux/
  Recherche_de_chemin/ Taquin/ Sokoban/
                                 un probleme_*.py par jeu (implémente l'interface Probleme),
                                 decrire_pour_llm.py (description texte pour les prompts),
                                 waypoints_llm_a_etoile.py (cout_vers_cible du mécanisme papier)
Resultat/
  lancer_experimentation.py      grande expérimentation (baseline vs 3 points d'insertion, 3 jeux)
  outils/
    lancer_partie.py             outil principal, voir ci-dessus
    lancer_pathfinding_tous_niveaux.py, lancer_taquin_tous_niveaux.py,
    lancer_sokoban_tous_niveaux.py, generer_figures_pathfinding_etoile.py
                                  scripts ayant produit les résultats et figures du rapport
    dessiner_*.py                visualisation matplotlib par jeu
  Recherche_de_chemin/ Taquin/ Sokoban/Experimentation/
                                  résultats bruts (CSV/JSON) et figures utilisés dans le rapport
```

## Reproduire les résultats du rapport

Les scripts `Resultat/outils/lancer_{pathfinding,taquin,sokoban}_tous_niveaux.py` et
`generer_figures_pathfinding_etoile.py` relancent l'intégralité des mesures citées dans le
rapport (plusieurs dizaines d'appels API, quelques minutes). `Resultat/lancer_experimentation.py`
relance la comparaison des 3 points d'insertion sur les 3 jeux. Pour un test ponctuel sur un seul
niveau, préférer `lancer_partie.py` ci-dessus.
