import matplotlib.pyplot as plt

from Jeux.Taquin.probleme_taquin import charger_depuis_fichier
from Resultat.outils.dessiner_taquin import dessiner_taquin

NIVEAUX = ["niveau1_facile", "niveau2_moyen", "niveau3_difficile", "niveau4_tres_difficile"]
NUMEROS = [1, 2, 3]

fig, axes = plt.subplots(len(NIVEAUX), len(NUMEROS), figsize=(9, 12))

for ligne, niveau in enumerate(NIVEAUX):
    for colonne, numero in enumerate(NUMEROS):
        chemin_fichier = f"Jeux/Taquin/exemples/{niveau}/carte{numero}.txt"
        probleme = charger_depuis_fichier(chemin_fichier)
        ax = axes[ligne][colonne]
        dessiner_taquin(probleme, ax=ax)
        ax.set_title(f"{niveau} - carte{numero}", fontsize=9)

CHEMIN_IMAGE = "Resultat/Taquin/A_etoile/apercu_cartes.png"
plt.tight_layout()
plt.savefig(CHEMIN_IMAGE, dpi=150)
plt.close(fig)
print(f"Aperçu enregistré dans {CHEMIN_IMAGE}")
