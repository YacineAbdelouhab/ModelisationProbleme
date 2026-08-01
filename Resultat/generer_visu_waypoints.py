import json
import os

from Algorithmes.A_etoile.a_etoile import a_etoile
from Algorithmes.LLM_A_etoile_papier.llm_a_etoile_papier import llm_a_etoile_papier
from Algorithmes.Points_d_insertion_LLM.client_llm import demander_a_deepseek

from Jeux.Recherche_de_chemin.probleme_recherche_de_chemin import charger_depuis_fichier as charger_pf
from Jeux.Recherche_de_chemin.waypoints_llm_a_etoile import generer_waypoints_llm as gen_wp_pf, cout_vers_cible as cout_pf

from Jeux.Taquin.probleme_taquin import charger_depuis_fichier as charger_taquin
from Jeux.Taquin.waypoints_llm_a_etoile import generer_waypoints_llm as gen_wp_taquin, cout_vers_cible as cout_taquin

from Jeux.Sokoban.probleme_sokoban import charger_depuis_fichier as charger_sokoban
from Jeux.Sokoban.waypoints_llm_a_etoile import generer_dispositions_llm, cout_vers_disposition

from Resultat.outils.dessiner_waypoints import (
    dessiner_waypoints_pathfinding,
    dessiner_dispositions_taquin,
    dessiner_dispositions_sokoban,
)

DOSSIER = "Resultat/Visualisation_Waypoints"
CAP_SOKOBAN_ORIGINAL = 250_000  # meme seuil que le reste du projet pour ce niveau


def sauvegarder_donnees(nom, donnees):
    os.makedirs(DOSSIER, exist_ok=True)
    with open(f"{DOSSIER}/donnees_{nom}.json", "w", encoding="utf-8") as f:
        json.dump(donnees, f, indent=2, ensure_ascii=False)
    print(f"  données sauvegardées -> {DOSSIER}/donnees_{nom}.json")


def tester_pathfinding():
    print("\n===== Pathfinding niveau2_moyen/carte1 =====")
    probleme = charger_pf("Jeux/Recherche_de_chemin/exemples/niveau2_moyen/carte1.txt")
    _, cout_base, fermes_base = a_etoile(probleme)
    waypoints = gen_wp_pf(probleme, demander=demander_a_deepseek)
    chemin, cout, fermes = llm_a_etoile_papier(probleme, lambda p: waypoints, cout_pf)
    print(f"  baseline cout={cout_base} visites={len(fermes_base)} | waypoints cout={cout} visites={len(fermes)}")

    sauvegarder_donnees("pathfinding_niveau2", {
        "cout_baseline": cout_base, "visites_baseline": len(fermes_base),
        "cout_waypoints": cout, "visites_waypoints": len(fermes),
        "waypoints": waypoints, "chemin": chemin,
    })
    titre = f"Pathfinding niveau2_moyen — coût={cout} (baseline={cout_base}), {len(fermes)} états visités (baseline={len(fermes_base)})"
    dessiner_waypoints_pathfinding(probleme, chemin, fermes, waypoints, titre,
                                    f"{DOSSIER}/visu_pathfinding_niveau2.png")


def tester_taquin():
    print("\n===== Taquin niveau2_moyen/carte1 =====")
    probleme = charger_taquin("Jeux/Taquin/exemples/niveau2_moyen/carte1.txt")
    _, cout_base, fermes_base = a_etoile(probleme)
    dispositions = gen_wp_taquin(probleme, demander=demander_a_deepseek)
    chemin, cout, fermes = llm_a_etoile_papier(probleme, lambda p: dispositions, cout_taquin)
    print(f"  baseline cout={cout_base} visites={len(fermes_base)} | dispositions cout={cout} visites={len(fermes)}")

    sauvegarder_donnees("taquin_niveau2", {
        "cout_baseline": cout_base, "visites_baseline": len(fermes_base),
        "cout_dispositions": cout, "visites_dispositions": len(fermes),
        "dispositions": [list(d) for d in dispositions],
    })
    dessiner_dispositions_taquin(dispositions, probleme.n, f"{DOSSIER}/visu_taquin_niveau2.png")


def tester_sokoban(nom_fichier, id_sortie, cap=None):
    print(f"\n===== Sokoban {nom_fichier} =====")
    probleme = charger_sokoban(nom_fichier)
    _, cout_base, fermes_base = a_etoile(probleme, max_etats_explores=cap)
    dispositions = generer_dispositions_llm(probleme, demander=demander_a_deepseek)
    chemin, cout, fermes = llm_a_etoile_papier(probleme, lambda p: dispositions, cout_vers_disposition, max_etats_explores=cap)
    print(f"  baseline cout={cout_base} visites={len(fermes_base)} | dispositions cout={cout} visites={len(fermes)}")

    sauvegarder_donnees(id_sortie, {
        "fichier": nom_fichier,
        "cout_baseline": cout_base, "visites_baseline": len(fermes_base),
        "cout_dispositions": cout, "visites_dispositions": len(fermes),
        "dispositions": [sorted(list(d)) for d in dispositions],
    })
    dessiner_dispositions_sokoban(probleme, dispositions, f"{DOSSIER}/visu_{id_sortie}.png")


if __name__ == "__main__":
    tester_pathfinding()
    tester_taquin()
    tester_sokoban("Jeux/Sokoban/exemples/microban/niveau1_facile.txt", "sokoban_microban_niveau1")
    tester_sokoban("Jeux/Sokoban/exemples/original/niveau1.txt", "sokoban_original_niveau1", cap=CAP_SOKOBAN_ORIGINAL)
    print("\nTerminé.")
