from dataclasses import dataclass

import numpy as np
from scipy.optimize import linear_sum_assignment

from Algorithmes.A_etoile.probleme import Probleme


@dataclass(frozen=True)
class EtatSokoban:
    # frozen=True : un état ne change jamais après sa création (on en crée
    # un nouveau à chaque coup) -- nécessaire pour qu'il soit utilisable
    # comme clé de dictionnaire / élément de set, comme les autres jeux.
    joueur: tuple  # (x, y)
    caisses: frozenset  # ensemble de (x, y)


class ProblemeSokoban(Probleme):
    """Sokoban. Le joueur pousse des caisses (une seule à la fois, jamais
    tirées) sur des cibles. 4 déplacements possibles, chaque coup coûte 1
    que le joueur pousse une caisse ou se déplace simplement.
    """

    def __init__(self, murs, cibles, joueur, caisses):
        self.murs = murs  # ensemble de (x, y), cases infranchissables
        self.cibles = cibles  # ensemble de (x, y), là où les caisses doivent finir
        self.etat_initial = EtatSokoban(joueur, caisses)
        # cases hors cible où une caisse reste bloquée à jamais (coins, et
        # couloirs entiers bordés d'un mur sans aucune cible dedans)
        self._coins_mortels = _calculer_coins_mortels(murs, cibles) | _calculer_couloirs_morts(murs, cibles)

    def est_but(self, etat):  # etat : EtatSokoban -> renvoie un booléen
        return etat.caisses == self.cibles

    def voisins(self, etat):  # etat : EtatSokoban -> renvoie une liste de (action, etat_suivant, cout)
        deplacements = [(0, -1, "haut"), (0, 1, "bas"), (-1, 0, "gauche"), (1, 0, "droite")]
        px, py = etat.joueur

        resultat = []
        for dx, dy, action in deplacements:
            nx, ny = px + dx, py + dy
            if (nx, ny) in self.murs:
                continue  # mur devant le joueur, coup impossible

            if (nx, ny) in etat.caisses:
                # il y a une caisse devant le joueur : il faut la pousser
                bx, by = nx + dx, ny + dy
                if (bx, by) in self.murs or (bx, by) in etat.caisses:
                    continue  # rien derrière la caisse, poussée impossible
                if (bx, by) in self._coins_mortels:
                    continue  # la caisse serait bloquée à jamais dans un coin -- coup inutile, jamais gagnant
                nouvelles_caisses = (etat.caisses - {(nx, ny)}) | {(bx, by)}
                resultat.append((action, EtatSokoban((nx, ny), frozenset(nouvelles_caisses)), 1))
            else:
                # case libre : simple déplacement, les caisses ne bougent pas
                resultat.append((action, EtatSokoban((nx, ny), etat.caisses), 1))
        return resultat

    def heuristique(self, etat):  # etat : EtatSokoban -> renvoie un int
        # affectation optimale caisses -> cibles (algorithme hongrois, vu en
        # cours), somme des distances de Manhattan. Admissible car c'est un
        # relâchement du vrai problème (ignore les murs et le fait qu'on ne
        # pousse qu'une caisse à la fois).
        caisses = list(etat.caisses)
        cibles = list(self.cibles)
        if not caisses:
            return 0
        couts = np.array(
            [[abs(cx - tx) + abs(cy - ty) for (tx, ty) in cibles] for (cx, cy) in caisses]
        )
        lignes, colonnes = linear_sum_assignment(couts)
        return int(couts[lignes, colonnes].sum())

    def est_impossible(self, etat):  # etat : EtatSokoban -> renvoie un booléen
        # une seule caisse dans un coin/couloir mort suffit à condamner la
        # partie entière -- déjà utilisé pour filtrer voisins() au moment de
        # la poussée (ligne ~50), exposé ici comme règle certaine réutilisable
        return any(caisse in self._coins_mortels for caisse in etat.caisses)


