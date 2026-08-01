def decrire_etat(probleme, etat):
    cases = probleme.murs | probleme.cibles | etat.caisses | {etat.joueur}
    xs = [x for x, _ in cases]
    ys = [y for _, y in cases]

    grille = []
    for y in range(min(ys), max(ys) + 1):
        ligne = []
        for x in range(min(xs), max(xs) + 1):
            case = (x, y)
            sur_cible = case in probleme.cibles
            if case in probleme.murs:
                ligne.append("#")
            elif case == etat.joueur:
                ligne.append("+" if sur_cible else "@")
            elif case in etat.caisses:
                ligne.append("*" if sur_cible else "$")
            elif sur_cible:
                ligne.append(".")
            else:
                ligne.append(" ")
        grille.append("".join(ligne))

    return (
        "Sokoban. Le joueur pousse des caisses (une seule à la fois, jamais "
        "tirée) sur des cibles.\n"
        "Coordonnées (x, y) : x = colonne (augmente vers la droite), "
        "y = ligne (0 en haut, augmente vers le bas).\n"
        "'#' = mur, '@' = joueur, '+' = joueur sur cible, '$' = caisse, "
        "'*' = caisse sur cible, '.' = cible vide :\n"
        + "\n".join(grille)
        + f"\n\nJoueur : {etat.joueur}\nCaisses : {sorted(etat.caisses)}\nCibles : {sorted(probleme.cibles)}\n"
    )


def decrire_etat_minimal(probleme, etat):
    # variante A/B : juste la grille et les regles, sans repeter les
    # coordonnees en toutes lettres apres -- pour tester si les listes
    # explicites de decrire_etat() aident vraiment ou ne sont que du bruit
    cases = probleme.murs | probleme.cibles | etat.caisses | {etat.joueur}
    xs = [x for x, _ in cases]
    ys = [y for _, y in cases]

    grille = []
    for y in range(min(ys), max(ys) + 1):
        ligne = []
        for x in range(min(xs), max(xs) + 1):
            case = (x, y)
            sur_cible = case in probleme.cibles
            if case in probleme.murs:
                ligne.append("#")
            elif case == etat.joueur:
                ligne.append("+" if sur_cible else "@")
            elif case in etat.caisses:
                ligne.append("*" if sur_cible else "$")
            elif sur_cible:
                ligne.append(".")
            else:
                ligne.append(" ")
        grille.append("".join(ligne))

    return (
        "Sokoban. Le joueur pousse des caisses (une seule à la fois, jamais "
        "tirée) sur des cibles.\n"
        "'#' = mur, '@' = joueur, '+' = joueur sur cible, '$' = caisse, "
        "'*' = caisse sur cible, '.' = cible vide :\n"
        + "\n".join(grille)
    )


def decrire_etat_tableau(probleme, etat):
    # variante A/B : la grille en liste de listes façon tableau Python
    # (une ligne = une sous-liste), au lieu du dessin ASCII -- teste si un
    # format plus "indexé" aide le LLM a mieux raisonner sur les
    # coordonnees (x, y) qu'on attend en sortie
    cases = probleme.murs | probleme.cibles | etat.caisses | {etat.joueur}
    xs = [x for x, _ in cases]
    ys = [y for _, y in cases]

    tableau = []
    for y in range(min(ys), max(ys) + 1):
        ligne = []
        for x in range(min(xs), max(xs) + 1):
            case = (x, y)
            sur_cible = case in probleme.cibles
            if case in probleme.murs:
                ligne.append("#")
            elif case == etat.joueur:
                ligne.append("+" if sur_cible else "@")
            elif case in etat.caisses:
                ligne.append("*" if sur_cible else "$")
            elif sur_cible:
                ligne.append(".")
            else:
                ligne.append(" ")
        tableau.append(ligne)

    return (
        "Sokoban. Le joueur pousse des caisses (une seule à la fois, jamais "
        "tirée) sur des cibles.\n"
        "'#' = mur, '@' = joueur, '+' = joueur sur cible, '$' = caisse, "
        "'*' = caisse sur cible, '.' = cible vide :\n"
        "Grille sous forme de tableau (liste de lignes, chaque ligne une "
        "liste de cases) : tableau[y][x], avec x = colonne (augmente vers "
        "la droite), y = ligne (0 en haut, augmente vers le bas) :\n"
        + repr(tableau)
        + f"\n\nJoueur : {etat.joueur}\nCaisses : {sorted(etat.caisses)}\nCibles : {sorted(probleme.cibles)}\n"
    )
