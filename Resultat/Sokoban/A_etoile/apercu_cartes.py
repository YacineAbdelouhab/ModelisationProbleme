import matplotlib.pyplot as plt

from Jeux.Sokoban.probleme_sokoban import charger_depuis_fichier
from Resultat.outils.dessiner_sokoban import dessiner_sokoban

NIVEAUX = ["niveau1_facile", "niveau2_moyen", "niveau3_difficile", "niveau4_tres_difficile"]

fig, axes = plt.subplots(1, len(NIVEAUX), figsize=(16, 5))

for colonne, niveau in enumerate(NIVEAUX):
    chemin_fichier = f"Jeux/Sokoban/exemples/microban/{niveau}.txt"
    probleme = charger_depuis_fichier(chemin_fichier)
    ax = axes[colonne]
    dessiner_sokoban(probleme, ax=ax)
    ax.set_title(niveau, fontsize=9)

CHEMIN_IMAGE = "Resultat/Sokoban/A_etoile/apercu_cartes.png"
plt.tight_layout()
plt.savefig(CHEMIN_IMAGE, dpi=150)
plt.close(fig)
print(f"Aperçu enregistré dans {CHEMIN_IMAGE}")
