import re

from Algorithmes.Points_d_insertion_LLM.client_llm import demander_a_claude


def generer_waypoints_llm(probleme, demander=demander_a_claude):
    # une cible = un plateau COMPLET (pas juste une tuile) -- le LLM propose
    # 2-3 dispositions intermediaires plausibles entre le depart et le but,
    # comme pour Pathfinding. Contrairement a Sokoban, n'importe quelle
    # permutation des chiffres 1..n*n-1 + case vide est un etat valide (pas
    # de mur a respecter), donc pas de risque d'etat invalide type "case
    # occupee deux fois" hors erreur de parsing.
    n = probleme.n
    lignes = [probleme.etat_initial[i * n:(i + 1) * n] for i in range(n)]
    grille_depart = "\n".join(" ".join(("_" if v == 0 else str(v)) for v in ligne) for ligne in lignes)
    lignes_but = [probleme.but[i * n:(i + 1) * n] for i in range(n)]
    grille_but = "\n".join(" ".join(("_" if v == 0 else str(v)) for v in ligne) for ligne in lignes_but)

    prompt = (
        f"Taquin {n}x{n} ('_' = case vide).\n"
        "Plateau de départ :\n" + grille_depart + "\n\n"
        "Plateau but :\n" + grille_but + "\n\n"
        "Contexte : ces dispositions intermédiaires vont guider une "
        "recherche A* -- de bonnes dispositions réduisent fortement le "
        "nombre d'états explorés, de mauvaises peuvent la ralentir. Prends "
        "tout le temps de réflexion nécessaire.\n\n"
        "En partant du plateau de départ et en allant vers le plateau but, "
        "donne 2 ou 3 dispositions COMPLÈTES intermédiaires plausibles du "
        f"plateau (chaque chiffre de 1 à {n * n - 1} et la case vide, "
        "chacun une seule fois). Termine par exactement une ligne par "
        "disposition, au format 'DISPOSITION i: v1 v2 v3 ...' (les "
        f"{n * n} valeurs lues ligne par ligne, 0 pour la case vide)."
    )
    texte = demander(prompt, max_tokens=3000)

    valeurs_attendues = set(range(n * n))
    dispositions = []
    for i in range(1, 10):  # large marge, on s'arrete des qu'on ne trouve plus de DISPOSITION i
        trouve = re.search(rf"DISPOSITION\s*{i}\s*:\s*(.+)", texte)
        if not trouve:
            break
        nombres = [int(x) for x in re.findall(r"\d+", trouve.group(1))][:n * n]
        if len(nombres) == n * n and set(nombres) == valeurs_attendues:  # doit etre une vraie permutation
            dispositions.append(tuple(nombres))

    # le plateau but n'est jamais invente par le LLM -- toujours garanti valide, comme pour Pathfinding
    return [probleme.etat_initial] + dispositions + [probleme.but]


def cout_vers_cible(etat_cible, etat):
    # generalisation de l'heuristique classique : distance de Manhattan
    # sommee sur toutes les tuiles, entre DEUX etats quelconques (pas
    # forcement l'etat but fixe) -- 0 ssi les deux plateaux sont identiques
    n = int(len(etat) ** 0.5)
    position_dans_cible = {valeur: indice for indice, valeur in enumerate(etat_cible)}
    total = 0
    for indice, valeur in enumerate(etat):
        if valeur == 0:
            continue
        indice_cible = position_dans_cible[valeur]
        l1, c1 = divmod(indice, n)
        l2, c2 = divmod(indice_cible, n)
        total += abs(l1 - l2) + abs(c1 - c2)
    return total
