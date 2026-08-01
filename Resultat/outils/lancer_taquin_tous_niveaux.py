import json
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from Algorithmes.LLM_A_etoile_papier.llm_a_etoile_papier import llm_a_etoile_papier
from Algorithmes.Points_d_insertion_LLM.client_llm import demander_a_claude, demander_a_deepseek
from Jeux.Taquin.probleme_taquin import charger_depuis_fichier
from Jeux.Taquin.waypoints_llm_a_etoile import cout_vers_cible

DOSSIER_SORTIE = RACINE / "Resultat" / "Taquin" / "Experimentation"
DOSSIER_SORTIE.mkdir(exist_ok=True)

NIVEAUX = ["niveau1_facile", "niveau2_moyen", "niveau3_difficile"]
CARTES = ["carte1", "carte2", "carte3"]

# budgets valides par test (Claude reflechit moins que DeepSeek sur ce type de prompt)
TOKENS = {"Claude": 16000, "DeepSeek": 32000}


def generer_dispositions_avec_intermediaires(probleme, demander, tokens, max_essais=3):
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

    valeurs_attendues = set(range(n * n))
    for essai in range(max_essais):
        texte = demander(prompt, max_tokens=tokens)
        dispositions = []
        for i in range(1, 10):
            trouve = re.search(rf"DISPOSITION\s*{i}\s*:\s*(.+)", texte)
            if not trouve:
                break
            nombres = [int(x) for x in re.findall(r"\d+", trouve.group(1))][:n * n]
            if len(nombres) == n * n and set(nombres) == valeurs_attendues:
                dispositions.append(tuple(nombres))
        if dispositions:
            return [probleme.etat_initial] + dispositions + [probleme.but]
        print(f"  essai {essai + 1}/{max_essais} : aucune disposition, on retente")
    return [probleme.etat_initial, probleme.but]


def traiter(niveau, carte, fournisseur_nom, demander):
    chemin_fichier = RACINE / f"Jeux/Taquin/exemples/{niveau}/{carte}.txt"
    probleme = charger_depuis_fichier(str(chemin_fichier))

    from Algorithmes.A_etoile.a_etoile import a_etoile
    chemin_base, cout_base, fermes_base = a_etoile(probleme)

    dispositions = generer_dispositions_avec_intermediaires(
        probleme, demander=demander, tokens=TOKENS[fournisseur_nom]
    )
    chemin_wp, cout_wp, fermes_wp = llm_a_etoile_papier(probleme, lambda p: dispositions, cout_vers_cible)

    nb_intermediaires = max(0, len(dispositions) - 2)
    resultat = {
        "niveau": niveau, "carte": carte, "fournisseur": fournisseur_nom,
        "cout_baseline": cout_base, "visites_baseline": len(fermes_base),
        "cout_dispositions": cout_wp, "visites_dispositions": len(fermes_wp) if fermes_wp is not None else None,
        "nb_intermediaires": nb_intermediaires,
    }
    print(
        f"{niveau}/{carte} [{fournisseur_nom}] : baseline cout={cout_base} visites={len(fermes_base)} "
        f"| LLM-A* cout={cout_wp} visites={len(fermes_wp) if fermes_wp is not None else 'None'} "
        f"intermediaires={nb_intermediaires}"
    )
    return resultat


if __name__ == "__main__":
    resultats = []
    for niveau in NIVEAUX:
        for carte in CARTES:
            resultats.append(traiter(niveau, carte, "Claude", demander_a_claude))
            resultats.append(traiter(niveau, carte, "DeepSeek", demander_a_deepseek))
    with open(DOSSIER_SORTIE / "taquin_tous_niveaux_cartes.json", "w", encoding="utf-8") as f:
        json.dump(resultats, f, indent=2, ensure_ascii=False)
    print("\nTermine, resultats enregistres dans taquin_tous_niveaux_cartes.json")
