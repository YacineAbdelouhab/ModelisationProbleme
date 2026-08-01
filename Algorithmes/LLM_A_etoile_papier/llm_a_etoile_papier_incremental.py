import heapq
import itertools


def llm_a_etoile_papier_incremental(probleme, choisir_prochaine_cible, cout_vers_cible, max_etats_sans_progres=30, max_etats_explores=None):
    """Variante incrémentale du LLM-A* du papier (voir llm_a_etoile_papier.py) :
    au lieu de générer TOUTE la liste de cibles à l'avance (figée), on ne
    décide QUE la prochaine cible, à partir de l'état RÉEL du moment où on
    en a besoin -- et on en redemande une nouvelle si la cible courante
    n'est pas atteinte après max_etats_sans_progres états fermés (bloqué).

    Pensée pour Sokoban : les sous-objectifs (caisses/cibles) s'interfèrent
    (la littérature confirme que les décomposer à l'avance est fragile --
    voir notes_rapport.md), décider avec l'état à jour limite ce risque, au
    prix de plusieurs appels LLM au lieu d'un seul (mais toujours beaucoup
    moins qu'un appel par état comme heuristique_llm/elaguer_llm).

    choisir_prochaine_cible(etat, cibles_non_remplies) -> une cible choisie
    parmi cibles_non_remplies (un ensemble, jamais vide quand appelée).
    cout_vers_cible(cible, etat) -> nombre, 0 si la cible est atteinte.

    Renvoie (chemin, cout, fermes), même format que les autres moteurs.
    """
    compteur = itertools.count()
    cout_g = {probleme.etat_initial: 0}
    vient_de = {}
    fermes = set()

    cibles_non_remplies = probleme.cibles - probleme.etat_initial.caisses
    cible_actuelle = choisir_prochaine_cible(probleme.etat_initial, cibles_non_remplies) if cibles_non_remplies else None
    etats_depuis_cible = 0

    def f_avec_cible(etat, g, h):
        if cible_actuelle is None:  # toutes les cibles deja remplies (etat initial == but, cas limite)
            return g + h
        return g + h + cout_vers_cible(cible_actuelle, etat)

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
        etats_depuis_cible += 1

        if max_etats_explores is not None and len(fermes) >= max_etats_explores:
            return None, None, fermes  # budget depasse -- pas de solution trouvee dans la limite

        cibles_non_remplies = probleme.cibles - etat.caisses
        if cible_actuelle is not None and cible_actuelle not in cibles_non_remplies:
            # cible atteinte (une caisse l'occupe desormais) -- en choisir une nouvelle
            cible_actuelle = choisir_prochaine_cible(etat, cibles_non_remplies) if cibles_non_remplies else None
            etats_depuis_cible = 0
        elif cibles_non_remplies and etats_depuis_cible >= max_etats_sans_progres:
            # bloque depuis trop longtemps sur la cible courante -- on redemande, avec l'etat a jour
            cible_actuelle = choisir_prochaine_cible(etat, cibles_non_remplies)
            etats_depuis_cible = 0

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
