from Algorithmes.A_etoile.probleme import Probleme


class ProblemeRechercheDeChemin(Probleme):
    """Plus court chemin dans une grille avec obstacles.

    Un état est une case (x, y). 4 déplacements possibles (haut/bas/
    gauche/droite), chaque coup coûte 1.
    """

    def __init__(self, largeur, hauteur, obstacles, depart, but):
        self.largeur = largeur  # int, nombre de colonnes
        self.hauteur = hauteur  # int, nombre de lignes
        self.obstacles = obstacles  # ensemble de tuples (x, y), cases infranchissables
        self.etat_initial = depart  # tuple (x, y)
        self.but = but  # tuple (x, y)

    def est_but(self, etat):  # etat : tuple (x, y) -> renvoie un booléen
        return etat == self.but

    def voisins(self, etat):  # etat : tuple (x, y) -> renvoie une liste de (action: str, etat_suivant: tuple, cout: int)
        x, y = etat
        deplacements = [(-1, 0, "gauche"), (1, 0, "droite"), (0, -1, "haut"), (0, 1, "bas")]

        resultat = []
        for dx, dy, action in deplacements:
            nx, ny = x + dx, y + dy
            dans_la_grille = 0 <= nx < self.largeur and 0 <= ny < self.hauteur
            if dans_la_grille and (nx, ny) not in self.obstacles:
                resultat.append((action, (nx, ny), 1))
        return resultat

    def heuristique(self, etat):  # etat : tuple (x, y) -> renvoie un int
        # distance de Manhattan : nombre de coups si on ignorait les
        # obstacles. Admissible car ça ne peut jamais surestimer le vrai coût
        # (avec des obstacles, le vrai chemin ne peut être que plus long).
        x, y = etat
        bx, by = self.but
        return abs(x - bx) + abs(y - by)


def charger_depuis_fichier(chemin_fichier):  # str, chemin vers un .txt -> ProblemeRechercheDeChemin
    """Lit une carte texte (A=départ, D=but, #=mur, tout le reste=case libre)
    et construit le problème correspondant."""
    with open(chemin_fichier, encoding="utf-8") as fichier:
        lignes = [ligne.rstrip("\n") for ligne in fichier if ligne.strip("\n") != ""]

    hauteur = len(lignes)
    largeur = max(len(ligne) for ligne in lignes)

    obstacles = set()
    depart = None
    but = None
    for y, ligne in enumerate(lignes):
        for x, caractere in enumerate(ligne):
            if caractere == "#":
                obstacles.add((x, y))
            elif caractere == "A":
                depart = (x, y)
            elif caractere == "D":
                but = (x, y)

    return ProblemeRechercheDeChemin(largeur, hauteur, obstacles, depart, but)
