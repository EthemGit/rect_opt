# Aufgabe: generates instances, validates inputs
# Manages problem parameters (box size, rectangle list), creates instances, validates solutions.
# Not necessarily tied to interface (could be helper class)

from typing import List
import random

from core.problem import Problem
from rec_problem.rectangle import Rectangle
from rec_problem.box import Box
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

        # initialise attributes
        self.box_length: int = box_length
        self.rectangles: List[Rectangle] = []

        # create random rectangles
        for _ in range(rect_number):
            length = random.randint(rect_min_size, rect_max_size)
            width = random.randint(rect_min_size, rect_max_size)
            
            rect = Rectangle(length=length, width=width)
            self.rectangles.append(rect)

    # ----- GREEDY ------------------------------------------------------------------

    def empty_solution(self) -> RectanglePackingSolution:
        """Creates initial empty solution for greedy algorithm"""
        return RectanglePackingSolution(boxes=[], problem=self)
    
    def items_for_greedy(self) -> list:
        """Returns unplaced rectangles"""
        return self.rectangles
    
    def process_item(self, sol: RectanglePackingSolution, item: Rectangle) -> None:
        """
        Selects a box and places item (rect) inside it
        called by GreedyAlgo.solve()

        Attributes:
            sol: RectanglePackingSolution
                Solution that is modified by sorting into a box. 
            item: Rectangle
                The item we want to place.
        """

        length = item.length
        width = item.width

        item_rot = Rectangle(length=width, width=length)

        for box in sol.boxes:
            # check if there is a gap that fits the given rect or its rotation
            box_length = box.box_length
            
            for y in range(box_length):
                for x in range(box_length):
                    if box.rect_fits_here(coordinates=(x, y), rect=item):
                        box.insert_rect(rect=item, coordinates=(x, y))
                        return
                    if box.rect_fits_here(coordinates=(x, y), rect=item_rot):
                        # rotate rect before positioning it
                        new_length = width
                        new_width = length
                        item.width = new_width
                        item.length = new_length
                        box.insert_rect(rect=item, coordinates=(x, y))
                        return
        # Create new box if we cannot place rect in existing box
        new_box = Box(box_length)
        new_box.insert_rect(rect=item)
        sol.boxes.append(new_box)
        return

    # ----- LOCAL SEARCH -----------------------------------------------------------------------
    
    def bad_solution(self) -> RectanglePackingSolution:
        pass
    
    def neighbors(self, sol):
        pass
    
    def evaluate(self, sol) -> float:
        """Evaluates given solution. Needed for stop condition."""
        pass
