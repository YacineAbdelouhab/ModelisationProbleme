import csv
import time

import matplotlib.pyplot as plt

from Algorithmes.A_etoile.a_etoile import a_etoile
from Algorithmes.Points_d_insertion_LLM.client_llm import demander_a_claude, demander_a_deepseek
from Algorithmes.Points_d_insertion_LLM.Ordonner_noeuds_a_explorer.ordonner_noeuds import departager_llm
from Algorithmes.Points_d_insertion_LLM.Calculer_Heuristique_d_un_noeud.heuristique_llm import heuristique_llm, heuristique_llm_lot
from Algorithmes.Points_d_insertion_LLM.Elaguer_les_etats.elaguer_llm import elaguer_llm

CHAMPS_CSV = ["axe", "jeu", "instance", "variante", "cout", "visites", "temps_total_s", "nb_appels_api", "temps_api_s"]


def chronometrer(demander, max_appels=None):
    # enveloppe demander_a_claude/demander_a_deepseek pour compter les
    # appels et mesurer le temps cumule passe DANS l'API elle-meme (latence
    # reseau + modele) -- separe de temps_total_s qui mesure tout a_etoile,
    # cote local compris. Ne touche pas a client_llm.py.
    #
    # max_appels (optionnel) : budget dur sur le nombre d'appels API, plutot
    # que de deviner un cap d'etats qui traduit mal en cout reel (le ratio
    # appels/etat varie par hook et par jeu). Une fois le budget epuise,
    # renvoie une chaine vide au lieu d'appeler l'API -- chaque hook a deja
    # un repli classique prevu pour une reponse inexploitable (voir
    # heuristique_llm/departager_llm/elaguer_llm), donc la recherche
    # continue et finit quand meme, juste sans LLM pour le reste.
    stats = {"nb_appels": 0, "temps_api_s": 0.0, "budget_epuise": False}

    def demander_mesure(prompt, max_tokens=600):
        if max_appels is not None and stats["nb_appels"] >= max_appels:
            stats["budget_epuise"] = True
            return ""  # aucune ligne REPONSE dedans -- declenche le repli classique du hook
        debut = time.perf_counter()
        reponse = demander(prompt, max_tokens=max_tokens)
        stats["temps_api_s"] += time.perf_counter() - debut
        stats["nb_appels"] += 1
        return reponse

    return demander_mesure, stats


def executer_variante(nom_axe, nom_jeu, nom_instance, nom_variante, probleme, kwargs_a_etoile, stats_api=None):
    debut = time.perf_counter()
    _, cout, fermes = a_etoile(probleme, **kwargs_a_etoile)
    duree = time.perf_counter() - debut

    ligne = {
        "axe": nom_axe,
        "jeu": nom_jeu,
        "instance": nom_instance,
        "variante": nom_variante,
        "cout": cout,
        "visites": len(fermes),
        "temps_total_s": round(duree, 3),
        "nb_appels_api": stats_api["nb_appels"] if stats_api else 0,
        "temps_api_s": round(stats_api["temps_api_s"], 3) if stats_api else 0.0,
    }
    print(
        f"[{nom_axe}] {nom_jeu:18s} {nom_instance:20s} {nom_variante:24s} "
        f"cout={cout!s:>5} visites={len(fermes):5d} temps={duree:6.2f}s "
        f"appels={ligne['nb_appels_api']:4d} temps_api={ligne['temps_api_s']:6.2f}s"
    )
    return ligne


# ----- AXE 1 : baseline vs chaque point d'insertion -----
def axe1_points_insertion(nom_jeu, nom_instance, probleme, decrire_etat, max_etats_explores=None,
                           fn_demander=demander_a_claude, inclure_elaguer=True, max_appels_api=None):
    # max_etats_explores : passe directement a a_etoile -- borne le pire cas
    # cote ETATS (utile sur les niveaux difficiles ou l'espace peut exploser)
    # max_appels_api : borne dure sur le nombre d'appels LLM -- une fois
    # atteinte, le hook retombe sur son comportement classique pour le
    # reste de la recherche (voir chronometrer() ci-dessus). Les deux caps
    # sont independants et peuvent etre combines.
    # fn_demander : demander_a_claude ou demander_a_deepseek, interchangeable
    # inclure_elaguer : point3_elaguer n'a de sens que sur des jeux avec une
    # vraie notion de cul-de-sac certain (Sokoban) -- Pathfinding/Taquin ont
    # tout etat reachable resoluble, tester l'elagage dessus ne veut rien dire
    decrire = lambda etat: decrire_etat(probleme, etat)
    lignes = [executer_variante("1_points_insertion", nom_jeu, nom_instance, "baseline", probleme,
                                 {"max_etats_explores": max_etats_explores})]

    demander, stats = chronometrer(fn_demander, max_appels_api)
    kwargs = {"departager_llm": departager_llm(decrire, demander), "max_etats_explores": max_etats_explores}
    lignes.append(executer_variante("1_points_insertion", nom_jeu, nom_instance, "point1_departager", probleme, kwargs, stats))

    demander, stats = chronometrer(fn_demander, max_appels_api)
    kwargs = {"heuristique_llm_lot": heuristique_llm_lot(decrire, probleme.heuristique, demander), "max_etats_explores": max_etats_explores}
    lignes.append(executer_variante("1_points_insertion", nom_jeu, nom_instance, "point2_heuristique_lot", probleme, kwargs, stats))

    if inclure_elaguer:
        demander, stats = chronometrer(fn_demander, max_appels_api)
        kwargs = {"elaguer_llm": elaguer_llm(decrire, demander), "max_etats_explores": max_etats_explores}
        lignes.append(executer_variante("1_points_insertion", nom_jeu, nom_instance, "point3_elaguer", probleme, kwargs, stats))

    return lignes


