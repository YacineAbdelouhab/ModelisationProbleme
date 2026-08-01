import re

from Algorithmes.Points_d_insertion_LLM.client_llm import demander_a_claude


def generer_waypoints_llm(probleme, demander=demander_a_claude):
    # décrit toute la carte (pas un seul état) et demande une séquence de
    # points de passage du départ au but -- voir Algorithme 1 du papier
    grille = []
    for y in range(probleme.hauteur):
        ligne = []
        for x in range(probleme.largeur):
            case = (x, y)
            if case == probleme.etat_initial:
                ligne.append("A")
            elif case == probleme.but:
                ligne.append("D")
            elif case in probleme.obstacles:
                ligne.append("#")
            else:
                ligne.append(".")
        grille.append("".join(ligne))

    prompt = (
        f"Grille {probleme.largeur}x{probleme.hauteur} pour un problème de "
        "recherche de chemin.\n"
        "Coordonnées (x, y) : x = colonne (0 à gauche), y = ligne (0 en "
        "haut, augmente vers le bas).\n"
        "'A' = départ, 'D' = but, '#' = mur, '.' = case libre :\n"
        + "\n".join(grille)
        + f"\n\nDépart : {probleme.etat_initial}\nBut : {probleme.but}\n\n"
        "Contexte : cette séquence de points de passage va guider une "
        "recherche A* -- un bon itinéraire réduit fortement le nombre "
        "d'états explorés, un mauvais peut la ralentir ou l'égarer. Prends "
        "tout le temps de réflexion nécessaire.\n\n"
        "Propose une séquence de 3 à 6 points de passage (waypoints) du "
        "départ au but, en évitant les murs, qui te semble un bon "
        "itinéraire global. Termine par exactement une ligne 'REPONSE: "
        "(x1,y1) (x2,y2) ...' avec le départ en premier point et le but en "
        "dernier point."
    )
    texte = demander(prompt, max_tokens=2000)

    trouve = re.search(r"REPONSE:\s*(.+)", texte)
    waypoints = [probleme.etat_initial, probleme.but]  # repli si échec de lecture
    if trouve:
        paires = re.findall(r"\((\d+)\s*,\s*(\d+)\)", trouve.group(1))
        candidats = [(int(x), int(y)) for x, y in paires]

        # contrainte du papier : départ et but doivent être dans la liste
        if candidats and candidats[0] != probleme.etat_initial:
            candidats.insert(0, probleme.etat_initial)
        if candidats and candidats[-1] != probleme.but:
            candidats.append(probleme.but)

        # contrainte du papier : aucun waypoint dans un mur
        candidats = [c for c in candidats if c not in probleme.obstacles]

        if len(candidats) >= 2:
            waypoints = candidats

    return waypoints


def cout_vers_cible(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
