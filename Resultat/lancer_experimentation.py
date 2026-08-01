import csv
import os
import sys
from collections import defaultdict

import matplotlib.pyplot as plt

from Jeux.Recherche_de_chemin.probleme_recherche_de_chemin import charger_depuis_fichier as charger_pathfinding
from Jeux.Recherche_de_chemin.decrire_pour_llm import decrire_etat as decrire_pathfinding

from Jeux.Taquin.probleme_taquin import charger_depuis_fichier as charger_taquin
from Jeux.Taquin.decrire_pour_llm import decrire_etat as decrire_taquin

from Jeux.Sokoban.probleme_sokoban import charger_depuis_fichier as charger_sokoban
from Jeux.Sokoban.decrire_pour_llm import decrire_etat as decrire_sokoban

from Algorithmes.Points_d_insertion_LLM.client_llm import demander_a_deepseek

from Resultat.outils.dessiner_recherche_de_chemin import dessiner_recherche_de_chemin
from Resultat.outils.dessiner_taquin import dessiner_taquin
from Resultat.outils.dessiner_sokoban import dessiner_sokoban

from Resultat.outils.experimentation import (
    axe1_points_insertion,
    axe2_protections,
    sauvegarder_csv,
    dessiner_barres,
    ecrire_tableau_markdown,
)

# Note pour le rapport : heuristique_llm existe aussi en version "un par un",
# mais seule la version par lot (heuristique_llm_lot) est utilisee ici --
# deja verifie ailleurs (voir notes_rapport.md) que les deux donnent
# EXACTEMENT le meme resultat (55 vs 33 appels API pour le meme cout et les
# memes visites), le lot est retenu uniquement pour limiter les appels API.

CAP_ETATS_STANDARD = 100_000  # genereux : couvre meme Sokoban microban niveau4 (56 240)
CAP_ETATS_ORIGINAL = 250_000  # Sokoban original a besoin de bien plus (voir sweep dans notes_rapport.md)
MAX_APPELS_API = 150  # borne le cout REEL peu importe la taille du niveau -- une fois atteint,
# chaque hook retombe sur son repli classique pour le reste de la recherche (voir chronometrer())
FN_DEMANDER = demander_a_deepseek

DOSSIERS = {
    "Recherche_de_chemin": "Resultat/Recherche_de_chemin/Experimentation",
    "Taquin": "Resultat/Taquin/Experimentation",
    "Sokoban": "Resultat/Sokoban/Experimentation",
}

DESSINER = {
    "Recherche_de_chemin": lambda p, ax: dessiner_recherche_de_chemin(p, chemin=None, visites=None, ax=ax),
    "Taquin": lambda p, ax: dessiner_taquin(p, ax=ax),
    "Sokoban": lambda p, ax: dessiner_sokoban(p, ax=ax),
}


def sauvegarder_apercu(nom_jeu, probleme, nom_instance):
    dossier = DOSSIERS[nom_jeu]
    os.makedirs(dossier, exist_ok=True)
    fig, ax = plt.subplots(figsize=(5, 5))
    DESSINER[nom_jeu](probleme, ax)
    ax.set_title(f"{nom_jeu} — {nom_instance}", fontsize=10)
    fig.tight_layout()
    nom_fichier = nom_instance.replace("/", "_")
    fig.savefig(f"{dossier}/apercu_{nom_fichier}.png", dpi=110)
    plt.close(fig)


def tache_axe1(nom_jeu, nom_instance, charger, decrire_etat, chemin, cap_etats, inclure_elaguer):
    # renvoie une fonction sans argument (executee seulement quand la tache
    # est reellement lancee, pas au moment de construire le registre)
    def executer():
        probleme = charger(chemin)
        sauvegarder_apercu(nom_jeu, probleme, nom_instance)
        return axe1_points_insertion(nom_jeu, nom_instance, probleme, decrire_etat,
                                      max_etats_explores=cap_etats, fn_demander=FN_DEMANDER,
                                      inclure_elaguer=inclure_elaguer, max_appels_api=MAX_APPELS_API)
    return executer


def tache_axe2():
    def executer():
        probleme = charger_pathfinding("Jeux/Recherche_de_chemin/exemples/niveau1_facile/carte1.txt")
        return axe2_protections("Recherche_de_chemin", "niveau1_facile/carte1", probleme, decrire_pathfinding,
                                 max_etats_explores=CAP_ETATS_STANDARD, fn_demander=FN_DEMANDER,
                                 max_appels_api=MAX_APPELS_API)
    return executer


