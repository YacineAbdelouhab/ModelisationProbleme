import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from Algorithmes.Points_d_insertion_LLM.client_llm import demander_a_claude, demander_a_deepseek
from Algorithmes.LLM_A_etoile_papier.llm_a_etoile_papier import llm_a_etoile_papier
from Jeux.Recherche_de_chemin.probleme_recherche_de_chemin import charger_depuis_fichier
from Jeux.Recherche_de_chemin.waypoints_llm_a_etoile import cout_vers_cible
from Resultat.outils.generer_figures_pathfinding_etoile import generer_waypoints_avec_intermediaires

probleme = charger_depuis_fichier(
    str(RACINE / "Jeux/Recherche_de_chemin/exemples/niveau3_difficile/carte1.txt")
)

for nom, fn in [("Claude", demander_a_claude), ("DeepSeek", demander_a_deepseek)]:
    waypoints = generer_waypoints_avec_intermediaires(probleme, demander=fn, max_essais=3)
    chemin, cout, fermes = llm_a_etoile_papier(probleme, lambda p: waypoints, cout_vers_cible)
    print(f"{nom} : waypoints={waypoints} cout={cout} visites={len(fermes)}")
