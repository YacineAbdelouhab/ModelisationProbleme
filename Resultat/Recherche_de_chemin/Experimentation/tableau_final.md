# Résultats d'expérimentation

## Axe 1_points_insertion

| Jeu | Instance | Variante | Coût | Visites | Temps total (s) | Appels API | Temps API (s) |
|---|---|---|---|---|---|---|---|
| Recherche_de_chemin | niveau2_moyen/carte1 | baseline | 21 | 110 | 0.001 | 0 | 0.0 |
| Recherche_de_chemin | niveau2_moyen/carte1 | point1_departager | 21 | 109 | 3464.86 | 109 | 3464.811 |
| Recherche_de_chemin | niveau2_moyen/carte1 | point2_heuristique_lot | 21 | 110 | 4582.54 | 106 | 4582.527 |
| Recherche_de_chemin | niveau3_difficile/carte1 | baseline | 42 | 171 | 0.002 | 0 | 0.0 |
| Recherche_de_chemin | niveau3_difficile/carte1 | point1_departager | 42 | 171 | 4854.665 | 150 | 4854.467 |
| Recherche_de_chemin | niveau3_difficile/carte1 | point2_heuristique_lot | 42 | 171 | 7102.57 | 150 | 7102.524 |

## Axe 2_protections

| Jeu | Instance | Variante | Coût | Visites | Temps total (s) | Appels API | Temps API (s) |
|---|---|---|---|---|---|---|---|
| Recherche_de_chemin | niveau1_facile/carte1 | aucune_protection | 10 | 28 | 756.366 | 28 | 756.361 |
| Recherche_de_chemin | niveau1_facile/carte1 | consistance_seule_pathmax | 10 | 30 | 797.75 | 30 | 797.747 |
| Recherche_de_chemin | niveau1_facile/carte1 | admissibilite_seule_min | 10 | 33 | 886.709 | 33 | 886.706 |
| Recherche_de_chemin | niveau1_facile/carte1 | les_deux_protections | 10 | 33 | 906.334 | 33 | 906.331 |

