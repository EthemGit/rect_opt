# core/neighbor_generator.py
from abc import ABC, abstractmethod
from typing import Iterable, Optional


class NeighborGenerator(ABC):
    """
    A NeighborGenerator is responsible for producing neighboring Solution objects
    for a given Problem+Solution. The generator *may* require knowledge of the
    Problem (box size, constraints) and therefore generate_neighbors receives
    the Problem and the current Solution.

    Implementations must implement `generate_neighbors(problem, solution)` which
    yields or returns an iterable of Solution objects (each a clone / copy).
    """

    @abstractmethod
    def generate_neighbors(self, problem, current_solution) -> Iterable:
        """Yield/return neighbor Solution objects (do NOT modify current_solution)."""
        raise NotImplementedError
    
    @abstractmethod
    def is_permutation_based(self) -> bool:
        """Return True if this neighbor generator works on permutation-based solutions."""
        raise NotImplementedError

    

    def best_improving_neighbor(self, problem, sol, *, first_improvement: bool = True, max_neighbors: int = 100):
        """
        Default helper: iterate over generate_neighbors and return an improving neighbor.
        - If first_improvement=True: return the first neighbor with strictly better score.
        - If first_improvement=False: scan whole neighborhood and return the best neighbor (if any).
        - max_neighbors: optional cap to number of neighbors inspected.
        Returns None if no improving neighbor exists.
        """
        count = 0
        current_sol = sol
        for potential_sol in self.generate_neighbors(problem, sol):
            if max_neighbors is not None and count >= max_neighbors:
                break
            count += 1
            if problem.is_better_solution(current_sol, potential_sol):
                current_sol = potential_sol
                if first_improvement:
                    return current_sol
        if current_sol != sol:
            return current_sol
        return None
