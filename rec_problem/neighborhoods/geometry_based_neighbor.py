# implements neighbor_generator
# neighborhood definition that generates neighbors by moving rectangles within/between boxes.

from core.neighbor_generator import NeighborGenerator
from dataclasses import dataclass

@dataclass
class GeometryBasedNeighborhood(NeighborGenerator):

    def generate_neighbors(self, current_solution):
        return 

    def best_improving_neighbor(problem, sol):
        return
    