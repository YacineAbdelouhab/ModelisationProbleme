def decrire_etat(probleme, etat):
    n = probleme.n
    lignes = [etat[i * n:(i + 1) * n] for i in range(n)]
    grille = "\n".join(" ".join(("_" if v == 0 else str(v)) for v in ligne) for ligne in lignes)

    return (
        f"Taquin {n}x{n} ('_' = case vide). But à atteindre : les nombres "
        f"1 à {n * n - 1} dans l'ordre, ligne par ligne, case vide en "
        "dernier.\n"
        "Un coup fait glisser une pièce voisine de la case vide à sa place.\n"
        "Plateau actuel :\n" + grille + "\n"
    )
