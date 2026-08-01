import matplotlib.pyplot as plt

from Algorithmes.A_etoile.a_etoile import a_etoile
from Jeux.Recherche_de_chemin.probleme_recherche_de_chemin import charger_depuis_fichier
from Resultat.outils.dessiner_recherche_de_chemin import dessiner_recherche_de_chemin

NIVEAUX = ["niveau1_facile", "niveau2_moyen", "niveau3_difficile", "niveau4_labyrinthe_ouvert"]
NUMEROS = [1, 2, 3]

fig, axes = plt.subplots(len(NIVEAUX), len(NUMEROS), figsize=(15, 20))

for ligne, niveau in enumerate(NIVEAUX):
    for colonne, numero in enumerate(NUMEROS):
        chemin_fichier = f"Jeux/Recherche_de_chemin/exemples/{niveau}/carte{numero}.txt"
        probleme = charger_depuis_fichier(chemin_fichier)

        chemin, cout, visites = a_etoile(probleme)

        ax = axes[ligne][colonne]
        dessiner_recherche_de_chemin(probleme, chemin, visites, ax=ax)

        if chemin is not None:
            titre = f"{niveau} - carte{numero}\ncout={cout}  visites={len(visites)}"
        else:
            titre = f"{niveau} - carte{numero}\nPAS DE SOLUTION"
        ax.set_title(titre, fontsize=9)

        print(f"{niveau}/carte{numero}: cout={cout} visites={len(visites)}")

CHEMIN_IMAGE = "Resultat/Recherche_de_chemin/A_etoile/apercu_resolutions.png"
plt.tight_layout()
plt.savefig(CHEMIN_IMAGE, dpi=150)
plt.close(fig)
print(f"Aperçu enregistré dans {CHEMIN_IMAGE}")
