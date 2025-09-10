# abstract class
# creates neighboring solutions for local search
# Provides a way to generate neighbors from a given Solution (for local search).
# called by LocalSearchAlgo.solve()
# implemented in geometry_based_neighbor, partial_overlap_neighbor, rule_based_neighbor

from abc import ABC, abstractmethod

class NeighborGenerator(ABC):

    @abstractmethod
    def generate_neighbors(self, current_solution):
        """Generate and return a list of neighboring solutions."""
        pass

    def reset(self):
        """Reset internal state (default: do nothing)."""
        pass

    @abstractmethod
    def get_algo_type(self):
        pass