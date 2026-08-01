import heapq
import itertools


def llm_a_etoile_papier(probleme, generer_waypoints, cout_vers_cible, max_etats_explores=None):
    """Reproduction de l'algorithme LLM-A* du papier (Meng et al., 2024,
    "LLM-A*: Large Language Model Enhanced Incremental Heuristic Search on
    Path Planning") : le LLM génère une liste de points de passage
    (waypoints) une seule fois, au début, puis
        f(s) = g(s) + h(s) + cout(cible_actuelle, s)
    au lieu de juste g(s) + h(s). La cible actuelle avance dans la liste
    dès qu'un état l'atteint.

    Différence fondamentale avec les hooks de a_etoile.py : ce terme
    cout(cible, s) modifie directement f, donc peut changer quel état a le
    f le plus petit. AUCUNE garantie d'optimalité ici (comme dans le
    papier d'origine, qui rapporte ~102% du chemin optimal, pas 100%).

    generer_waypoints(probleme) -> liste de cibles, du départ au but inclus.
    Une cible n'est pas forcément un état complet (ex: Taquin -- un numéro
    de tuile, la cible est "atteinte" dès que cette tuile est à sa place,
    peu importe le reste du plateau) : cout_vers_cible décide seul de ce
    qui compte comme "atteint" (voir plus bas), pas une comparaison d'état.
    cout_vers_cible(cible, etat) -> nombre, 0 si la cible est atteinte
    (ex: distance de Manhattan pour une grille -- 0 ssi même coordonnée).

    max_etats_explores (optionnel) : borne le pire cas, comme dans a_etoile()
    -- utile sur des niveaux ou meme le classique explose (Sokoban original).

    Renvoie (chemin, cout, fermes), même format que a_etoile().

    Simplification par rapport au pseudocode original : les f des états
    déjà dans les ouverts ne sont pas recalculés quand la cible avance
    (étape 11 du papier) -- seuls les nouveaux états générés utilisent la
    cible à jour. Effet limité : une priorité un peu moins à jour pour des
    états déjà en attente, pas une erreur de calcul.
    """
    compteur = itertools.count()

    cibles = generer_waypoints(probleme)  # liste d'états : [depart, ..., but]
    indice_cible = 0

    cout_g = {probleme.etat_initial: 0}
    vient_de = {}
    fermes = set()

    def f_avec_cible(etat, g, h):
        return g + h + cout_vers_cible(cibles[indice_cible], etat)

    ouverts = []
    h_initial = probleme.heuristique(probleme.etat_initial)
    heapq.heappush(
        ouverts, (f_avec_cible(probleme.etat_initial, 0, h_initial), next(compteur), probleme.etat_initial)
    )

    while ouverts:
        _, _, etat = heapq.heappop(ouverts)

        if etat in fermes:
            continue

        if probleme.est_but(etat):
            return _reconstruire_chemin(vient_de, etat), cout_g[etat], fermes

        fermes.add(etat)

        if max_etats_explores is not None and len(fermes) >= max_etats_explores:
            return None, None, fermes  # budget depasse -- pas de solution trouvee dans la limite

        # avance la cible actuelle si on vient de l'atteindre (et que ce n'est
        # pas le but) -- teste via cout_vers_cible == 0 plutot qu'une egalite
        # stricte d'etat, pour accepter des cibles partielles (ex: Taquin,
        # une cible = un numero de tuile, pas un etat complet)
        if indice_cible < len(cibles) - 1 and cout_vers_cible(cibles[indice_cible], etat) == 0:
            indice_cible += 1

        for action, etat_suivant, cout in probleme.voisins(etat):
            if etat_suivant in fermes:
                continue

            nouveau_g = cout_g[etat] + cout
            if etat_suivant not in cout_g or nouveau_g < cout_g[etat_suivant]:
                cout_g[etat_suivant] = nouveau_g
                vient_de[etat_suivant] = (etat, action)
                h_suivant = probleme.heuristique(etat_suivant)
                f_suivant = f_avec_cible(etat_suivant, nouveau_g, h_suivant)
                heapq.heappush(ouverts, (f_suivant, next(compteur), etat_suivant))

    return None, None, fermes


def _reconstruire_chemin(vient_de, etat):
    chemin = [etat]
    while etat in vient_de:
        etat, action = vient_de[etat]
        chemin.append(etat)
    chemin.reverse()
    return chemin
