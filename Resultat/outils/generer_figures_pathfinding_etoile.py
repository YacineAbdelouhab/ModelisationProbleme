import json
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from Algorithmes.A_etoile.a_etoile import a_etoile
from Algorithmes.LLM_A_etoile_papier.llm_a_etoile_papier import llm_a_etoile_papier
from Algorithmes.Points_d_insertion_LLM.client_llm import demander_a_claude, demander_a_deepseek
from Jeux.Recherche_de_chemin.probleme_recherche_de_chemin import charger_depuis_fichier
from Jeux.Recherche_de_chemin.waypoints_llm_a_etoile import cout_vers_cible
from Resultat.outils.dessiner_recherche_de_chemin import dessiner_recherche_de_chemin
from Resultat.outils.dessiner_waypoints import dessiner_waypoints_pathfinding

DOSSIER_SORTIE = RACINE / "Resultat" / "Recherche_de_chemin" / "Experimentation"


def grille_avec_axes(probleme):
    # repere de lignes/colonnes -- aide le LLM a lire les coordonnees exactes
    # sans compter les caracteres a la main sur une grille large
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


def generer_waypoints_avec_intermediaires(probleme, demander, max_essais=3):
    # Variante illustrative du prompt officiel (Jeux/Recherche_de_chemin/waypoints_llm_a_etoile.py) :
    # demande EXPLICITEMENT des points intermediaires distincts du depart et du but, ce que le
    # prompt officiel n'exigeait pas assez clairement (il accepte une reponse reduite a depart+but,
    # observe sur plusieurs essais reels, cf. nb_dispositions=0 dans comparaison_fournisseurs.json).
    # Ajoute aussi un repere de lignes/colonnes -- sans lui, le LLM doit compter les caracteres a
    # la main sur une grille large, ce qui le fait "reflechir" longtemps (voire epuiser tout le
    # budget de tokens en reflexion sans jamais emettre de reponse, cf. demander_a_claude qui
    # renvoie "" si aucun bloc "text" n'est produit). D'ou le max_tokens tres eleve ci-dessous.
    # Sert uniquement a illustrer le mecanisme du papier avec un vrai trajet par points de passage,
    # PAS a remplacer le prompt officiel utilise pour les resultats mesures du rapport.
    grille_texte = grille_avec_axes(probleme)

    exemple = (
        "Voici un exemple.\n\n"
        "Grille 5x5 pour un problème de recherche de chemin. La règle en "
        "haut donne le numéro de colonne (x), le nombre à gauche de "
        "chaque ligne donne le numéro de ligne (y).\n"
        "'A' = départ, 'D' = but, '#' = mur, '.' = case libre :\n"
        "  01234\n"
        "0 A....\n1 .###.\n2 .....\n3 .###.\n4 ....D\n\n"
        "Départ : (0, 0)\nBut : (4, 4)\n\n"
        "REPONSE: (0,0) (0,2) (4,2) (4,4)\n\n"
        "Ici, les deux points intermédiaires (0,2) et (4,2) marquent les "
        "deux passages entre les murs, avant de rejoindre le but.\n\n"
        "Maintenant, fais la même chose pour la grille suivante.\n\n"
    )

    prompt = (
        exemple
        + "Grille pour un problème de recherche de chemin. La règle en "
        "haut donne le numéro de colonne (x), le nombre à gauche de "
        "chaque ligne donne le numéro de ligne (y).\n"
        "'A' = départ, 'D' = but, '#' = mur, '.' = case libre :\n"
        + grille_texte
        + f"\n\nDépart : {probleme.etat_initial}\nBut : {probleme.but}\n\n"
        "Propose une séquence de 3 à 6 coordonnées où doit passer le "
        "chemin optimal, de moindre coût, entre le départ et le but, qui "
        "te semble un bon itinéraire global. Évite les murs.\n\n"
        "Termine par exactement une ligne 'REPONSE: (x1,y1) (x2,y2) ...' "
        "avec le départ en premier point et le but en dernier point."
    )

    for essai in range(max_essais):
        texte = demander(prompt, max_tokens=16000)
        trouve = re.search(r"REPONSE:\s*(.+)", texte)
        if trouve:
            paires = re.findall(r"\((\d+)\s*,\s*(\d+)\)", trouve.group(1))
            candidats = [(int(x), int(y)) for x, y in paires]
            if candidats and candidats[0] != probleme.etat_initial:
                candidats.insert(0, probleme.etat_initial)
            if candidats and candidats[-1] != probleme.but:
                candidats.append(probleme.but)
            candidats = [c for c in candidats if c not in probleme.obstacles]
            intermediaires = [c for c in candidats[1:-1]]
            if len(candidats) >= 2 and len(intermediaires) >= 1:
                return candidats
        print(f"  essai {essai + 1}/{max_essais} : aucun point intermédiaire, on retente")
    return [probleme.etat_initial, probleme.but]  # repli si tous les essais echouent


def traiter(nom_niveau, chemin_fichier, waypoints_deja_connus=None):
    probleme = charger_depuis_fichier(str(chemin_fichier))

    # --- baseline, A* classique, sans LLM ---
    chemin_base, cout_base, fermes_base = a_etoile(probleme)
    print(f"{nom_niveau} baseline : cout={cout_base}, visites={len(fermes_base)}")
    dessiner_recherche_de_chemin(
        probleme, chemin_base, fermes_base,
        chemin_fichier=str(DOSSIER_SORTIE / f"visu_{nom_niveau}_baseline_etoile.png"),
    )

    # --- LLM-A* (papier), avec le prompt renforce pour obtenir de vrais points intermediaires ---
    # DeepSeek refuse systematiquement (6/6 essais, 2 niveaux x 3 tentatives) de proposer un
    # point intermediaire, meme avec ce prompt renforce -- on tente Claude, qui en donnait
    # naturellement sur des niveaux similaires (comparaison_fournisseurs.json).
    waypoints = generer_waypoints_avec_intermediaires(probleme, demander=demander_a_claude)
    print(f"{nom_niveau} waypoints (Claude, prompt renforce) : {waypoints}")
    chemin_wp, cout_wp, fermes_wp = llm_a_etoile_papier(probleme, lambda p: waypoints, cout_vers_cible)
    print(f"{nom_niveau} LLM-A* : cout={cout_wp}, visites={len(fermes_wp)}")

    titre = (
        f"Pathfinding {nom_niveau} — coût={cout_wp} (baseline={cout_base}), "
        f"{len(fermes_wp)} états visités (baseline={len(fermes_base)})"
    )
    dessiner_waypoints_pathfinding(
        probleme, chemin_wp, fermes_wp, waypoints, titre,
        str(DOSSIER_SORTIE / f"visu_{nom_niveau}_waypoints_etoile.png"),
    )

    return {
        "cout_baseline": cout_base, "visites_baseline": len(fermes_base),
        "cout_waypoints": cout_wp, "visites_waypoints": len(fermes_wp),
        "waypoints": waypoints,
    }


if __name__ == "__main__":
    resultats = {}
    resultats["niveau3_difficile"] = traiter(
        "niveau3_difficile", RACINE / "Jeux/Recherche_de_chemin/exemples/niveau3_difficile/carte1.txt"
    )
    with open(DOSSIER_SORTIE / "donnees_figures_etoile.json", "w", encoding="utf-8") as f:
        json.dump(resultats, f, indent=2, ensure_ascii=False)
    print(json.dumps(resultats, indent=2, ensure_ascii=False))
