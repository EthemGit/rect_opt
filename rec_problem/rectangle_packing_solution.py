# Holds rectangles in boxes, computes score
# Stores current placement of rectangles, box assignments, can calculate objective (number of boxes).
# implements solution

from typing import List

import Solution
from rectangle import Rectangle
from box import Box
from rectangle_packing_problem import RectanglePackingProblem
from core.optimization_algorithm import OptimizationAlgo
from greedy.greedy_algo import GreedyAlgo
from local_search.local_search_algo import LocalSearchAlgo

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

    # GUI: Boxen (leer oder reudig)

    final_solution = algo.solve(initial_solution)

"""

class RectanglePackingSolution(Solution):
    def __init__(self, problem: RectanglePackingProblem, algo: OptimizationAlgo):
        """ 
        
        Args:
            problem: RectanglePaackingProblem
                Used to copy attributes rects and box_length.

            algo: OptimizationAlgo
                Used to determine which initial solution to create.
           """
        self.rectangles: List[Rectangle] = problem.rectangles
        self.boxes: List[Box] = []
        self.box_length: int = problem.box_length
        if type(algo) is LocalSearchAlgo:
            self.local_rects()            
    
    def local_rects(self):
        """ Initial bad solution for local search. Puts one rect in every box at coords 0, 0. """
        for i, rect in enumerate(self.rectangles):
            self.boxes[i] = Box(box_length=self.box_length, my_rects={rect: (0,0)})
    
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
    

