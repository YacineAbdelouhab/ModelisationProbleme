from Jeux.Recherche_de_chemin.probleme_recherche_de_chemin import charger_depuis_fichier
from Jeux.Recherche_de_chemin.decrire_pour_llm import decrire_etat
from Algorithmes.Points_d_insertion_LLM.client_llm import demander_a_deepseek
from Resultat.outils.experimentation import axe1_points_insertion, sauvegarder_csv, ecrire_tableau_markdown

# reprise de supplement_pathfinding_tous_niveaux.py apres une coupure reseau
# (getaddrinfo failed) pendant niveau3_difficile -- niveau1/niveau2 avaient
# deja fini avec succes (voir logs de la tache b2sx3qx30), on les reinjecte
# tels quels au lieu de re-depenser des appels API pour rien.

DOSSIER = "Resultat/Recherche_de_chemin/Experimentation"
CAP_ETATS = 100_000
MAX_APPELS_API = 150

LIGNES_DEJA_FAITES = [
    {"axe": "1_points_insertion", "jeu": "Recherche_de_chemin", "instance": "niveau1_facile/carte1 (supplement)",
     "variante": "baseline", "cout": 10, "visites": 33, "temps_total_s": 0.0, "nb_appels_api": 0, "temps_api_s": 0.0},
    {"axe": "1_points_insertion", "jeu": "Recherche_de_chemin", "instance": "niveau1_facile/carte1 (supplement)",
     "variante": "point1_departager", "cout": 10, "visites": 31, "temps_total_s": 1001.68, "nb_appels_api": 31, "temps_api_s": 1001.67},
    {"axe": "1_points_insertion", "jeu": "Recherche_de_chemin", "instance": "niveau1_facile/carte1 (supplement)",
     "variante": "point2_heuristique_lot", "cout": 10, "visites": 33, "temps_total_s": 1124.74, "nb_appels_api": 33, "temps_api_s": 1124.74},

    {"axe": "1_points_insertion", "jeu": "Recherche_de_chemin", "instance": "niveau2_moyen/carte1 (supplement)",
     "variante": "baseline", "cout": 21, "visites": 110, "temps_total_s": 0.0, "nb_appels_api": 0, "temps_api_s": 0.0},
    {"axe": "1_points_insertion", "jeu": "Recherche_de_chemin", "instance": "niveau2_moyen/carte1 (supplement)",
     "variante": "point1_departager", "cout": 21, "visites": 109, "temps_total_s": 3574.81, "nb_appels_api": 109, "temps_api_s": 3574.75},
    {"axe": "1_points_insertion", "jeu": "Recherche_de_chemin", "instance": "niveau2_moyen/carte1 (supplement)",
     "variante": "point2_heuristique_lot", "cout": 21, "visites": 110, "temps_total_s": 4000.53, "nb_appels_api": 106, "temps_api_s": 4000.52},
]

if __name__ == "__main__":
    probleme = charger_depuis_fichier("Jeux/Recherche_de_chemin/exemples/niveau3_difficile/carte1.txt")
    lignes_niveau3 = axe1_points_insertion(
        "Recherche_de_chemin", "niveau3_difficile/carte1 (supplement)", probleme, decrire_etat,
        max_etats_explores=CAP_ETATS, fn_demander=demander_a_deepseek,
        inclure_elaguer=False, max_appels_api=MAX_APPELS_API,
    )

    toutes_les_lignes = LIGNES_DEJA_FAITES + lignes_niveau3
    sauvegarder_csv(toutes_les_lignes, f"{DOSSIER}/supplement_pathfinding_tous_niveaux.csv")
    ecrire_tableau_markdown(toutes_les_lignes, f"{DOSSIER}/supplement_pathfinding_tous_niveaux.md")
    print(f"\nTerminé -> {DOSSIER}/supplement_pathfinding_tous_niveaux.csv")
