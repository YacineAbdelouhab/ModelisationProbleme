from abc import ABC, abstractmethod

class Probleme(ABC):
    """Contrat qu'un jeu doit respecter pour qu'un algorithme de recherche
    générique (A*, LLM-A*) puisse le résoudre sans rien connaître de ses
    règles.
    """

    etat_initial = None

    @abstractmethod
    def est_but(self, etat):
        """True si etat est un état solution."""
        ...

    @abstractmethod
    def voisins(self, etat):
        """Coups légaux depuis etat : liste de
        (action, etat_suivant, cout_du_coup).
        """
        ...

    @abstractmethod
    def heuristique(self, etat):
        """Estimation admissible du coût restant entre etat et le but."""
        ...

    def est_impossible(self, etat):
        # pas abstraite : la plupart des jeux n'ont pas de notion de "cul-de-sac"
        # certain (ex: pathfinding, taquin -- tout état atteint reste résoluble),
        # donc False par défaut. Un jeu qui a une vraie règle prouvée (ex: Sokoban,
        # voir _coins_mortels dans probleme_sokoban.py) peut la redéfinir.
        return False
