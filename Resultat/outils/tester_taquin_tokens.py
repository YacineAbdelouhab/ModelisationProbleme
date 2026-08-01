import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from Algorithmes.Points_d_insertion_LLM.client_llm import demander_a_claude, demander_a_deepseek
from Jeux.Taquin.probleme_taquin import charger_depuis_fichier

probleme = charger_depuis_fichier(str(RACINE / "Jeux/Taquin/exemples/niveau2_moyen/carte1.txt"))
n = probleme.n
lignes = [probleme.etat_initial[i * n:(i + 1) * n] for i in range(n)]
grille_depart = "\n".join(" ".join(("_" if v == 0 else str(v)) for v in ligne) for ligne in lignes)
lignes_but = [probleme.but[i * n:(i + 1) * n] for i in range(n)]
grille_but = "\n".join(" ".join(("_" if v == 0 else str(v)) for v in ligne) for ligne in lignes_but)

prompt = (
    f"Taquin {n}x{n} ('_' = case vide).\n"
    "Plateau de départ :\n" + grille_depart + "\n\n"
    "Plateau but :\n" + grille_but + "\n\n"
    "Contexte : ces dispositions intermédiaires vont guider une "
    "recherche A* -- de bonnes dispositions réduisent fortement le "
    "nombre d'états explorés, de mauvaises peuvent la ralentir.\n\n"
    "En partant du plateau de départ et en allant vers le plateau but, "
    "donne 2 ou 3 dispositions COMPLÈTES intermédiaires plausibles du "
    f"plateau (chaque chiffre de 1 à {n * n - 1} et la case vide, "
    "chacun une seule fois). Termine par exactement une ligne par "
    "disposition, au format 'DISPOSITION i: v1 v2 v3 ...' (les "
    f"{n * n} valeurs lues ligne par ligne, 0 pour la case vide)."
)

for nom, fn in [("DeepSeek", demander_a_deepseek)]:
    texte = fn(prompt, max_tokens=32000)
    print(f"----- {nom} (texte brut) -----")
    print(texte[:1500])
    print("...")
    dispositions = []
    for i in range(1, 10):
        trouve = re.search(rf"DISPOSITION\s*{i}\s*:\s*(.+)", texte)
        if not trouve:
            break
        dispositions.append(trouve.group(1)[:60])
    print(f"{nom} dispositions trouvees : {dispositions}")
