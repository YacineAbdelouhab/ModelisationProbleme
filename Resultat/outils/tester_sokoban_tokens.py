import re
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from Algorithmes.Points_d_insertion_LLM.client_llm import demander_a_claude, demander_a_deepseek
from Jeux.Sokoban.decrire_pour_llm import decrire_etat
from Jeux.Sokoban.probleme_sokoban import charger_depuis_fichier

probleme = charger_depuis_fichier(str(RACINE / "Jeux/Sokoban/exemples/microban/niveau2_moyen.txt"))
caisses_depart = list(probleme.etat_initial.caisses)
cibles = list(probleme.cibles)
couts = np.array([[abs(cx - tx) + abs(cy - ty) for (tx, ty) in cibles] for (cx, cy) in caisses_depart])
lignes, colonnes = linear_sum_assignment(couts)
affectation = [(caisses_depart[i], cibles[j]) for i, j in zip(lignes, colonnes)]

prompt = (
    "Voici une carte de Sokoban et l'affectation caisse -> cible la "
    "plus courte au total (calculée sans tenir compte de l'ordre) :\n"
    + "\n".join(f"Caisse en {c} -> cible en {t}" for c, t in affectation)
    + "\n\n" + decrire_etat(probleme, probleme.etat_initial)
    + "\n\nContexte : ces dispositions vont guider une recherche A* -- "
    "de bonnes dispositions intermédiaires réduisent fortement le "
    "nombre d'états explorés, de mauvaises peuvent bloquer des caisses "
    "ou ralentir la recherche.\n\n"
    "En partant de la disposition actuelle des caisses et en allant "
    "vers la disposition finale (chaque caisse sur sa cible assignée), "
    "donne 2 ou 3 dispositions INTERMÉDIAIRES plausibles (uniquement "
    "les positions des caisses, pas le joueur). Termine par exactement "
    "une ligne par disposition, au format 'DISPOSITION i: (x,y) (x,y) "
    "...'"
)

for nom, fn, tokens in [("DeepSeek", demander_a_deepseek, 48000)]:
    texte = fn(prompt, max_tokens=tokens)
    print(f"----- {nom} ({tokens} tokens) -----")
    print(texte[:1200])
    print("...")
    dispositions = []
    for i in range(1, 10):
        trouve = re.search(rf"DISPOSITION\s*{i}\s*:\s*(.+)", texte)
        if not trouve:
            break
        dispositions.append(trouve.group(1)[:60])
    print(f"{nom} dispositions trouvees : {dispositions}")