def charger_depuis_fichier(chemin_fichier):  # str, chemin vers un .txt -> ProblemeSokoban
    # format XSB standard : '#'=mur, '@'=joueur, '+'=joueur sur cible,
    # '$'=caisse, '*'=caisse sur cible, '.'=cible vide, tout le reste=sol
    murs, cibles, caisses = set(), set(), set()
    joueur = None

    with open(chemin_fichier, encoding="utf-8") as fichier:
        for y, ligne in enumerate(fichier):
            ligne = ligne.rstrip("\n")
            for x, caractere in enumerate(ligne):
                if caractere == "#":
                    murs.add((x, y))
                elif caractere == "@":
                    joueur = (x, y)
                elif caractere == "+":
                    joueur = (x, y)
                    cibles.add((x, y))
                elif caractere == "$":
                    caisses.add((x, y))
                elif caractere == "*":
                    caisses.add((x, y))
                    cibles.add((x, y))
                elif caractere == ".":
                    cibles.add((x, y))

    return ProblemeSokoban(frozenset(murs), frozenset(cibles), joueur, frozenset(caisses))


def _calculer_coins_mortels(murs, cibles):  # frozenset, frozenset -> frozenset de (x, y)
    # une caisse poussée dans un coin (mur perpendiculaire des deux côtés)
    # et qui n'est pas sur une cible ne peut plus jamais être repoussée --
    # aucun coup ne peut plus la faire bouger, donc la partie est perdue.
    # On repère ces cases une fois pour toutes, pour ne plus jamais y
    # pousser de caisse (vu en cours : "détection d'interblocage").
    if not murs:
        return frozenset()
    xs = [x for x, _ in murs]
    ys = [y for _, y in murs]

    coins = set()
    for x in range(min(xs), max(xs) + 1):
        for y in range(min(ys), max(ys) + 1):
            if (x, y) in murs or (x, y) in cibles:
                continue
            mur_horizontal = (x - 1, y) in murs or (x + 1, y) in murs
            mur_vertical = (x, y - 1) in murs or (x, y + 1) in murs
            if mur_horizontal and mur_vertical:
                coins.add((x, y))
    return frozenset(coins)


def _calculer_couloirs_morts(murs, cibles):  # frozenset, frozenset -> frozenset de (x, y)
    # généralise le coin mort : un couloir entier bordé d'un même côté par
    # un mur (la caisse n'y glisse donc plus que dans un sens) et qui ne
    # contient aucune cible -- une caisse poussée n'importe où dans ce
    # couloir y reste bloquée à jamais. Un coin est le cas particulier d'un
    # couloir de longueur 1.
    #
    # Point important : on ne marque mort que si le couloir est bordé par
    # de VRAIS murs des deux côtés (pas juste "le mur guide s'arrête" --
    # à cet endroit la caisse pourrait justement s'échapper par là, donc ce
    # ne serait pas sûr de la marquer morte).
    if not murs:
        return frozenset()
    xs = [x for x, _ in murs]
    ys = [y for _, y in murs]
    mortes = set()

    def balayer(cases_de_la_ligne, guide):
        # cases_de_la_ligne : positions dans l'ordre le long de la ligne/colonne
        # guide(case) -> booléen : le mur qui empêche de s'échapper perpendiculairement
        segment = []
        borde_par_un_mur = False  # le segment courant a-t-il commencé juste après un vrai mur ?
        for case in cases_de_la_ligne:
            if case in murs:
                if borde_par_un_mur and segment and not any(c in cibles for c in segment):
                    mortes.update(segment)
                segment = []
                borde_par_un_mur = True  # le prochain segment, s'il y en a un, commence bordé
            elif not guide(case):
                # le mur guide s'arrête ici : la caisse pourrait s'échapper,
                # ce segment n'est pas sûr, on l'abandonne sans le marquer
                segment = []
                borde_par_un_mur = False
            else:
                segment.append(case)
        # fin de ligne sans mur de fermeture : pas de bordure garantie, on n'y touche pas

    for y in range(min(ys), max(ys) + 1):
        ligne = [(x, y) for x in range(min(xs), max(xs) + 1)]
        balayer(ligne, lambda case: (case[0], case[1] - 1) in murs)  # guidée par le mur au-dessus
        balayer(ligne, lambda case: (case[0], case[1] + 1) in murs)  # guidée par le mur en-dessous

    for x in range(min(xs), max(xs) + 1):
        colonne = [(x, y) for y in range(min(ys), max(ys) + 1)]
        balayer(colonne, lambda case: (case[0] - 1, case[1]) in murs)  # guidée par le mur à gauche
        balayer(colonne, lambda case: (case[0] + 1, case[1]) in murs)  # guidée par le mur à droite

    return frozenset(mortes)
