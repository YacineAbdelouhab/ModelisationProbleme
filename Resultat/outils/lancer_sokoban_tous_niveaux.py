import json
import re
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from Algorithmes.A_etoile.a_etoile import a_etoile
from Algorithmes.LLM_A_etoile_papier.llm_a_etoile_papier import llm_a_etoile_papier
from Algorithmes.Points_d_insertion_LLM.client_llm import demander_a_claude, demander_a_deepseek
from Jeux.Sokoban.decrire_pour_llm import decrire_etat
from Jeux.Sokoban.probleme_sokoban import charger_depuis_fichier

DOSSIER_SORTIE = RACINE / "Resultat" / "Sokoban" / "Experimentation"


def cout_vers_cible(disposition_cible, etat):
    # cout_vers_cible officiel de Jeux/Sokoban/waypoints_llm_a_etoile.py attend UNE
    # SEULE cible (mecanisme incremental) -- ici chaque "cible" est une disposition
    # COMPLETE (mecanisme par lot, comme Taquin) : affectation hongroise entre
    # les caisses actuelles et celles de la disposition cible, somme des distances
    # de Manhattan, generalisation de probleme.heuristique() a deux dispositions
    # quelconques (pas seulement caisses -> cibles fixes du jeu).
    caisses = list(etat.caisses)
    cibles = list(disposition_cible)
    if not caisses:
        return 0
    couts = np.array(
        [[abs(cx - tx) + abs(cy - ty) for (tx, ty) in cibles] for (cx, cy) in caisses]
    )
    lignes, colonnes = linear_sum_assignment(couts)
    return int(couts[lignes, colonnes].sum())

NIVEAUX = [
    "niveau0_trivial", "niveau1_facile", "niveau2_moyen", "niveau3_difficile", "niveau4_tres_difficile",
]

TOKENS = {"Claude": 16000, "DeepSeek": 48000}


def generer_dispositions_avec_intermediaires(probleme, demander, tokens, max_essais=3):
    caisses_depart = list(probleme.etat_initial.caisses)
    cibles = list(probleme.cibles)
    couts = np.array([[abs(cx - tx) + abs(cy - ty) for (tx, ty) in cibles] for (cx, cy) in caisses_depart])
    lignes, colonnes = linear_sum_assignment(couts)
    affectation = [(caisses_depart[i], cibles[j]) for i, j in zip(lignes, colonnes)]

    prompt = (
        "Voici une carte de Sokoban et l'affectation caisse -> cible la "
        "plus courte au total (calculée sans tenir compte de l'ordre) :\n"
        + "\n".join(f"Caisse en {c} -> cible en {t}" for c, t in affectation)
        + "\n\n" + decrire_etat(probleme, probleme.etat_initial)
        + "\n\nContexte : ces dispositions vont guider une recherche A* -- "
        "de bonnes dispositions intermédiaires réduisent fortement le "
        "nombre d'états explorés, de mauvaises peuvent bloquer des caisses "
        "ou ralentir la recherche.\n\n"
        "En partant de la disposition actuelle des caisses et en allant "
        "vers la disposition finale (chaque caisse sur sa cible assignée), "
        "donne 2 ou 3 dispositions INTERMÉDIAIRES plausibles (uniquement "
        "les positions des caisses, pas le joueur). Termine par exactement "
        "une ligne par disposition, au format 'DISPOSITION i: (x,y) (x,y) "
        "...'"
    )

    nb_caisses = len(cibles)
    disposition_finale = frozenset(t for c, t in affectation)
    for essai in range(max_essais):
        texte = demander(prompt, max_tokens=tokens)
        dispositions = []
        for i in range(1, 10):
            trouve = re.search(rf"DISPOSITION\s*{i}\s*:\s*(.+)", texte)
            if not trouve:
                break
            paires = re.findall(r"\((\d+)\s*,\s*(\d+)\)", trouve.group(1))
            disposition = frozenset((int(x), int(y)) for x, y in paires)
            if len(disposition) == nb_caisses:
                dispositions.append(disposition)
        if dispositions:
            return [probleme.etat_initial.caisses] + dispositions + [disposition_finale]
        print(f"  essai {essai + 1}/{max_essais} : aucune disposition, on retente")
    return [probleme.etat_initial.caisses, disposition_finale]


def traiter(niveau, fournisseur_nom, demander):
    chemin_fichier = RACINE / f"Jeux/Sokoban/exemples/microban/{niveau}.txt"
    probleme = charger_depuis_fichier(str(chemin_fichier))

    chemin_base, cout_base, fermes_base = a_etoile(probleme, max_etats_explores=100_000)

    dispositions = generer_dispositions_avec_intermediaires(
        probleme, demander=demander, tokens=TOKENS[fournisseur_nom]
    )
    chemin_wp, cout_wp, fermes_wp = llm_a_etoile_papier(
        probleme, lambda p: dispositions, cout_vers_cible, max_etats_explores=100_000
    )

    nb_intermediaires = max(0, len(dispositions) - 2)
    resultat = {
        "niveau": niveau, "fournisseur": fournisseur_nom,
        "cout_baseline": cout_base, "visites_baseline": len(fermes_base),
        "cout_dispositions": cout_wp, "visites_dispositions": len(fermes_wp) if fermes_wp is not None else None,
        "nb_intermediaires": nb_intermediaires,
    }
    print(
        f"{niveau} [{fournisseur_nom}] : baseline cout={cout_base} visites={len(fermes_base)} "
        f"| LLM-A* cout={cout_wp} visites={len(fermes_wp) if fermes_wp is not None else 'None'} "
        f"intermediaires={nb_intermediaires}"
    )
    return resultat


if __name__ == "__main__":
    resultats = []
    for niveau in NIVEAUX:
        resultats.append(traiter(niveau, "Claude", demander_a_claude))
        resultats.append(traiter(niveau, "DeepSeek", demander_a_deepseek))
    with open(DOSSIER_SORTIE / "sokoban_tous_niveaux.json", "w", encoding="utf-8") as f:
        json.dump(resultats, f, indent=2, ensure_ascii=False)
    print("\nTermine, resultats enregistres dans sokoban_tous_niveaux.json")