# ----- AXE 2 : protections du point 2 (on/off), sur un vrai niveau -----
def axe2_protections(nom_jeu, nom_instance, probleme, decrire_etat, max_etats_explores=None,
                      fn_demander=demander_a_claude, max_appels_api=None):
    decrire = lambda etat: decrire_etat(probleme, etat)
    lignes = []
    combinaisons = [
        ("aucune_protection", False, False),
        ("consistance_seule_pathmax", True, False),
        ("admissibilite_seule_min", False, True),
        ("les_deux_protections", True, True),
    ]
    for nom_variante, proteger_consistance, proteger_admissibilite in combinaisons:
        demander, stats = chronometrer(fn_demander, max_appels_api)
        h_lot = heuristique_llm_lot(decrire, probleme.heuristique, demander, proteger_admissibilite=proteger_admissibilite)
        kwargs = {"heuristique_llm_lot": h_lot, "proteger_consistance": proteger_consistance, "max_etats_explores": max_etats_explores}
        lignes.append(executer_variante("2_protections", nom_jeu, nom_instance, nom_variante, probleme, kwargs, stats))
    return lignes


# ----- AXE 3 : un par un vs par lot -----
def axe3_lot_vs_un_par_un(nom_jeu, nom_instance, probleme, decrire_etat, max_etats_explores=None, fn_demander=demander_a_claude):
    decrire = lambda etat: decrire_etat(probleme, etat)
    lignes = []

    demander, stats = chronometrer(fn_demander)
    kwargs = {"heuristique_llm": heuristique_llm(decrire, probleme.heuristique, demander), "max_etats_explores": max_etats_explores}
    lignes.append(executer_variante("3_lot_vs_un_par_un", nom_jeu, nom_instance, "un_par_un", probleme, kwargs, stats))

    demander, stats = chronometrer(fn_demander)
    kwargs = {"heuristique_llm_lot": heuristique_llm_lot(decrire, probleme.heuristique, demander), "max_etats_explores": max_etats_explores}
    lignes.append(executer_variante("3_lot_vs_un_par_un", nom_jeu, nom_instance, "par_lot", probleme, kwargs, stats))

    return lignes


def sauvegarder_csv(lignes, chemin_fichier):
    with open(chemin_fichier, "w", newline="", encoding="utf-8") as fichier:
        writer = csv.DictWriter(fichier, fieldnames=CHAMPS_CSV)
        writer.writeheader()
        writer.writerows(lignes)


def dessiner_barres(lignes, cle_valeur, titre, ylabel, chemin_fichier):
    noms = [l["variante"] for l in lignes]
    valeurs = [l[cle_valeur] for l in lignes]
    fig, ax = plt.subplots(figsize=(max(4.5, len(noms) * 1.4), 4))
    ax.bar(noms, valeurs, color="steelblue")
    ax.set_title(titre, fontsize=12)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Variante")
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    fig.tight_layout()
    fig.savefig(chemin_fichier, dpi=120)
    plt.close(fig)

    # sauvegarde aussi les valeurs exactes tracees (meme nom, .csv) -- pour
    # pouvoir reformater le graphe plus tard (autre style, figure combinee...)
    # sans avoir a relancer les appels API
    chemin_csv = chemin_fichier.rsplit(".", 1)[0] + ".csv"
    with open(chemin_csv, "w", newline="", encoding="utf-8") as fichier:
        writer = csv.writer(fichier)
        writer.writerow(["variante", cle_valeur])
        writer.writerows(zip(noms, valeurs))


def ecrire_tableau_markdown(lignes, chemin_fichier):
    with open(chemin_fichier, "w", encoding="utf-8") as fichier:
        fichier.write("# Résultats d'expérimentation\n\n")
        axes = sorted(set(l["axe"] for l in lignes))
        for axe in axes:
            fichier.write(f"## Axe {axe}\n\n")
            fichier.write("| Jeu | Instance | Variante | Coût | Visites | Temps total (s) | Appels API | Temps API (s) |\n")
            fichier.write("|---|---|---|---|---|---|---|---|\n")
            for l in lignes:
                if l["axe"] != axe:
                    continue
                fichier.write(
                    f"| {l['jeu']} | {l['instance']} | {l['variante']} | {l['cout']} | {l['visites']} | "
                    f"{l['temps_total_s']} | {l['nb_appels_api']} | {l['temps_api_s']} |\n"
                )
            fichier.write("\n")
