import matplotlib.pyplot as plt

from Algorithmes.A_etoile.a_etoile import a_etoile
from Jeux.Sokoban.probleme_sokoban import charger_depuis_fichier
from Resultat.outils.dessiner_sokoban import dessiner_sokoban

NIVEAUX = ["niveau1_facile", "niveau2_moyen", "niveau3_difficile", "niveau4_tres_difficile"]
MAX_ETATS_EXPLORES = 500_000  # garde-fou, Sokoban peut exploser vite

fig, axes = plt.subplots(1, len(NIVEAUX), figsize=(16, 5))

for colonne, niveau in enumerate(NIVEAUX):
    chemin_fichier = f"Jeux/Sokoban/exemples/microban/{niveau}.txt"
    probleme = charger_depuis_fichier(chemin_fichier)

    chemin, cout, visites = a_etoile(probleme, max_etats_explores=MAX_ETATS_EXPLORES)

    ax = axes[colonne]
    dessiner_sokoban(probleme, ax=ax)  # affiche l'état de départ (pas le déroulé du chemin)

    if chemin is not None:
        titre = f"{niveau}\ncout={cout}  visites={len(visites)}"
    else:
        titre = f"{niveau}\nPAS DE SOLUTION (budget {MAX_ETATS_EXPLORES})"
    ax.set_title(titre, fontsize=9)

    print(f"{niveau}: cout={cout} visites={len(visites)}")

CHEMIN_IMAGE = "Resultat/Sokoban/A_etoile/apercu_resolutions.png"
plt.tight_layout()
plt.savefig(CHEMIN_IMAGE, dpi=150)
plt.close(fig)
print(f"Aperçu enregistré dans {CHEMIN_IMAGE}")
