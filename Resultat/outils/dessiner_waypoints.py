import matplotlib.patches as patches
import matplotlib.pyplot as plt

from Resultat.outils.dessiner_recherche_de_chemin import dessiner_recherche_de_chemin


def dessiner_waypoints_pathfinding(probleme, chemin, visites, waypoints, titre, chemin_fichier):
    # reutilise le dessin existant (murs, cases visitees en gris, chemin en
    # rouge, depart/but) et rajoute les waypoints par-dessus, en etoiles
    # jaunes -- clairement visibles sur n'importe quel fond
    fig, ax = plt.subplots(figsize=(probleme.largeur, probleme.hauteur))
    dessiner_recherche_de_chemin(probleme, chemin, visites, ax=ax)
    xs = [x + 0.5 for x, y in waypoints]
    ys = [y + 0.5 for x, y in waypoints]
    ax.plot(xs, ys, marker="*", color="gold", markersize=22, markeredgecolor="black",
            linestyle="None", zorder=5)
    ax.set_title(titre, fontsize=11)
    fig.tight_layout()
    fig.savefig(chemin_fichier, dpi=140)
    plt.close(fig)


def _dessiner_grille_taquin(etat, n, ax, titre):
    for indice, valeur in enumerate(etat):
        ligne, colonne = divmod(indice, n)
        couleur = "lightgray" if valeur == 0 else "white"
        ax.add_patch(patches.Rectangle((colonne, ligne), 1, 1, facecolor=couleur, edgecolor="black"))
        if valeur != 0:
            ax.text(colonne + 0.5, ligne + 0.5, str(valeur), ha="center", va="center", fontsize=14)
    ax.set_xlim(0, n)
    ax.set_ylim(0, n)
    ax.set_aspect("equal")
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(titre, fontsize=9)


def dessiner_dispositions_taquin(dispositions, n, chemin_fichier):
    # une disposition = un etat complet (tuple) -- un panneau par disposition,
    # cote a cote, pour voir la progression depart -> ... -> but
    fig, axes = plt.subplots(1, len(dispositions), figsize=(n * len(dispositions) * 1.1, n * 1.1))
    if len(dispositions) == 1:
        axes = [axes]
    noms = ["Départ"] + [f"Disposition {i}" for i in range(1, len(dispositions) - 1)] + ["But"]
    for ax, etat, nom in zip(axes, dispositions, noms):
        _dessiner_grille_taquin(etat, n, ax, nom)
    fig.tight_layout()
    fig.savefig(chemin_fichier, dpi=140)
    plt.close(fig)


def _dessiner_grille_sokoban(probleme, caisses, joueur, ax, titre):
    cases = probleme.murs | probleme.cibles | caisses | ({joueur} if joueur else set())
    xs = [x for x, _ in cases]
    ys = [y for _, y in cases]
    for x in range(min(xs), max(xs) + 1):
        for y in range(min(ys), max(ys) + 1):
            case = (x, y)
            sur_cible = case in probleme.cibles
            if case in probleme.murs:
                couleur = "black"
            elif joueur and case == joueur:
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
    ax.set_title(titre, fontsize=9)


def dessiner_dispositions_sokoban(probleme, dispositions, chemin_fichier):
    # dispositions : liste d'ensembles de caisses (frozenset), OU de tuples
    # (caisses, joueur) si la variante "avec joueur" est utilisee
    fig, axes = plt.subplots(1, len(dispositions), figsize=(5 * len(dispositions), 5))
    if len(dispositions) == 1:
        axes = [axes]
    noms = ["Départ"] + [f"Disposition {i}" for i in range(1, len(dispositions) - 1)] + ["Finale"]
    for ax, disposition, nom in zip(axes, dispositions, noms):
        if isinstance(disposition, tuple) and len(disposition) == 2 and not isinstance(disposition, frozenset):
            caisses, joueur = disposition
        else:
            caisses, joueur = disposition, None
        _dessiner_grille_sokoban(probleme, caisses, joueur, ax, nom)
    fig.tight_layout()
    fig.savefig(chemin_fichier, dpi=140)
    plt.close(fig)
