import matplotlib.patches as patches
import matplotlib.pyplot as plt


def dessiner_recherche_de_chemin(probleme, chemin, visites, chemin_fichier=None, ax=None):
    # ax=None (cas normal) : on crée notre propre figure et on l'enregistre.
    # ax fourni (cas d'un montage avec plusieurs cartes côte à côte) : on
    # dessine juste dessus, sans créer ni enregistrer de figure ici -- c'est
    # l'appelant qui s'en charge.
    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(probleme.largeur, probleme.hauteur))

    visites = visites or set()  # au cas où on ne veut pas les afficher

    # une case par cellule de la grille : noire si mur, grise si visitée par
    # la recherche (mais pas sur le chemin final), blanche sinon
    for x in range(probleme.largeur):
        for y in range(probleme.hauteur):
            if (x, y) in probleme.obstacles:
                couleur = "black"
            elif (x, y) in visites:
                couleur = "lightgray"
            else:
                couleur = "white"
            ax.add_patch(patches.Rectangle((x, y), 1, 1, facecolor=couleur, edgecolor="gray"))

    # départ en bleu, but en vert (par-dessus la case, même si ce n'est pas un mur)
    ax.add_patch(patches.Rectangle(probleme.etat_initial, 1, 1, facecolor="royalblue"))
    ax.add_patch(patches.Rectangle(probleme.but, 1, 1, facecolor="seagreen"))

    # chemin trouvé, tracé en rouge par-dessus, centré dans chaque case (+0.5)
    if chemin:
        xs = [x + 0.5 for x, y in chemin]
        ys = [y + 0.5 for x, y in chemin]
        ax.plot(xs, ys, color="red", linewidth=2, marker="o")

    ax.set_xlim(0, probleme.largeur)
    ax.set_ylim(0, probleme.hauteur)
    ax.set_aspect("equal")
    ax.invert_yaxis()  # y=0 en haut, comme dans nos grilles (même convention que le parsing)
    ax.set_xticks(range(probleme.largeur + 1))
    ax.set_yticks(range(probleme.hauteur + 1))
    ax.grid(True)

    if fig is not None:  # on n'enregistre que si c'est nous qui avons créé la figure
        plt.savefig(chemin_fichier, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"Image enregistrée dans {chemin_fichier}")
