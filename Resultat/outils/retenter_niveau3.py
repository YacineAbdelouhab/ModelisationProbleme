import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from Algorithmes.Points_d_insertion_LLM.client_llm import demander_a_claude, demander_a_deepseek
from Jeux.Recherche_de_chemin.probleme_recherche_de_chemin import charger_depuis_fichier

probleme = charger_depuis_fichier(str(RACINE / "Jeux/Recherche_de_chemin/exemples/niveau3_difficile/carte1.txt"))

grille = []
for y in range(probleme.hauteur):
    ligne = []
    for x in range(probleme.largeur):
        case = (x, y)
        if case == probleme.etat_initial:
            ligne.append("A")
        elif case == probleme.but:
            ligne.append("D")
        elif case in probleme.obstacles:
            ligne.append("#")
        else:
            ligne.append(".")
    grille.append("".join(ligne))

prompt = (
    f"Grille {probleme.largeur}x{probleme.hauteur} pour un problème de recherche de chemin.\n"
    "Coordonnées (x, y) : x = colonne (0 à gauche), y = ligne (0 en haut, augmente vers le bas).\n"
    "'A' = départ, 'D' = but, '#' = mur, '.' = case libre :\n"
    + "\n".join(grille)
    + f"\n\nDépart : {probleme.etat_initial}\nBut : {probleme.but}\n\n"
    "Choisis 2 points de passage INTERMÉDIAIRES quelconques, sur des cases "
    "libres, même si tu penses qu'ils ne sont pas nécessaires ou pas "
    "optimaux. Ce n'est pas grave si le choix est arbitraire, le but est "
    "juste d'illustrer un trajet en plusieurs étapes. Une réponse avec "
    "seulement le départ et le but n'est pas une réponse valide. Termine "
    "par exactement une ligne 'REPONSE: (x1,y1) (x2,y2) (x3,y3) (x4,y4)' "
    "avec le départ en premier point, le but en dernier point, et "
    "exactement 2 points intermédiaires entre les deux."
)

for nom, fn in [("Claude", demander_a_claude), ("DeepSeek", demander_a_deepseek)]:
    for essai in range(2):
        texte = fn(prompt, max_tokens=1500)
        trouve = re.search(r"REPONSE:\s*(.+)", texte)
        pts = re.findall(r"\((\d+)\s*,\s*(\d+)\)", trouve.group(1)) if trouve else []
        print(nom, essai + 1, pts)
