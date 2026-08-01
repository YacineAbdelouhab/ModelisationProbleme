import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from Algorithmes.A_etoile.a_etoile import a_etoile
from Algorithmes.LLM_A_etoile_papier.llm_a_etoile_papier import llm_a_etoile_papier
from Algorithmes.Points_d_insertion_LLM.client_llm import demander_a_claude, demander_a_deepseek
from Jeux.Recherche_de_chemin.probleme_recherche_de_chemin import charger_depuis_fichier
from Jeux.Recherche_de_chemin.waypoints_llm_a_etoile import cout_vers_cible
from Resultat.outils.generer_figures_pathfinding_etoile import generer_waypoints_avec_intermediaires

DOSSIER_SORTIE = RACINE / "Resultat" / "Recherche_de_chemin" / "Experimentation"

NIVEAUX = ["niveau1_facile", "niveau2_moyen", "niveau3_difficile"]
CARTES = ["carte1", "carte2", "carte3"]


def traiter(niveau, carte, fournisseur_nom, demander):
    chemin_fichier = RACINE / f"Jeux/Recherche_de_chemin/exemples/{niveau}/{carte}.txt"
    probleme = charger_depuis_fichier(str(chemin_fichier))

    chemin_base, cout_base, fermes_base = a_etoile(probleme)

    waypoints = generer_waypoints_avec_intermediaires(probleme, demander=demander, max_essais=3)
    chemin_wp, cout_wp, fermes_wp = llm_a_etoile_papier(probleme, lambda p: waypoints, cout_vers_cible)

    nb_intermediaires = max(0, len(waypoints) - 2)
    resultat = {
        "niveau": niveau, "carte": carte, "fournisseur": fournisseur_nom,
        "cout_baseline": cout_base, "visites_baseline": len(fermes_base),
        "cout_waypoints": cout_wp, "visites_waypoints": len(fermes_wp),
        "nb_intermediaires": nb_intermediaires, "waypoints": waypoints,
    }
    print(
        f"{niveau}/{carte} [{fournisseur_nom}] : baseline cout={cout_base} visites={len(fermes_base)} "
        f"| LLM-A* cout={cout_wp} visites={len(fermes_wp)} intermediaires={nb_intermediaires}"
    )
    return resultat


if __name__ == "__main__":
    resultats = []
    for niveau in NIVEAUX:
        for carte in CARTES:
            resultats.append(traiter(niveau, carte, "Claude", demander_a_claude))
            resultats.append(traiter(niveau, carte, "DeepSeek", demander_a_deepseek))
    with open(DOSSIER_SORTIE / "pathfinding_tous_niveaux_cartes.json", "w", encoding="utf-8") as f:
        json.dump(resultats, f, indent=2, ensure_ascii=False)
    print("\nTermine, resultats enregistres dans pathfinding_tous_niveaux_cartes.json")
