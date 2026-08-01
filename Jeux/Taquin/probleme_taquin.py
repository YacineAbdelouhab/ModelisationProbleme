import random

from Algorithmes.A_etoile.probleme import Probleme


class ProblemeTaquin(Probleme):
    """Taquin (n x n). Un état est un tuple plat de n*n entiers, lu ligne
    par ligne, 0 = case vide. 4 déplacements possibles (la case vide
    échange sa place avec un voisin), chaque coup coûte 1.
    """

    def __init__(self, n, etat_initial):
        self.n = n  # int, taille du taquin (3 pour 3x3, 4 pour 4x4)
        self.etat_initial = etat_initial  # tuple plat de n*n entiers
        self.but = etat_but(n)  # tuple plat, la position résolue
        self._position_but = {valeur: indice for indice, valeur in enumerate(self.but)}  # valeur -> indice dans self.but

    def est_but(self, etat):  # etat : tuple -> renvoie un booléen
        return etat == self.but

    def voisins(self, etat):  # etat : tuple -> renvoie une liste de (action: str, etat_suivant: tuple, cout: int)
        n = self.n
        indice_case_vide = etat.index(0)
        ligne, colonne = divmod(indice_case_vide, n)

        deplacements = [(-1, 0, "haut"), (1, 0, "bas"), (0, -1, "gauche"), (0, 1, "droite")]
        resultat = []
        for dl, dc, action in deplacements:
            nouvelle_ligne, nouvelle_colonne = ligne + dl, colonne + dc
            dans_la_grille = 0 <= nouvelle_ligne < n and 0 <= nouvelle_colonne < n
            if dans_la_grille:
                indice_voisin = nouvelle_ligne * n + nouvelle_colonne
                nouvel_etat = list(etat)
                nouvel_etat[indice_case_vide], nouvel_etat[indice_voisin] = (
                    nouvel_etat[indice_voisin],
                    nouvel_etat[indice_case_vide],
                )
                resultat.append((action, tuple(nouvel_etat), 1))
        return resultat

    def heuristique(self, etat):  # etat : tuple -> renvoie un int
        # distance de Manhattan sommée sur toutes les pièces (sauf la case
        # vide) : pour chaque pièce, distance entre sa position actuelle et
        # sa position dans l'état but. Admissible : chaque coup ne peut
        # rapprocher qu'une seule pièce d'une seule case de son but.
        n = self.n
        total = 0
        for indice, valeur in enumerate(etat):
            if valeur == 0:
                continue
            indice_but = self._position_but[valeur]
            l1, c1 = divmod(indice, n)
            l2, c2 = divmod(indice_but, n)
            total += abs(l1 - l2) + abs(c1 - c2)
        return total


def etat_but(n):  # int -> tuple, l'état résolu : 1, 2, 3, ..., n*n-1, puis 0
    return tuple(range(1, n * n)) + (0,)


def est_resoluble(etat, n):  # etat : tuple, n : int -> renvoie un booléen
    # test d'insolubilité classique par comptage d'inversions (vu en
    # cours) : un taquin n'est résoluble que si sa permutation a la bonne
    # parité, sinon aucune suite de coups ne peut atteindre le but.
    pieces = [valeur for valeur in etat if valeur != 0]
    inversions = sum(
        1 for i in range(len(pieces)) for j in range(i + 1, len(pieces)) if pieces[i] > pieces[j]
    )
    if n % 2 == 1:  # grille de taille impaire (3x3, 5x5...)
        return inversions % 2 == 0
    # grille de taille paire (4x4...) : il faut aussi regarder la ligne de la case vide
    ligne_case_vide_depuis_le_bas = n - etat.index(0) // n
    if ligne_case_vide_depuis_le_bas % 2 == 0:
        return inversions % 2 == 1
    return inversions % 2 == 0


def generer_instance_aleatoire(n, nombre_melanges, graine=None):  # -> tuple (un état)
    # mélange depuis l'état but en appliquant des coups légaux au hasard :
    # garantit un état résoluble par construction, pas besoin de vérifier
    # avec est_resoluble après.
    rng = random.Random(graine)
    etat = etat_but(n)
    probleme = ProblemeTaquin(n, etat)
    for _ in range(nombre_melanges):
        voisins = probleme.voisins(etat)
        _, etat, _ = voisins[rng.randrange(len(voisins))]
    return etat


def charger_depuis_fichier(chemin_fichier):  # str, chemin vers un .txt -> ProblemeTaquin
    # lit une grille texte (nombres séparés par des espaces, 0 = case vide)
    with open(chemin_fichier, encoding="utf-8") as fichier:
        lignes = [ligne.split() for ligne in fichier if ligne.strip() != ""]

    n = len(lignes)
    etat = tuple(int(valeur) for ligne in lignes for valeur in ligne)
    return ProblemeTaquin(n, etat)


def sauvegarder_dans_fichier(etat, n, chemin_fichier):  # tuple, int, str -> rien, écrit le fichier
    lignes = [" ".join(str(etat[l * n + c]) for c in range(n)) for l in range(n)]
    with open(chemin_fichier, "w", encoding="utf-8") as fichier:
        fichier.write("\n".join(lignes) + "\n")