# registre de toutes les taches : id -> (jeu, fonction sans argument qui
# renvoie les lignes) -- chaque tache = un process independant possible
TACHES = {
    "pathfinding_niveau2": ("Recherche_de_chemin", tache_axe1(
        "Recherche_de_chemin", "niveau2_moyen/carte1", charger_pathfinding, decrire_pathfinding,
        "Jeux/Recherche_de_chemin/exemples/niveau2_moyen/carte1.txt", CAP_ETATS_STANDARD, False)),
    "pathfinding_niveau3": ("Recherche_de_chemin", tache_axe1(
        "Recherche_de_chemin", "niveau3_difficile/carte1", charger_pathfinding, decrire_pathfinding,
        "Jeux/Recherche_de_chemin/exemples/niveau3_difficile/carte1.txt", CAP_ETATS_STANDARD, False)),
    "pathfinding_axe2": ("Recherche_de_chemin", tache_axe2()),

    "taquin_niveau2": ("Taquin", tache_axe1(
        "Taquin", "niveau2_moyen/carte1", charger_taquin, decrire_taquin,
        "Jeux/Taquin/exemples/niveau2_moyen/carte1.txt", CAP_ETATS_STANDARD, False)),
    "taquin_niveau3": ("Taquin", tache_axe1(
        "Taquin", "niveau3_difficile/carte1", charger_taquin, decrire_taquin,
        "Jeux/Taquin/exemples/niveau3_difficile/carte1.txt", CAP_ETATS_STANDARD, False)),

    "sokoban_microban_niveau0": ("Sokoban", tache_axe1(
        "Sokoban", "microban/niveau0_trivial", charger_sokoban, decrire_sokoban,
        "Jeux/Sokoban/exemples/microban/niveau0_trivial.txt", CAP_ETATS_STANDARD, True)),
    "sokoban_microban_niveau1": ("Sokoban", tache_axe1(
        "Sokoban", "microban/niveau1_facile", charger_sokoban, decrire_sokoban,
        "Jeux/Sokoban/exemples/microban/niveau1_facile.txt", CAP_ETATS_STANDARD, True)),
    "sokoban_microban_niveau2": ("Sokoban", tache_axe1(
        "Sokoban", "microban/niveau2_moyen", charger_sokoban, decrire_sokoban,
        "Jeux/Sokoban/exemples/microban/niveau2_moyen.txt", CAP_ETATS_STANDARD, True)),
    "sokoban_microban_niveau3": ("Sokoban", tache_axe1(
        "Sokoban", "microban/niveau3_difficile", charger_sokoban, decrire_sokoban,
        "Jeux/Sokoban/exemples/microban/niveau3_difficile.txt", CAP_ETATS_STANDARD, True)),
    "sokoban_microban_niveau4": ("Sokoban", tache_axe1(
        "Sokoban", "microban/niveau4_tres_difficile", charger_sokoban, decrire_sokoban,
        "Jeux/Sokoban/exemples/microban/niveau4_tres_difficile.txt", CAP_ETATS_STANDARD, True)),
    "sokoban_original_niveau1": ("Sokoban", tache_axe1(
        "Sokoban", "original/niveau1", charger_sokoban, decrire_sokoban,
        "Jeux/Sokoban/exemples/original/niveau1.txt", CAP_ETATS_ORIGINAL, True)),
}


def executer_tache(id_tache):
    nom_jeu, fonction = TACHES[id_tache]
    dossier = DOSSIERS[nom_jeu]
    os.makedirs(dossier, exist_ok=True)
    print(f"\n===== TÂCHE : {id_tache} =====")
    lignes = fonction()
    # chaque tache ecrit dans SON PROPRE fichier -- jamais le meme fichier
    # que 2 taches en parallele, aucun risque d'ecrasement mutuel
    sauvegarder_csv(lignes, f"{dossier}/partiel_{id_tache}.csv")
    print(f"{id_tache} terminée : {len(lignes)} lignes -> {dossier}/partiel_{id_tache}.csv")


def dessiner_moyennes_axe1(nom_jeu, lignes_axe1, dossier):
    somme = defaultdict(lambda: {"visites": 0, "temps": 0.0, "n": 0})
    for l in lignes_axe1:
        s = somme[l["variante"]]
        s["visites"] += l["visites"] or 0
        s["temps"] += l["temps_total_s"] or 0
        s["n"] += 1
    lignes_moy = [
        {"variante": v, "visites": s["visites"] / s["n"], "temps_total_s": s["temps"] / s["n"]}
        for v, s in somme.items()
    ]
    dessiner_barres(lignes_moy, "visites", f"États explorés (moyenne) — {nom_jeu}", "États explorés (moy.)",
                     f"{dossier}/axe1_visites_moyenne.png")
    dessiner_barres(lignes_moy, "temps_total_s", f"Temps de recherche (moyenne) — {nom_jeu}", "Temps (s, moy.)",
                     f"{dossier}/axe1_temps_moyenne.png")


def fusionner():
    # relit tous les partiel_*.csv de chaque jeu (produits par des taches
    # potentiellement lancees dans des process separes) et recombine en
    # resultats.csv + tableau_final.md + graphes -- a lancer une fois que
    # toutes les taches individuelles sont terminees
    for nom_jeu, dossier in DOSSIERS.items():
        if not os.path.isdir(dossier):
            continue
        lignes = []
        for nom_fichier in sorted(os.listdir(dossier)):
            if nom_fichier.startswith("partiel_") and nom_fichier.endswith(".csv"):
                with open(f"{dossier}/{nom_fichier}", encoding="utf-8") as f:
                    lignes += list(csv.DictReader(f))
        if not lignes:
            continue

        for l in lignes:  # le csv relit tout en texte -- reconvertit les champs numeriques
            for champ in ("cout", "visites", "nb_appels_api"):
                l[champ] = int(l[champ]) if l[champ] not in ("", "None") else None
            for champ in ("temps_total_s", "temps_api_s"):
                l[champ] = float(l[champ]) if l[champ] not in ("", "None") else None

        sauvegarder_csv(lignes, f"{dossier}/resultats.csv")
        ecrire_tableau_markdown(lignes, f"{dossier}/tableau_final.md")

        lignes_axe1 = [l for l in lignes if l["axe"] == "1_points_insertion"]
        if lignes_axe1:
            dessiner_moyennes_axe1(nom_jeu, lignes_axe1, dossier)

        print(f"{nom_jeu} fusionné : {len(lignes)} lignes -> {dossier}/resultats.csv")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--fusionner":
        fusionner()
    elif len(sys.argv) > 1 and sys.argv[1] in TACHES:
        executer_tache(sys.argv[1])
    elif len(sys.argv) > 1:
        print(f"Tâche inconnue : {sys.argv[1]}. Tâches disponibles : {list(TACHES)}")
    else:
        for id_tache in TACHES:
            executer_tache(id_tache)
        fusionner()
