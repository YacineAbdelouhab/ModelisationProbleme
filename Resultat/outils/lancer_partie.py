import argparse
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # évite les accents mal affichés dans certains terminaux Windows

from Algorithmes.A_etoile.a_etoile import a_etoile
from Algorithmes.LLM_A_etoile_papier.llm_a_etoile_papier import llm_a_etoile_papier
from Algorithmes.Points_d_insertion_LLM.client_llm import demander_a_claude, demander_a_deepseek
from Algorithmes.Points_d_insertion_LLM.Ordonner_noeuds_a_explorer.ordonner_noeuds import departager_llm
from Algorithmes.Points_d_insertion_LLM.Calculer_Heuristique_d_un_noeud.heuristique_llm import heuristique_llm_lot
from Algorithmes.Points_d_insertion_LLM.Elaguer_les_etats.elaguer_llm import elaguer_llm

from Jeux.Recherche_de_chemin.probleme_recherche_de_chemin import charger_depuis_fichier as charger_pathfinding
from Jeux.Recherche_de_chemin.decrire_pour_llm import decrire_etat as decrire_pathfinding
from Jeux.Recherche_de_chemin.waypoints_llm_a_etoile import cout_vers_cible as cout_pathfinding

from Jeux.Taquin.probleme_taquin import charger_depuis_fichier as charger_taquin
from Jeux.Taquin.decrire_pour_llm import decrire_etat as decrire_taquin
from Jeux.Taquin.waypoints_llm_a_etoile import cout_vers_cible as cout_taquin

from Jeux.Sokoban.probleme_sokoban import charger_depuis_fichier as charger_sokoban
from Jeux.Sokoban.decrire_pour_llm import decrire_etat as decrire_sokoban

# réutilise telles quelles les fonctions de génération de cibles (waypoints/dispositions)
# validées lors de la ré-expérimentation complète (prompt + max_tokens corrects) --
# une seule version de chaque prompt, pas de copie qui pourrait diverger.
from Resultat.outils.generer_figures_pathfinding_etoile import (
    generer_waypoints_avec_intermediaires as generer_cibles_pathfinding,
)
from Resultat.outils.lancer_taquin_tous_niveaux import (
    generer_dispositions_avec_intermediaires as generer_cibles_taquin,
    TOKENS as TOKENS_TAQUIN,
)
from Resultat.outils.lancer_sokoban_tous_niveaux import (
    generer_dispositions_avec_intermediaires as generer_cibles_sokoban,
    cout_vers_cible as cout_sokoban,
    TOKENS as TOKENS_SOKOBAN,
)

FOURNISSEURS = {"claude": demander_a_claude, "deepseek": demander_a_deepseek}
NOM_FOURNISSEUR = {"claude": "Claude", "deepseek": "DeepSeek"}  # clés utilisées par les dicts TOKENS_*


def resoudre_chemin_fichier(jeu, niveau, carte):
    if jeu == "pathfinding":
        if not carte:
            raise SystemExit("--carte est requis pour --jeu pathfinding (ex: --niveau niveau2_moyen --carte carte1)")
        return RACINE / f"Jeux/Recherche_de_chemin/exemples/{niveau}/{carte}.txt"
    if jeu == "taquin":
        if not carte:
            raise SystemExit("--carte est requis pour --jeu taquin (ex: --niveau niveau1_facile --carte carte2)")
        return RACINE / f"Jeux/Taquin/exemples/{niveau}/{carte}.txt"
    # sokoban : --niveau est déjà un chemin complet, ex: microban/niveau2_moyen
    if carte:
        raise SystemExit("--carte ne s'utilise pas pour --jeu sokoban -- donne le chemin complet dans --niveau (ex: microban/niveau2_moyen)")
    return RACINE / f"Jeux/Sokoban/exemples/{niveau}.txt"


def charger_probleme(jeu, chemin_fichier):
    if jeu == "pathfinding":
        return charger_pathfinding(str(chemin_fichier))
    if jeu == "taquin":
        return charger_taquin(str(chemin_fichier))
    return charger_sokoban(str(chemin_fichier))


def decrire(jeu, probleme, etat):
    if jeu == "pathfinding":
        return decrire_pathfinding(probleme, etat)
    if jeu == "taquin":
        return decrire_taquin(probleme, etat)
    return decrire_sokoban(probleme, etat)


def resumer_etat(jeu, etat):
    # format compact, une ligne par état du chemin -- assez pour vérifier
    # visuellement le trajet sans ré-imprimer toute la grille à chaque pas
    if jeu == "sokoban":
        return f"joueur={etat.joueur} caisses={sorted(etat.caisses)}"
    return str(etat)


