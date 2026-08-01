import re

import numpy as np
from scipy.optimize import linear_sum_assignment

from Algorithmes.Points_d_insertion_LLM.client_llm import demander_a_claude
from Jeux.Sokoban.decrire_pour_llm import decrire_etat


def choisir_prochaine_cible_llm(probleme, etat, cibles_non_remplies, demander=demander_a_claude):
    # cibles_non_remplies : ensemble de (x,y), les cibles pas encore
    # occupees par une caisse. On montre l'affectation hongroise (deja
    # calculee classiquement, fiable) comme repere, mais c'est le LLM qui
    # choisit LA PROCHAINE cible a prioriser, a partir de l'etat REEL --
    # pas un plan fige a l'avance (voir llm_a_etoile_papier_incremental.py)
    cibles_non_remplies = sorted(cibles_non_remplies)
    if len(cibles_non_remplies) == 1:
        return cibles_non_remplies[0]  # rien a choisir

    caisses = sorted(etat.caisses)
    couts = np.array([[abs(cx - tx) + abs(cy - ty) for (tx, ty) in cibles_non_remplies] for (cx, cy) in caisses])
    lignes, colonnes = linear_sum_assignment(couts)
    affectation = [(caisses[i], cibles_non_remplies[j]) for i, j in zip(lignes, colonnes)]

    prompt = (
        "Voici une carte de Sokoban et l'affectation caisse -> cible la "
        "plus courte au total (calculée sans tenir compte de l'ordre) :\n"
        + "\n".join(f"Caisse en {c} -> cible en {t}" for c, t in affectation)
        + "\n\n" + decrire_etat(probleme, etat)
        + "\n\nContexte : ce choix guide une recherche A* incrémentale -- "
        "prioriser la bonne cible réduit le nombre d'états explorés, un "
        "mauvais choix peut faire tourner la recherche en rond ou bloquer "
        "d'autres caisses. Prends tout le temps de réflexion nécessaire.\n\n"
        "Parmi les cibles pas encore occupées, laquelle faudrait-il "
        "remplir en PREMIER maintenant ? Une caisse posée trop tôt peut en "
        "bloquer une autre. Termine par exactement une ligne 'REPONSE: "
        "(x,y)' avec la cible choisie.\n"
        f"Cibles non remplies : {cibles_non_remplies}"
    )
    texte = demander(prompt, max_tokens=2000)

    trouve = re.search(r"REPONSE:\s*\((\d+)\s*,\s*(\d+)\)", texte)
    if trouve:
        cible = (int(trouve.group(1)), int(trouve.group(2)))
        if cible in cibles_non_remplies:
            return cible
    return cibles_non_remplies[0]  # repli : la premiere par ordre naturel si reponse inexploitable


def cout_vers_cible(cible, etat):
    # 0 si une caisse occupe deja cette cible precise, sinon distance de la
    # caisse la plus proche de cette cible (n'importe laquelle -- pas de
    # notion d'identite de caisse, juste "la cible est remplie ou pas")
    if cible in etat.caisses:
        return 0
    return min(abs(cx - cible[0]) + abs(cy - cible[1]) for cx, cy in etat.caisses)


def _cout_affectation(caisses, cibles):
    caisses, cibles = list(caisses), list(cibles)
    couts = np.array([[abs(cx - tx) + abs(cy - ty) for (tx, ty) in cibles] for (cx, cy) in caisses])
    lignes, colonnes = linear_sum_assignment(couts)
    return couts[lignes, colonnes]


