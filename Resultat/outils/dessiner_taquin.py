import matplotlib.patches as patches
import matplotlib.pyplot as plt


def dessiner_taquin(probleme, ax=None):
    # ax=None (cas normal) : on crée notre propre figure et on l'affiche/enregistre.
    # ax fourni (cas d'un montage) : on dessine juste dessus.
    n = probleme.n
    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(n, n))

    etat = probleme.etat_initial
    for indice, valeur in enumerate(etat):
        ligne, colonne = divmod(indice, n)
        couleur = "lightgray" if valeur == 0 else "white"
        ax.add_patch(patches.Rectangle((colonne, ligne), 1, 1, facecolor=couleur, edgecolor="black"))
        if valeur != 0:
            ax.text(colonne + 0.5, ligne + 0.5, str(valeur), ha="center", va="center", fontsize=16)

    ax.set_xlim(0, n)
    ax.set_ylim(0, n)
    ax.set_aspect("equal")
    ax.invert_yaxis()  # ligne 0 en haut, comme la grille
    ax.set_xticks([])
    ax.set_yticks([])

    return fig, ax