def lancer_llm_a_etoile(jeu, probleme, demander, fournisseur, max_etats_explores):
    nom = NOM_FOURNISSEUR[fournisseur]
    if jeu == "pathfinding":
        cibles = generer_cibles_pathfinding(probleme, demander)
        print(f"Points de passage proposés par le LLM : {cibles}")
    elif jeu == "taquin":
        cibles = generer_cibles_taquin(probleme, demander, tokens=TOKENS_TAQUIN[nom])
        print(f"Dispositions proposées par le LLM : {cibles}")
    else:
        cibles = generer_cibles_sokoban(probleme, demander=demander, tokens=TOKENS_SOKOBAN[nom])
        print(f"Dispositions proposées par le LLM : {cibles}")

    cout_cible = {"pathfinding": cout_pathfinding, "taquin": cout_taquin, "sokoban": cout_sokoban}[jeu]
    return llm_a_etoile_papier(probleme, lambda p: cibles, cout_cible, max_etats_explores=max_etats_explores)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Lance A* classique, un point d'insertion LLM, ou la reproduction du "
            "mécanisme LLM-A* du papier (waypoints/dispositions), sur un niveau donné."
        ),
    )
    parser.add_argument("--jeu", required=True, choices=["pathfinding", "taquin", "sokoban"])
    parser.add_argument(
        "--niveau", required=True,
        help=(
            "Pathfinding/Taquin : nom du dossier de niveau (ex: niveau2_moyen), à combiner avec --carte. "
            "Sokoban : chemin complet sans extension depuis Jeux/Sokoban/exemples/ (ex: microban/niveau2_moyen)."
        ),
    )
    parser.add_argument("--carte", default=None, help="Pathfinding/Taquin uniquement (ex: carte1)")
    parser.add_argument(
        "--mecanisme", default="astar",
        choices=["astar", "llm_a_etoile", "point1_departager", "point2_heuristique", "point3_elaguer"],
        help="astar = baseline classique. point1/2/3 = points d'insertion LLM dans A*. llm_a_etoile = reproduction du papier (aucune garantie d'optimalité).",
    )
    parser.add_argument("--fournisseur", default="claude", choices=list(FOURNISSEURS), help="LLM utilisé (ignoré pour --mecanisme astar)")
    parser.add_argument("--max-etats-explores", type=int, default=100_000)
    args = parser.parse_args()

    if args.mecanisme == "point3_elaguer" and args.jeu != "sokoban":
        raise SystemExit(
            "point3_elaguer n'a de sens que sur Sokoban : c'est le seul des trois jeux avec de vrais "
            "culs-de-sac certains à élaguer (voir rapport, section sur les points d'insertion)."
        )

    chemin_fichier = resoudre_chemin_fichier(args.jeu, args.niveau, args.carte)
    if not chemin_fichier.exists():
        raise SystemExit(f"Fichier introuvable : {chemin_fichier}")
    probleme = charger_probleme(args.jeu, chemin_fichier)
    demander = FOURNISSEURS[args.fournisseur]
    decrire_fn = lambda etat: decrire(args.jeu, probleme, etat)

    niveau_affiche = f"{args.niveau}/{args.carte}" if args.carte else args.niveau
    print(f"Jeu : {args.jeu} | Niveau : {niveau_affiche} | Mécanisme : {args.mecanisme}")
    if args.mecanisme != "astar":
        print(f"Fournisseur LLM : {args.fournisseur}")
    print()

    if args.mecanisme == "llm_a_etoile":
        chemin, cout, fermes = lancer_llm_a_etoile(args.jeu, probleme, demander, args.fournisseur, args.max_etats_explores)
    else:
        kwargs = {"max_etats_explores": args.max_etats_explores}
        if args.mecanisme == "point1_departager":
            kwargs["departager_llm"] = departager_llm(decrire_fn, demander)
        elif args.mecanisme == "point2_heuristique":
            kwargs["heuristique_llm_lot"] = heuristique_llm_lot(decrire_fn, probleme.heuristique, demander)
        elif args.mecanisme == "point3_elaguer":
            kwargs["elaguer_llm"] = elaguer_llm(decrire_fn, demander)
        chemin, cout, fermes = a_etoile(probleme, **kwargs)

    print()
    if chemin is None:
        print(f"Pas de solution trouvée (états visités : {len(fermes)})")
        return

    print(f"Coût : {cout}")
    print(f"États visités : {len(fermes)}")
    print(f"Longueur du chemin : {len(chemin)} états")
    print("Chemin :")
    for etat in chemin:
        print("  " + resumer_etat(args.jeu, etat))


if __name__ == "__main__":
    main()
