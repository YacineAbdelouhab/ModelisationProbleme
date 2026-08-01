import heapq
import itertools


def a_etoile(
    probleme,
    max_etats_explores=None,
    departager_llm=None,
    heuristique_llm=None,
    heuristique_llm_lot=None,
    elaguer_llm=None,
    proteger_consistance=True,
):
    """Recherche A* classique.

    Trouve un chemin de coût minimal entre probleme.etat_initial et un état
    vérifiant probleme.est_but(). Renvoie (chemin, cout, fermes) si une
    solution existe, sinon (None, None, fermes) -- fermes est l'ensemble des
    états explorés, utile pour visualiser la recherche (ex: les griser).

    max_etats_explores (optionnel) : arrête la recherche (résultat "pas de
    solution") si trop d'états ont été traités -- utile sur des problèmes
    où l'espace d'états peut exploser (Sokoban), pour ne jamais attendre
    indéfiniment.

    departager_llm (optionnel) : fonction qui reçoit la liste des états
    actuellement à égalité de f = g + h en tête des ouverts,
    [(etat, g, h), ...], et renvoie lequel explorer en premier. Appelée
    UNIQUEMENT quand une vraie égalité de f est détectée au moment de
    dépiler -- jamais pour comparer des f différents. Comme elle ne change
    donc jamais quel f est le plus petit, elle ne peut jamais faire manquer
    le vrai optimum à A* -- seul l'ordre d'exploration (et donc le nombre
    d'états explorés) peut changer. C'est le point d'insertion "Ordonner
    les nœuds à explorer".

    heuristique_llm (optionnel) : fonction etat -> nombre, REMPLACE
    complètement probleme.heuristique(). Contrairement à departager_llm,
    elle change directement quel f est le plus petit -- si le LLM n'est
    pas admissible (il peut surestimer le vrai coût restant), A* peut
    manquer l'optimum. C'est le point d'insertion "Calculer l'heuristique
    d'un nœud", et l'admissibilité doit être vérifiée empiriquement
    (comparer le coût obtenu à un run baseline), pas supposée.

    heuristique_llm_lot (optionnel, remplace heuristique_llm) : même rôle,
    mais note TOUS les voisins nouveaux d'un même nœud en un seul appel API
    (fonction etats -> {etat: valeur}) au lieu d'un appel par état -- divise
    le nombre d'appels par le facteur de branchement. Mêmes risques que
    heuristique_llm sur l'optimalité (admissibilité/consistance). Les deux
    paramètres ne sont pas utilisés en même temps.

    Deux protections partielles existent, aucune ne suffit seule (vérifié
    empiriquement) :
    - PATHMAX, ci-dessous dans h(), activée par proteger_consistance=True
      (défaut) : empêche f de chuter d'un état à son voisin (restaure la
      CONSISTANCE), mais ne peut jamais réduire une valeur déjà trop haute
      (protège pas l'ADMISSIBILITÉ).
    - le "min" avec l'heuristique classique, fait dans heuristique_llm.py
      lui-même (pas ici, voir son propre paramètre proteger_admissibilite) :
      protège l'ADMISSIBILITÉ, mais pas la consistance à lui seul.

    proteger_consistance (par défaut True) : active pathmax. La désactiver
    (False) sert à observer le comportement "brut" du LLM pour la mesure --
    sans effet sur une heuristique déjà consistante (comme les heuristiques
    classiques du projet), donc sans risque de la laisser à True partout
    ailleurs.

    elaguer_llm (optionnel) : fonction etat -> booléen (True = jugé
    impossible/sans issue). Un état élagué n'entre jamais dans les ouverts --
    s'il élague à tort un état qui faisait partie de tout chemin optimal,
    A* peut manquer l'optimum, voire ne trouver aucune solution du tout.
    C'est le point d'insertion "Élaguer les états", risque à vérifier
    empiriquement comme pour heuristique_llm.
    """

    h_fn = heuristique_llm or probleme.heuristique  # remplace complètement h si fourni

    compteur = itertools.count()  # compte : 0, 1, 2, ... un numéro par état poussé sur le tas, jamais deux fois le même

    cout_g = {probleme.etat_initial: 0}  # dictionnaire état : g(état)
    cout_h = {}  # dictionnaire état : h(état) final (après pathmax), mis en cache
    cout_h_brut = {}  # dictionnaire état : h(état) tel que renvoyé par h_fn, sans pathmax (calculé une seule fois -- évite les appels LLM redondants)
    vient_de = {}  # dictionnaire état : (état_parent, action_réalisé)
    fermes = set()  # états définitvement traités

    def h(etat, parent=None, cout_du_pas=None):
        if etat not in cout_h_brut:
            cout_h_brut[etat] = h_fn(etat)
        valeur = cout_h_brut[etat]

        if parent is not None and proteger_consistance:
            # PATHMAX : h ne peut pas chuter de plus que le coût du pas
            # qu'on vient de faire -- sinon f baisserait en avançant, ce
            # qui rendrait la fermeture d'un état non fiable (voir
            # docstring plus haut : ça restaure la consistance).
            valeur = max(valeur, cout_h[parent] - cout_du_pas)

        if etat not in cout_h or valeur > cout_h[etat]:
            cout_h[etat] = valeur
        return cout_h[etat]

    ouverts = []  # liste des noeuds voisin à potentiellement visiter
    if heuristique_llm_lot:
        cout_h_brut[probleme.etat_initial] = heuristique_llm_lot([probleme.etat_initial])[probleme.etat_initial]
    heapq.heappush(ouverts, (h(probleme.etat_initial), next(compteur), probleme.etat_initial))

    while ouverts:  # tant qu'il reste des états repérés à explorer
        f, _, etat = heapq.heappop(ouverts)  # l'état le plus prometteur (f le plus petit, puis billet)

        # égalité de f : d'autres états attendent-ils avec EXACTEMENT le
        # même f ? ouverts[0] regarde le sommet du tas sans le retirer,
        # donc ce test ne coûte rien si departager_llm n'est pas fourni.
        a_egalite = [etat]
        if departager_llm:
            while ouverts and ouverts[0][0] == f:
                _, _, autre = heapq.heappop(ouverts)
                a_egalite.append(autre)

        if len(a_egalite) > 1:
            infos = [(e, cout_g[e], h(e)) for e in a_egalite]
            etat = departager_llm(infos)  # choisit lequel explorer en premier PARMI les à-égalité
            for e in a_egalite:
                if e != etat:
                    heapq.heappush(ouverts, (f, next(compteur), e))  # les non-choisis retournent aux ouverts, même f

        if etat in fermes:
            continue  # copie obsolète d'un état déjà traité, on l'ignore

        if probleme.est_but(etat):
            return _reconstruire_chemin(vient_de, etat), cout_g[etat], fermes  # but atteint : chemin + son coût

        fermes.add(etat)  # etat est désormais définitivement traité

        if max_etats_explores is not None and len(fermes) >= max_etats_explores:
            return None, None, fermes  # budget dépassé -- pas de solution trouvée dans la limite

        voisins = list(probleme.voisins(etat))  # matérialisé une fois : réutilisé pour le lot ET la boucle

        if heuristique_llm_lot:
            a_evaluer = [e for _, e, _ in voisins if e not in fermes and e not in cout_h_brut]
            if a_evaluer:
                cout_h_brut.update(heuristique_llm_lot(a_evaluer))  # 1 seul appel pour tous les voisins nouveaux de CE nœud

        for action, etat_suivant, cout in voisins:  # chaque voisin légal
            if etat_suivant in fermes:
                continue  # déjà traité, inutile d'y revenir

            nouveau_g = cout_g[etat] + cout  # coût pour atteindre etat_suivant en passant par etat

            # etat_suivant jamais vu, ou ce chemin-ci est meilleur que le précédent connu
            if etat_suivant not in cout_g or nouveau_g < cout_g[etat_suivant]:
                if elaguer_llm and elaguer_llm(etat_suivant):
                    continue  # jugé impossible/sans issue -- jamais ajouté aux ouverts
                cout_g[etat_suivant] = nouveau_g  # on retient ce meilleur coût
                vient_de[etat_suivant] = (etat, action)  # ... et le parent qui y mène
                f_suivant = nouveau_g + h(etat_suivant, etat, cout)  # etat = parent ici, cout = coût du pas -- déclenche pathmax
                heapq.heappush(ouverts, (f_suivant, next(compteur), etat_suivant))  # candidat ajouté aux ouverts

    return None, None, fermes  # plus rien à explorer, but jamais atteint : pas de solution


def _reconstruire_chemin(vient_de, etat):
    """Remonte les parents depuis le but jusqu'au départ via vient_de."""
    chemin = [etat]
    while etat in vient_de:
        etat, action = vient_de[etat]
        chemin.append(etat)
    chemin.reverse()  # construit à l'envers (but -> départ), on remet dans le bon sens
    return chemin
