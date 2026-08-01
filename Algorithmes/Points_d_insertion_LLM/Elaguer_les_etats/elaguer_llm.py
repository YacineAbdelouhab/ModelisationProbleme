import re


def elaguer_llm(decrire_etat, demander, raisonnement_guide=False, expliquer_objectif=True):
    # decrire_etat : fonction etat -> texte, spécifique à chaque jeu
    # demander : fonction (prompt, max_tokens) -> texte -- demander_a_claude
    # ou demander_a_deepseek (client_llm.py), interchangeables
    #
    # renvoie une fonction etat -> booléen, utilisable comme elaguer_llm de
    # a_etoile() -- True = jugé impossible/sans issue, ne sera jamais exploré
    #
    # contrairement à heuristique_llm (min avec une valeur classique) ou
    # a_etoile (pathmax), il n'existe pas de garde-fou pour ce point : une
    # règle classique certaine (probleme.est_impossible) ne peut être
    # combinée sans neutraliser l'apport du LLM (tout état qui arrive
    # jusqu'ici a déjà passé les règles certaines, voir voisins() de
    # ProblemeSokoban -- un "ET" avec le classique renverrait donc toujours
    # faux). Limite acceptée : le LLM tranche seul, sans filet, à mesurer
    # empiriquement (comparer le coût avec/sans ce hook).
    #
    # raisonnement_guide (par défaut False) : au lieu de laisser un jugement
    # global libre, force à vérifier explicitement les 4 directions de
    # poussée de chaque caisse (mécanique Sokoban) -- teste si guider le
    # raisonnement corrige le raté observé sur un cas pourtant trivial
    # (coin mort raté par le jugement libre, voir notes_rapport.md). Pensé
    # pour Sokoban précisément (vocabulaire "caisse"/"poussée") ; pas de
    # sens particulier sur les jeux sans notion de cul-de-sac certain.
    #
    # expliquer_objectif (par défaut True) : explique en plus au LLM à quoi
    # sert sa réponse (un filtre dans une recherche A*, un faux "oui" peut
    # supprimer le seul chemin gagnant) -- teste si donner le contexte
    # d'usage le rend plus prudent, indépendamment de raisonnement_guide.
    def impossible(etat):
        objectif = (
            "Contexte : ta réponse sert de filtre dans un algorithme de "
            "recherche A* -- si tu réponds 'oui' à tort, cet état sera "
            "supprimé pour toujours de la recherche, ce qui peut faire "
            "rater le seul chemin gagnant ou la seule solution qui existe. "
            "Un 'non' à tort ne coûte qu'un peu de temps de recherche en "
            "plus, alors qu'un 'oui' à tort casse le résultat : sois donc "
            "prudent, ne réponds 'oui' que si tu es certain à 100%.\n\n"
            if expliquer_objectif else ""
        )
        if raisonnement_guide:
            prompt = (
                objectif
                + "Cet état de Sokoban est-il définitivement impossible à "
                "résoudre ? Une caisse est bloquée à jamais si, pour CHACUNE "
                "de ses 4 directions de poussée (haut/bas/gauche/droite), la "
                "poussée est impossible : soit la case où irait la caisse "
                "est un mur ou une autre caisse, soit la case où devrait se "
                "tenir le joueur (côté opposé) est un mur ou une autre "
                "caisse. Vérifie CHAQUE caisse une par une, en énumérant "
                "explicitement ses 4 directions une à une. Termine par "
                "exactement une ligne 'REPONSE: oui' ou 'REPONSE: non'.\n\n"
                + decrire_etat(etat)
            )
            max_tokens = 2500  # marge large : enumeration par caisse et par direction, raisonnement libre
        else:
            prompt = (
                objectif
                + "Cet état de puzzle est-il définitivement impossible à résoudre "
                "(un cul-de-sac dont on ne peut plus jamais atteindre le but, "
                "quels que soient les coups joués ensuite) ? Prends tout le "
                "temps de réflexion nécessaire, puis termine par exactement "
                "une ligne 'REPONSE: oui' ou 'REPONSE: non'.\n\n" + decrire_etat(etat)
            )
            max_tokens = 2000
        texte = demander(prompt, max_tokens=max_tokens)
        trouve = re.search(r"REPONSE:\s*(oui|non)", texte, re.IGNORECASE)
        return bool(trouve) and trouve.group(1).lower() == "oui"

    return impossible
