import json
import os

from Algorithmes.A_etoile.a_etoile import a_etoile
from Algorithmes.LLM_A_etoile_papier.llm_a_etoile_papier import llm_a_etoile_papier
from Algorithmes.Points_d_insertion_LLM.client_llm import demander_a_claude, demander_a_deepseek

from Jeux.Recherche_de_chemin.probleme_recherche_de_chemin import charger_depuis_fichier as charger_pf
from Jeux.Recherche_de_chemin.waypoints_llm_a_etoile import generer_waypoints_llm as gen_wp_pf, cout_vers_cible as cout_pf

from Jeux.Taquin.probleme_taquin import charger_depuis_fichier as charger_taquin
from Jeux.Taquin.waypoints_llm_a_etoile import generer_waypoints_llm as gen_wp_taquin, cout_vers_cible as cout_taquin

from Jeux.Sokoban.probleme_sokoban import charger_depuis_fichier as charger_sokoban
from Jeux.Sokoban.waypoints_llm_a_etoile import (
    generer_dispositions_llm,
    cout_vers_disposition,
    generer_dispositions_llm_avec_joueur,
    cout_vers_disposition_avec_joueur,
)

DOSSIER = "Resultat/Visualisation_Waypoints"
CAP_SOKOBAN_ORIGINAL = 250_000
NB_ESSAIS = 3
FOURNISSEURS = [("Claude", demander_a_claude), ("DeepSeek", demander_a_deepseek)]

# note : tous les prompts (Pathfinding, Taquin, Sokoban) utilisent la
# representation ASCII par defaut (decrire_etat, pas decrire_etat_tableau) --
# deja confirme meilleure en moyenne sur le test de representation

INSTANCES_PATHFINDING = ["niveau1_facile", "niveau2_moyen", "niveau3_difficile"]
INSTANCES_TAQUIN = ["niveau1_facile", "niveau2_moyen", "niveau3_difficile"]
INSTANCES_SOKOBAN_MICROBAN = ["niveau0_trivial", "niveau1_facile", "niveau2_moyen", "niveau3_difficile", "niveau4_tres_difficile"]


def sauvegarder(nom, donnees):
    os.makedirs(DOSSIER, exist_ok=True)
    with open(f"{DOSSIER}/comparaison_{nom}.json", "w", encoding="utf-8") as f:
        json.dump(donnees, f, indent=2, ensure_ascii=False)


def enregistrer(resultats, instance, nom_fournisseur, cout_base, cout, visites, nb_dispositions):
    resultats.setdefault(instance, {}).setdefault(nom_fournisseur, []).append(
        {"cout": cout, "optimal": cout == cout_base, "visites": visites, "nb_dispositions": nb_dispositions}
    )


def afficher_resume(resultats):
    print("\n--- résumé ---")
    for instance, par_fournisseur in resultats.items():
        for nom, essais in par_fournisseur.items():
            visites = [e["visites"] for e in essais]
            optimaux = sum(1 for e in essais if e["optimal"])
            print(f"{instance:35s} {nom:10s} : optimal {optimaux}/{len(essais)} | visites moy={sum(visites)/len(visites):.1f} (min={min(visites)}, max={max(visites)})")


