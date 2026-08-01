def decrire_etat(probleme, etat):
    grille = []
    for y in range(probleme.hauteur):
        ligne = []
        for x in range(probleme.largeur):
            case = (x, y)
            if case == etat:
                ligne.append("@")
            elif case == probleme.but:
                ligne.append("D")
            elif case in probleme.obstacles:
                ligne.append("#")
            else:
                ligne.append(".")
        grille.append("".join(ligne))

    return (
        f"Recherche de chemin sur une grille {probleme.largeur}x{probleme.hauteur}.\n"
        "Coordonnées (x, y) : x = colonne (0 à gauche, augmente vers la droite), "
        "y = ligne (0 en haut, augmente vers le bas).\n"
        "'@' = case actuelle, 'D' = but, '#' = mur, '.' = case libre :\n"
        + "\n".join(grille)
        + f"\n\nCase actuelle : {etat}\nBut : {probleme.but}\n"
    )
