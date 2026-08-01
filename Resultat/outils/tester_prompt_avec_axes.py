import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from Algorithmes.Points_d_insertion_LLM.client_llm import demander_a_claude, demander_a_deepseek
from Algorithmes.LLM_A_etoile_papier.llm_a_etoile_papier import llm_a_etoile_papier
from Jeux.Recherche_de_chemin.probleme_recherche_de_chemin import charger_depuis_fichier
from Jeux.Recherche_de_chemin.waypoints_llm_a_etoile import cout_vers_cible


def grille_avec_axes(probleme):
    largeur, hauteur = probleme.largeur, probleme.hauteur
    label_width = len(str(hauteur - 1))

    tens = "".join(str(x // 10) if x >= 10 else " " for x in range(largeur))
    units = "".join(str(x % 10) for x in range(largeur))

    lignes = [" " * (label_width + 1) + tens, " " * (label_width + 1) + units]

    for y in range(hauteur):
        row_chars = []
        for x in range(largeur):
            case = (x, y)
            if case == probleme.etat_initial:
                row_chars.append("A")
            elif case == probleme.but:
                row_chars.append("D")
            elif case in probleme.obstacles:
                row_chars.append("#")
            else:
                row_chars.append(".")
        label = str(y).rjust(label_width)
        lignes.append(f"{label} " + "".join(row_chars))
    return "\n".join(lignes)


def construire_prompt(probleme):
    grille_texte = grille_avec_axes(probleme)
    return (
        "Grille pour un problème de recherche de chemin. La règle en haut "
        "donne le numéro de colonne (x), le nombre à gauche de chaque "
        "ligne donne le numéro de ligne (y).\n"
        "'A' = départ, 'D' = but, '#' = mur, '.' = case libre :\n"
        + grille_texte
        + f"\n\nDépart : {probleme.etat_initial}\nBut : {probleme.but}\n\n"
        "Propose une séquence de 3 à 6 coordonnées où doit passer le "
        "chemin optimal, de moindre coût, entre le départ et le but, qui "
        "te semble un bon itinéraire global. Évite les murs.\n\n"
        "Termine par exactement une ligne 'REPONSE: (x1,y1) (x2,y2) ...' "
        "avec le départ en premier point et le but en dernier point."
    )


if __name__ == "__main__":
    probleme = charger_depuis_fichier(
        str(RACINE / "Jeux/Recherche_de_chemin/exemples/niveau3_difficile/carte1.txt")
    )
    prompt = construire_prompt(probleme)
    print(prompt)
    print("=" * 60)

    for nom, fn in [("Claude", demander_a_claude), ("DeepSeek", demander_a_deepseek)]:
        for essai in range(1):
            texte = fn(prompt, max_tokens=16000)
            print(f"----- {nom} essai{essai + 1} (texte brut) -----")
            print(texte)
            trouve = re.search(r"REPONSE:\s*(.+)", texte)
            pts = re.findall(r"\((\d+)\s*,\s*(\d+)\)", trouve.group(1)) if trouve else []
            print(f"{nom} essai{essai + 1} parse : {pts}")
