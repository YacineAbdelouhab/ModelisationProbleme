import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from Algorithmes.Points_d_insertion_LLM.client_llm import demander_a_claude, demander_a_deepseek


def prompt_taquin_renforce(probleme):
    n = probleme.n
    lignes = [probleme.etat_initial[i * n:(i + 1) * n] for i in range(n)]
    grille_depart = "\n".join(" ".join(("_" if v == 0 else str(v)) for v in ligne) for ligne in lignes)
    lignes_but = [probleme.but[i * n:(i + 1) * n] for i in range(n)]
    grille_but = "\n".join(" ".join(("_" if v == 0 else str(v)) for v in ligne) for ligne in lignes_but)
    return (
        f"Taquin {n}x{n} ('_' = case vide).\n"
        "Plateau de départ :\n" + grille_depart + "\n\n"
        "Plateau but :\n" + grille_but + "\n\n"
        "Contexte : ces dispositions intermédiaires vont guider une "
        "recherche A* -- de bonnes dispositions réduisent fortement le "
        "nombre d'états explorés, de mauvaises peuvent la ralentir.\n\n"
        "Donne OBLIGATOIREMENT 2 ou 3 dispositions COMPLÈTES "
        "INTERMÉDIAIRES, chacune différente du plateau de départ ET du "
        "plateau but (chaque chiffre de 1 à "
        f"{n * n - 1} et la case vide, chacun une seule fois). Une "
        "réponse vide ou identique au départ/but n'est pas acceptée. "
        "Termine par exactement une ligne par disposition, au format "
        "'DISPOSITION i: v1 v2 v3 ...' (les "
        f"{n * n} valeurs lues ligne par ligne, 0 pour la case vide)."
    )


def parser_taquin(texte, n):
    valeurs_attendues = set(range(n * n))
    dispositions = []
    for i in range(1, 10):
        trouve = re.search(rf"DISPOSITION\s*{i}\s*:\s*(.+)", texte)
        if not trouve:
            break
        nombres = [int(x) for x in re.findall(r"\d+", trouve.group(1))][:n * n]
        if len(nombres) == n * n and set(nombres) == valeurs_attendues:
            dispositions.append(tuple(nombres))
    return dispositions


def tester_taquin(nom_niveau, chemin_fichier, essais=2):
    from Jeux.Taquin.probleme_taquin import charger_depuis_fichier
    probleme = charger_depuis_fichier(str(chemin_fichier))
    prompt = prompt_taquin_renforce(probleme)
    for nom_fournisseur, demander in [("Claude", demander_a_claude), ("DeepSeek", demander_a_deepseek)]:
        for essai in range(essais):
            texte = demander(prompt, max_tokens=3000)
            dispositions = parser_taquin(texte, probleme.n)
            dispositions = [d for d in dispositions if d != probleme.etat_initial and d != probleme.but]
            print(f"Taquin {nom_niveau} {nom_fournisseur} essai{essai+1} : {len(dispositions)} disposition(s) intermediaire(s) reelle(s)")


def prompt_sokoban_renforce(probleme):
    from Jeux.Sokoban.decrire_pour_llm import decrire_etat
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    caisses_depart = list(probleme.etat_initial.caisses)
    cibles = list(probleme.cibles)
    couts = np.array([[abs(cx - tx) + abs(cy - ty) for (tx, ty) in cibles] for (cx, cy) in caisses_depart])
    lignes, colonnes = linear_sum_assignment(couts)
    affectation = [(caisses_depart[i], cibles[j]) for i, j in zip(lignes, colonnes)]
    return (
        "Voici une carte de Sokoban et l'affectation caisse -> cible la "
        "plus courte au total (calculée sans tenir compte de l'ordre) :\n"
        + "\n".join(f"Caisse en {c} -> cible en {t}" for c, t in affectation)
        + "\n\n" + decrire_etat(probleme, probleme.etat_initial)
        + "\n\nContexte : ces dispositions vont guider une recherche A* -- "
        "de bonnes dispositions intermédiaires réduisent fortement le "
        "nombre d'états explorés.\n\n"
        "Donne OBLIGATOIREMENT 2 ou 3 dispositions INTERMÉDIAIRES des "
        "caisses, chacune différente de la disposition de départ ET de la "
        "disposition finale (chaque caisse sur sa cible assignée). Une "
        "réponse vide ou identique au départ/final n'est pas acceptée. "
        "Termine par exactement une ligne par disposition, au format "
        "'DISPOSITION i: (x,y) (x,y) ...'"
    )


def parser_sokoban(texte, nb_caisses):
    dispositions = []
    for i in range(1, 10):
        trouve = re.search(rf"DISPOSITION\s*{i}\s*:\s*(.+)", texte)
        if not trouve:
            break
        paires = re.findall(r"\((\d+)\s*,\s*(\d+)\)", trouve.group(1))
        if len(paires) == nb_caisses:
            dispositions.append(frozenset((int(x), int(y)) for x, y in paires))
    return dispositions


def tester_sokoban(nom_niveau, chemin_fichier, essais=2):
    from Jeux.Sokoban.probleme_sokoban import charger_depuis_fichier
    probleme = charger_depuis_fichier(str(chemin_fichier))
    prompt = prompt_sokoban_renforce(probleme)
    depart = frozenset(probleme.etat_initial.caisses)
    final = frozenset(probleme.cibles)
    for nom_fournisseur, demander in [("Claude", demander_a_claude), ("DeepSeek", demander_a_deepseek)]:
        for essai in range(essais):
            texte = demander(prompt, max_tokens=3000)
            dispositions = parser_sokoban(texte, len(probleme.etat_initial.caisses))
            dispositions = [d for d in dispositions if d != depart and d != final]
            print(f"Sokoban {nom_niveau} {nom_fournisseur} essai{essai+1} : {len(dispositions)} disposition(s) intermediaire(s) reelle(s)")


if __name__ == "__main__":
    tester_taquin("niveau2_moyen", RACINE / "Jeux/Taquin/exemples/niveau2_moyen/carte1.txt")
    tester_sokoban("microban_niveau2_moyen", RACINE / "Jeux/Sokoban/exemples/microban/niveau2_moyen.txt")
