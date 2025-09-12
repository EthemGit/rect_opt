# Aufgabe: generates instances, validates inputs
# Manages problem parameters (box size, rectangle list), creates instances, validates solutions.
# Not necessarily tied to interface (could be helper class)

from typing import List
import random

from core.problem import Problem
from rec_problem.rectangle import Rectangle
from rec_problem.rectangle_packing_solution import RectanglePackingSolution

class RectanglePackingProblem(Problem):
    """
    Creates random rectangles based on parameters set by user
    Stores box length set by user 
    
    Attributes:
        - Box length
        - Set of rectangles
    """

    def __init__(
        self, 
        box_length: int,
        rect_number: int,
        rect_min_size: int,
        rect_max_size: int
    ):
        # Sanity checks
        assert box_length > 0, "Box length must be positive"
        assert rect_number > 0, "Number of rectangles must be positive"
        assert 0 < rect_min_size <= rect_max_size, "Invalid rectangle size bounds"

        # Attribute initialisieren
        self.box_length: int = box_length
        self.rectangles: List[Rectangle] = []

        # Random Rectangles erstellen
        for _ in range(rect_number):
            length = random.randint(rect_min_size, rect_max_size)
            width = random.randint(rect_min_size, rect_max_size)
            
            rect = Rectangle(length=length, width=width)
            self.rectangles.append(rect)

    # ----- GREEDY -------        
    def empty_solution(self) -> RectanglePackingSolution:
        """Creates initial empty solution for greedy algorithm"""
        pass
    
    def items_for_greedy(self) -> list:
        """Returns unplaced rectangles"""
        pass
    
    def process_item(self, sol: RectanglePackingSolution, item: Rectangle):
        """Selects box and places item (rect) inside it"""
        pass

    # ----- LOCAL SEARCH -----
    def bad_solution(self) -> RectanglePackingSolution:
        pass
    
    def neighbors(self, sol):
        pass
    
    def evaluate(self, sol) -> float:
        """Evaluates given solution. Needed for stop condition."""
        pass
