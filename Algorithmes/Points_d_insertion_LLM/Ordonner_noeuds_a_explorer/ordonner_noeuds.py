import re


def departager_llm(decrire_etat, demander):
    # decrire_etat : fonction etat -> texte, spécifique à chaque jeu
    # demander : fonction (prompt, max_tokens) -> texte -- demander_a_claude
    # ou demander_a_deepseek (client_llm.py), interchangeables : ce module
    # ne sait pas lequel des deux il utilise
    #
    # renvoie une fonction candidats -> etat choisi, utilisable comme
    # departager_llm de a_etoile() -- appelée SEULEMENT sur une vraie
    # égalité de f (jamais pour comparer des f différents)
    def choisir(candidats):
        # candidats : liste de (etat, g, h), tous à f égal
        descriptions = [
            f"--- Option {i} ---\n{decrire_etat(etat)}" for i, (etat, g, h) in enumerate(candidats, start=1)
        ]
        prompt = (
            "Contexte : tu aides une recherche A* à choisir quel état "
            "explorer en premier parmi plusieurs qui semblent aussi "
            "prometteurs (même valeur f = coût + heuristique). Ton choix ne "
            "peut jamais faire manquer la solution optimale -- il influence "
            "seulement l'ordre d'exploration, donc la rapidité de la "
            "recherche. Prends tout le temps de réflexion nécessaire.\n\n"
            f"Voici {len(candidats)} états parmi lesquels choisir lequel "
            "explorer en premier. Termine par exactement une ligne "
            "'REPONSE: <numéro de l'option choisie>'.\n\n" + "\n\n".join(descriptions)
        )
        texte = demander(prompt, max_tokens=2000)

        trouve = re.search(r"REPONSE:\s*(\d+)", texte)
        if trouve:
            indice = int(trouve.group(1)) - 1
            if 0 <= indice < len(candidats):
                return candidats[indice][0]
        return candidats[0][0]  # repli : le premier par défaut si réponse inexploitable

    return choisir
