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

    def initial_solution(self, problem):
        """Start from worst-case geometry: one rectangle per box."""
        from rec_problem.box import Box
        from rec_problem.rectangle_packing_solution import RectanglePackingSolution
        boxes = []
        for rect in problem.rectangles:
            box = Box(box_length=problem.box_length)
            box.insert_rect(rect)
            boxes.append(box)
        return RectanglePackingSolution(
            box_length=problem.box_length,
            rectangles=problem.rectangles,
            boxes=boxes
        )