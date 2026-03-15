# core/neighbor_generator.py
from abc import ABC, abstractmethod
from typing import Iterable


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
    def initial_solution(self, problem):
        """Return the starting solution for local search.
        Each neighborhood decides what a suitable (typically bad) starting point is."""
        raise NotImplementedError

    def best_improving_neighbor(self, problem, sol, *, first_improvement: bool = True, max_neighbors: int = 100):
        """
        Default helper: iterate over generate_neighbors and return an improving neighbor.
        - If first_improvement=True: return the first neighbor with strictly better score.
        - If first_improvement=False: scan whole neighborhood and return the best neighbor (if any).
        - max_neighbors: optional cap to number of neighbors inspected.
        Returns None if no improving neighbor exists.
        """
        base_val = problem.evaluate(sol)
        best = None
        best_val = base_val
        count = 0
        for nb in self.generate_neighbors(problem, sol):
            if max_neighbors is not None and count >= max_neighbors:
                break
            count += 1
            val = problem.evaluate(nb)
            if val < best_val:
                best = nb
                best_val = val
                if first_improvement:
                    return best
        return best
