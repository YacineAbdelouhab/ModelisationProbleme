import re


def heuristique_llm(decrire_etat, heuristique_secours, demander, proteger_admissibilite=True):
    # decrire_etat : fonction etat -> texte, spécifique à chaque jeu
    # heuristique_secours : fonction etat -> nombre (ex: probleme.heuristique),
    # une heuristique classique DONT ON SAIT qu'elle est admissible
    # demander : fonction (prompt, max_tokens) -> texte -- demander_a_claude
    # ou demander_a_deepseek (client_llm.py), interchangeables
    # proteger_admissibilite (par défaut True) : prend min(llm, classique) --
    # la désactiver (False) renvoie la valeur brute du LLM, pour observer le
    # comportement non protégé (utile pour l'expérimentation/la mesure)
    #
    # renvoie une fonction etat -> nombre, utilisable comme heuristique_llm
    # de a_etoile() -- REMPLACE complètement h(s), pas juste un départage
    def h(etat):
        prompt = (
            "Contexte : ton estimation sert d'heuristique dans une "
            "recherche A* -- si tu surestimes le vrai coût restant, la "
            "recherche peut manquer la solution optimale. Sous-estimer "
            "coûte juste un peu de temps de recherche en plus. Prends tout "
            "le temps de réflexion nécessaire pour être le plus précis "
            "possible, sans jamais dépasser le vrai coût restant.\n\n"
            "Estime le nombre minimal de coups restants pour résoudre ce "
            "puzzle depuis cet état. Termine par exactement une ligne "
            "'REPONSE: <nombre>'.\n\n" + decrire_etat(etat)
        )
        texte = demander(prompt, max_tokens=1500)
        trouve = re.search(r"REPONSE:\s*(\d+)", texte)
        valeur_llm = int(trouve.group(1)) if trouve else None

        valeur_classique = heuristique_secours(etat)
        if valeur_llm is None:
            return valeur_classique  # LLM inexploitable, on retombe entièrement sur le classique

        if not proteger_admissibilite:
            return valeur_llm  # comportement brut, non protégé -- pour l'expérimentation

        # PROTECTION ADMISSIBILITÉ : le LLM peut surestimer (h_llm > vrai
        # coût), mais l'heuristique classique, elle, ne surestime jamais.
        # En prenant le plus petit des deux, le résultat ne peut jamais
        # dépasser l'heuristique classique -- donc jamais dépasser la
        # vérité non plus. Ne protège PAS contre l'incohérence (un état
        # peut quand même sembler "trop proche" par rapport à son voisin) --
        # voir pathmax dans a_etoile.py pour ça.
        return min(valeur_llm, valeur_classique)

    return h


def heuristique_llm_lot(decrire_etat, heuristique_secours, demander, proteger_admissibilite=True):
    # comme heuristique_llm, mais note tout un lot d'états EN UN SEUL appel
    # API au lieu d'un appel par état -- divise le nombre d'appels par le
    # facteur de branchement, et donne au LLM les voisins comme point de
    # comparaison dans le même prompt
    #
    # renvoie une fonction etats -> {etat: valeur}, utilisable comme
    # heuristique_llm_lot de a_etoile() (paramètre séparé de heuristique_llm,
    # les deux ne sont pas utilisés en même temps)
    def noter(etats):
        descriptions = [
            f"--- Option {i} ---\n{decrire_etat(etat)}" for i, etat in enumerate(etats, start=1)
        ]
        prompt = (
            "Contexte : tes estimations servent d'heuristique dans une "
            "recherche A* -- si tu surestimes le vrai coût restant d'un "
            "état, la recherche peut manquer la solution optimale. "
            "Sous-estimer coûte juste un peu de temps de recherche en "
            "plus. Prends tout le temps de réflexion nécessaire pour être "
            "le plus précis possible, sans jamais dépasser le vrai coût "
            "restant.\n\n"
            f"Voici {len(etats)} états d'un même puzzle. Pour CHACUN, "
            "estime le nombre minimal de coups restants pour le résoudre. "
            "Termine par exactement une ligne par état, au format "
            "'REPONSE i: <nombre>' (une ligne par numéro).\n\n"
            + "\n\n".join(descriptions)
        )
        texte = demander(prompt, max_tokens=3000)  # marge large : plusieurs reponses a caser, raisonnement libre

        valeurs = {}
        for i, etat in enumerate(etats, start=1):
            trouve = re.search(rf"REPONSE\s*{i}\s*:\s*(\d+)", texte)
            valeur_classique = heuristique_secours(etat)
            if not trouve:
                valeurs[etat] = valeur_classique  # LLM inexploitable pour cet état, repli classique
            elif not proteger_admissibilite:
                valeurs[etat] = int(trouve.group(1))  # comportement brut, non protégé
            else:
                valeurs[etat] = min(int(trouve.group(1)), valeur_classique)  # même protection que heuristique_llm
        return valeurs

    return noter
