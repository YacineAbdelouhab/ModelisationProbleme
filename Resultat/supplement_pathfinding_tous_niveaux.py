from Jeux.Recherche_de_chemin.probleme_recherche_de_chemin import charger_depuis_fichier
from Jeux.Recherche_de_chemin.decrire_pour_llm import decrire_etat
from Algorithmes.Points_d_insertion_LLM.client_llm import demander_a_deepseek
from Resultat.outils.experimentation import axe1_points_insertion, sauvegarder_csv, ecrire_tableau_markdown

# test supplementaire, hors du pipeline officiel (Resultat/lancer_experimentation.py)
# -- garde dans un fichier a part expres, pour ne pas se faire ecraser/fusionner
# avec les 11 taches officielles en cours (qui continuent de tourner par ailleurs).
# Points 1 et 2 uniquement (pas d'elaguer, ca n'a pas de sens sur Pathfinding),
# sur les 3 niveaux, pour avoir un jeu de donnees complet et coherent en un
# seul run plutot que de recoller des morceaux du pipeline officiel.

DOSSIER = "Resultat/Recherche_de_chemin/Experimentation"
CAP_ETATS = 100_000
MAX_APPELS_API = 150
NIVEAUX = ["niveau1_facile", "niveau2_moyen", "niveau3_difficile"]

if __name__ == "__main__":
    toutes_les_lignes = []
    for niveau in NIVEAUX:
        probleme = charger_depuis_fichier(f"Jeux/Recherche_de_chemin/exemples/{niveau}/carte1.txt")
        lignes = axe1_points_insertion(
            "Recherche_de_chemin", f"{niveau}/carte1 (supplement)", probleme, decrire_etat,
            max_etats_explores=CAP_ETATS, fn_demander=demander_a_deepseek,
            inclure_elaguer=False, max_appels_api=MAX_APPELS_API,
        )
        toutes_les_lignes += lignes

    sauvegarder_csv(toutes_les_lignes, f"{DOSSIER}/supplement_pathfinding_tous_niveaux.csv")
    ecrire_tableau_markdown(toutes_les_lignes, f"{DOSSIER}/supplement_pathfinding_tous_niveaux.md")
    print(f"\nTerminé -> {DOSSIER}/supplement_pathfinding_tous_niveaux.csv")