# ----- AXE 1 : Claude vs DeepSeek, sur chaque niveau de chaque jeu, 3 essais chacun -----
def comparer_fournisseurs():
    resultats = {}

    print("\n===== Pathfinding =====")
    for niveau in INSTANCES_PATHFINDING:
        pf = charger_pf(f"Jeux/Recherche_de_chemin/exemples/{niveau}/carte1.txt")
        _, cout_base, fermes_base = a_etoile(pf)
        print(f"{niveau} baseline : cout={cout_base} visites={len(fermes_base)}")
        for essai in range(1, NB_ESSAIS + 1):
            for nom, demander in FOURNISSEURS:
                wp = gen_wp_pf(pf, demander=demander)
                _, cout, fermes = llm_a_etoile_papier(pf, lambda p: wp, cout_pf)
                print(f"  [essai {essai}] {nom} : cout={cout} visites={len(fermes)}")
                enregistrer(resultats, f"pathfinding_{niveau}", nom, cout_base, cout, len(fermes), len(wp) - 2)

    print("\n===== Taquin =====")
    for niveau in INSTANCES_TAQUIN:
        taquin = charger_taquin(f"Jeux/Taquin/exemples/{niveau}/carte1.txt")
        _, cout_base, fermes_base = a_etoile(taquin)
        print(f"{niveau} baseline : cout={cout_base} visites={len(fermes_base)}")
        for essai in range(1, NB_ESSAIS + 1):
            for nom, demander in FOURNISSEURS:
                disp = gen_wp_taquin(taquin, demander=demander)
                _, cout, fermes = llm_a_etoile_papier(taquin, lambda p: disp, cout_taquin)
                print(f"  [essai {essai}] {nom} : cout={cout} visites={len(fermes)}")
                enregistrer(resultats, f"taquin_{niveau}", nom, cout_base, cout, len(fermes), len(disp) - 2)

    print("\n===== Sokoban microban =====")
    for niveau in INSTANCES_SOKOBAN_MICROBAN:
        sokoban = charger_sokoban(f"Jeux/Sokoban/exemples/microban/{niveau}.txt")
        _, cout_base, fermes_base = a_etoile(sokoban)
        print(f"{niveau} baseline : cout={cout_base} visites={len(fermes_base)}")
        for essai in range(1, NB_ESSAIS + 1):
            for nom, demander in FOURNISSEURS:
                disp = generer_dispositions_llm(sokoban, demander=demander)
                _, cout, fermes = llm_a_etoile_papier(sokoban, lambda p: disp, cout_vers_disposition)
                print(f"  [essai {essai}] {nom} : cout={cout} visites={len(fermes)}")
                enregistrer(resultats, f"sokoban_microban_{niveau}", nom, cout_base, cout, len(fermes), len(disp) - 2)

    print("\n===== Sokoban original niveau1 =====")
    sokoban_orig = charger_sokoban("Jeux/Sokoban/exemples/original/niveau1.txt")
    _, cout_base, fermes_base = a_etoile(sokoban_orig, max_etats_explores=CAP_SOKOBAN_ORIGINAL)
    print(f"baseline : cout={cout_base} visites={len(fermes_base)}")
    for essai in range(1, NB_ESSAIS + 1):
        for nom, demander in FOURNISSEURS:
            disp = generer_dispositions_llm(sokoban_orig, demander=demander)
            _, cout, fermes = llm_a_etoile_papier(sokoban_orig, lambda p: disp, cout_vers_disposition, max_etats_explores=CAP_SOKOBAN_ORIGINAL)
            print(f"  [essai {essai}] {nom} : cout={cout} visites={len(fermes)}")
            enregistrer(resultats, "sokoban_original_niveau1", nom, cout_base, cout, len(fermes), len(disp) - 2)

    sauvegarder("fournisseurs", resultats)
    afficher_resume(resultats)


# ----- AXE 2 : position du joueur avec/sans, sur petit.txt, Claude, 3 essais chacun -----
def comparer_position_joueur():
    print("\n===== Position du joueur avec/sans (Claude, 3 essais chacun) =====")
    sokoban = charger_sokoban("Jeux/Sokoban/exemples/test_llm/petit.txt")
    _, cout_base, fermes_base = a_etoile(sokoban)
    print(f"baseline : cout={cout_base} visites={len(fermes_base)}")

    resultats = {"sans_joueur": [], "avec_joueur": []}
    for essai in range(1, NB_ESSAIS + 1):
        disp_sans = generer_dispositions_llm(sokoban, demander=demander_a_claude)
        _, cout_sans, fermes_sans = llm_a_etoile_papier(sokoban, lambda p: disp_sans, cout_vers_disposition)
        print(f"  [essai {essai}] SANS joueur : cout={cout_sans} visites={len(fermes_sans)} | {len(disp_sans) - 2} disposition(s)")
        resultats["sans_joueur"].append({"cout": cout_sans, "visites": len(fermes_sans), "nb_dispositions": len(disp_sans) - 2})

        disp_avec = generer_dispositions_llm_avec_joueur(sokoban, demander=demander_a_claude)
        _, cout_avec, fermes_avec = llm_a_etoile_papier(sokoban, lambda p: disp_avec, cout_vers_disposition_avec_joueur)
        print(f"  [essai {essai}] AVEC joueur : cout={cout_avec} visites={len(fermes_avec)} | {len(disp_avec) - 2} disposition(s)")
        resultats["avec_joueur"].append({"cout": cout_avec, "visites": len(fermes_avec), "nb_dispositions": len(disp_avec) - 2})

    sauvegarder("position_joueur", resultats)

    print("\n--- résumé position joueur ---")
    for nom, essais in resultats.items():
        visites = [e["visites"] for e in essais]
        optimaux = sum(1 for e in essais if e["cout"] == cout_base)
        print(f"{nom:15s} : optimal {optimaux}/{len(essais)} | visites moy={sum(visites)/len(visites):.1f} (min={min(visites)}, max={max(visites)})")


if __name__ == "__main__":
    comparer_fournisseurs()
    comparer_position_joueur()
    print("\nTerminé.")
