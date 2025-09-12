# Holds rectangles in boxes, computes score
# Stores current placement of rectangles, box assignments, can calculate objective (number of boxes).
# implements solution

from typing import List

from core.solution import Solution
from rectangle import Rectangle
from box import Box
from rectangle_packing_problem import RectanglePackingProblem

"""
    # main pseudo code
    problem_params = get_problem_params_from_GUI()
    problem = RectProblem(problem_params)

    # User sets Strategy in GUI
    strategy = Strategy()
    algo = strategy.get_algo()
    initial_solution = RectSolution(algo)
    # Konstruktor unterscheidet:
        greedy -> kein rect platziert
        local -> rects reudig platziert

    # GUI: Boxen (leer oder reudig) <<<------ klappt

    final_solution = algo.solve(initial_solution)

    
    TODO Donnerstag 11.9
    GUI
        params setzen
        --> rects erstellen
        strategy wählen
        --> initial solution wird generiert und angezeigt
            frage, wie ne solution angezeigt wird
"""

class RectanglePackingSolution(Solution):
    def __init__(self, problem: RectanglePackingProblem):
        """ 
        
        Args:
            problem: RectanglePaackingProblem
                Used to copy attributes rects and box_length.
           """
        self.rectangles: List[Rectangle] = problem.rectangles
        self.boxes: List[Box] = []
        self.box_length: int = problem.box_length        
    
    def validate(self, permitted_overlap: float):
        """ 
        Checks whether solution is permissible
        
        Args:
            permitted_overlap: float
                Permitted overlap in percentage ( = shared area / max(area_rect1, area_rect2) ).
        """

        # 1) alle platzierten Rechtecke sind innerhalb ihrer Box  
        # TODO

        # 2) Überlappungen nur so viel wie zulässig
        # TODO
        pass

    def all_rects_positioned(self):
        """ Checks whether all rects are positioned in a box"""
        return all(rect.is_positioned for rect in self.rectangles)

    def get_objective_value(self):
        """ Returns objective value"""
        return len(self.boxes)

    def clone(self):
        """ Creates an identical solution"""
        copy = RectanglePackingSolution(box_length=self.box_length, rects=self.rectangles)
        copy.boxes = self.boxes
        return copy
    

