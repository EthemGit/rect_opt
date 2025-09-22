# rec_problem/neighborhoods/partial_overlap_neighbor.py
from core.neighbor_generator import NeighborGenerator
from dataclasses import dataclass

@dataclass
class PartialOverlapNeighborhood(NeighborGenerator):
    """
    Partial-overlap neighborhood:
      TODO
    Parameters:
      - max_neighbors: optional cap for neighbors generated (helps performance)
    """
    max_neighbors: int = 200

    def generate_neighbors(self, problem, current_solution):
        pass
    # TODO
