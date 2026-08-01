import matplotlib.patches as patches
import matplotlib.pyplot as plt


def dessiner_sokoban(probleme, ax=None):
    # ax=None (cas normal) : on crée notre propre figure.
    # ax fourni (cas d'un montage) : on dessine juste dessus.
    cases = probleme.murs | probleme.cibles | probleme.etat_initial.caisses | {probleme.etat_initial.joueur}
    xs = [x for x, _ in cases]
    ys = [y for _, y in cases]
    largeur = max(xs) - min(xs) + 1
    hauteur = max(ys) - min(ys) + 1

    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(largeur, hauteur))

    joueur = probleme.etat_initial.joueur
    caisses = probleme.etat_initial.caisses

    for x in range(min(xs), max(xs) + 1):
        for y in range(min(ys), max(ys) + 1):
            case = (x, y)
            sur_cible = case in probleme.cibles
            if case in probleme.murs:
                couleur = "black"
            elif case == joueur:
                couleur = "royalblue"
            elif case in caisses:
                couleur = "seagreen" if sur_cible else "peru"
            elif sur_cible:
                couleur = "lightyellow"
            else:
                couleur = "white"
            ax.add_patch(patches.Rectangle((x, y), 1, 1, facecolor=couleur, edgecolor="gray"))

    ax.set_xlim(min(xs), max(xs) + 1)
    ax.set_ylim(min(ys), max(ys) + 1)
    ax.set_aspect("equal")
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.set_yticks([])

    return fig, ax