# ----- Version "classique" (un seul appel, comme Pathfinding/Taquin) -----
# alternative a choisir_prochaine_cible_llm ci-dessus : au lieu de
# redemander une cible a chaque fois (adaptatif), on demande une sequence
# COMPLETE de dispositions de caisses en un seul appel, a utiliser avec le
# moteur classique llm_a_etoile_papier.py (pas la version incrementale).
# Compromis inverse : moins d'appels, mais un plan fige a l'avance -- exactement
# le risque que la litterature signale pour Sokoban (sous-objectifs qui
# s'interferent), voir notes_rapport.md. Les deux versions sont gardees pour
# pouvoir comparer.
def generer_dispositions_llm(probleme, demander=demander_a_claude, decrire_etat=decrire_etat):
    # decrire_etat : fonction (probleme, etat) -> texte -- decrire_etat ou
    # decrire_etat_tableau (Jeux/Sokoban/decrire_pour_llm.py), pour comparer
    # les deux representations sur ce meme mecanisme
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
        "ou ralentir la recherche. Prends tout le temps de réflexion "
        "nécessaire.\n\n"
        "En partant de la disposition actuelle des caisses et en allant "
        "vers la disposition finale (chaque caisse sur sa cible assignée), "
        "donne 2 ou 3 dispositions INTERMÉDIAIRES plausibles (uniquement "
        "les positions des caisses, pas le joueur). Termine par exactement "
        "une ligne par disposition, au format 'DISPOSITION i: (x,y) (x,y) "
        "...'"
    )
    texte = demander(prompt, max_tokens=3000)

    nb_caisses = len(cibles)
    dispositions = []
    for i in range(1, 10):
        trouve = re.search(rf"DISPOSITION\s*{i}\s*:\s*(.+)", texte)
        if not trouve:
            break
        paires = re.findall(r"\((\d+)\s*,\s*(\d+)\)", trouve.group(1))
        disposition = frozenset((int(x), int(y)) for x, y in paires)
        if len(disposition) == nb_caisses:  # doit avoir autant de positions que de caisses
            dispositions.append(disposition)

    disposition_finale = frozenset(t for c, t in affectation)  # jamais inventee, garantie valide
    return [probleme.etat_initial.caisses] + dispositions + [disposition_finale]


def cout_vers_disposition(disposition_cible, etat):
    # generalisation par affectation hongroise : distance totale entre les
    # caisses actuelles et la disposition visee -- 0 ssi les deux ensembles
    # de positions sont identiques (peu importe quelle caisse va ou)
    if etat.caisses == disposition_cible:
        return 0
    return int(_cout_affectation(etat.caisses, disposition_cible).sum())


# ----- Variante avec position du joueur, pour comparer -----
# meme principe que generer_dispositions_llm/cout_vers_disposition, mais le
# LLM precise aussi OU doit etre le joueur a chaque etape (pas juste les
# caisses) -- plus fidele a la vraie difficulte de Sokoban (il faut etre du
# bon cote d'une caisse pour la pousser), au prix d'un prompt/parsing plus
# complexe. Position joueur ignoree sur la disposition finale (le but reel
# ne contraint pas le joueur, voir Probleme.est_but).
def generer_dispositions_llm_avec_joueur(probleme, demander=demander_a_claude):
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
        "ou ralentir la recherche. La position du joueur compte : il doit "
        "être du bon côté d'une caisse pour pouvoir la pousser dans la "
        "direction voulue. Prends tout le temps de réflexion nécessaire.\n\n"
        "En partant de la disposition actuelle et en allant vers la "
        "disposition finale (chaque caisse sur sa cible assignée), donne 2 "
        "ou 3 dispositions INTERMÉDIAIRES plausibles, en précisant à "
        "chaque fois la position du JOUEUR et celle des CAISSES. Termine "
        "par exactement une ligne par disposition, au format 'DISPOSITION "
        "i: JOUEUR (x,y) CAISSES (x,y) (x,y) ...'"
    )
    texte = demander(prompt, max_tokens=3000)

    nb_caisses = len(cibles)
    dispositions = []
    for i in range(1, 10):
        trouve = re.search(rf"DISPOSITION\s*{i}\s*:\s*JOUEUR\s*\((\d+)\s*,\s*(\d+)\)\s*CAISSES\s*(.+)", texte)
        if not trouve:
            break
        joueur = (int(trouve.group(1)), int(trouve.group(2)))
        paires = re.findall(r"\((\d+)\s*,\s*(\d+)\)", trouve.group(3))
        caisses = frozenset((int(x), int(y)) for x, y in paires)
        if len(caisses) == nb_caisses:
            dispositions.append((caisses, joueur))

    disposition_finale = (frozenset(t for c, t in affectation), None)  # position joueur non contrainte au but
    return [(probleme.etat_initial.caisses, probleme.etat_initial.joueur)] + dispositions + [disposition_finale]


def cout_vers_disposition_avec_joueur(cible, etat):
    disposition_caisses, position_joueur = cible
    cout_caisses = 0 if etat.caisses == disposition_caisses else int(_cout_affectation(etat.caisses, disposition_caisses).sum())
    if position_joueur is None:  # disposition finale : le but ne contraint pas le joueur
        return cout_caisses
    cout_joueur = abs(etat.joueur[0] - position_joueur[0]) + abs(etat.joueur[1] - position_joueur[1])
    return cout_caisses + cout_joueur
