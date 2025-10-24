# Aufgabe: generates instances, validates inputs
# Manages problem parameters (box size, rectangle list), creates instances, validates solutions.
# Not necessarily tied to interface (could be helper class)

from typing import List
import random

from core.problem import Problem
from rec_problem.rectangle import Rectangle
from rec_problem.box import Box
from rec_problem.rectangle_packing_solution import RectanglePackingSolution

from dataclasses import dataclass

@dataclass(frozen=True)
class RectangleTemplate:
    id: int
    length: int
    width: int
    

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
        for idx in range(rect_number):
            length = random.randint(rect_min_size, rect_max_size)
            width = random.randint(rect_min_size, rect_max_size)
            
            rect = Rectangle(length=length, width=width, id=idx)
            self.rectangles.append(rect)

        # NEW: immutable templates (sizes only) to reconstruct fresh rectangles by id
        self.rect_templates: dict[int, RectangleTemplate] = {
            r.id: RectangleTemplate(id=r.id, length=r.length, width=r.width) for r in self.rectangles
        }

    # ----- GREEDY ------------------------------------------------------------------

    def empty_solution(self) -> RectanglePackingSolution:
        """Creates initial empty solution for greedy algorithm"""
        return RectanglePackingSolution(boxes=[], box_length=self.box_length, rectangles=self.rectangles)
    
    def items_for_greedy(self) -> List:
        """Returns unplaced rectangles"""
        return self.rectangles
    
    def process_item(self, sol: RectanglePackingSolution, item: Rectangle) -> RectanglePackingSolution:
        """
        Creates a copy of the solution.
        Selects or creates a box and places item (rect) inside it
        called by GreedyAlgo.solve()

        Attributes:
            sol: RectanglePackingSolution
                Solution that is copied and modified by sorting into a box. 
            item: Rectangle
                The item we want to place.
        
        Returns
            New solution (modified copy of given parameter sol)
        """

        length = item.length
        width = item.width

        item_rot = Rectangle(length=width, width=length, id=item.id)  # rotated version of rect
        box_length = self.box_length

        new_sol = sol.clone()

        for box in new_sol.boxes:
            # check if there is a gap that fits the given rect or its rotation
            for y in range(box_length):
                for x in range(box_length):
                    if (x,y) in box.empty_coordinates:
                        if box.rect_fits_here(coordinates=(x, y), rect=item):
                            box.insert_rect(rect=item, coordinates=(x, y))
                            return new_sol
                        if box.rect_fits_here(coordinates=(x, y), rect=item_rot):
                            # rotate rect before positioning it
                            new_length, new_width = width, length
                            item.width, item.length = new_width, new_length
                            box.insert_rect(rect=item, coordinates=(x, y))
                            return new_sol
        # Create new box if we cannot place rect in existing box
        new_box = Box(box_length)
        new_box.insert_rect(rect=item)
        new_sol.boxes.append(new_box)
        return new_sol

    # ----- LOCAL SEARCH -----------------------------------------------------------------------
    
    def bad_solution(self) -> RectanglePackingSolution:
        """Returns a solution where each box contains exactly 1 rect at (0,0)."""
        boxes = []
        for rect in self.rectangles:
            box = Box(box_length=self.box_length)
            box.insert_rect(rect)
            boxes.append(box)

        return RectanglePackingSolution(box_length=self.box_length, rectangles=self.rectangles, boxes=boxes)
    
    def bad_permutation_solution(self) -> RectanglePackingSolution:
        boxes=[]

        self.rectangles = sorted(self.rectangles, key=lambda r: r.get_area())  # sort rectangles by area (smallest to largest)

        for rect in self.rectangles:
            positioned = False
            for box in boxes:
                anchors = box.get_anchor_positions()
                for (ax, ay) in anchors:
                    if box.rect_fits_here((ax, ay), rect):
                        box.insert_rect(rect, (ax, ay))
                        positioned = True
                        break
                
                if positioned:
                    break

            if not positioned:
                new_box = Box(self.box_length)
                new_box.insert_rect(rect)
                boxes.append(new_box)

        return RectanglePackingSolution(box_length=self.box_length, rectangles=self.rectangles, boxes=boxes)

    
    def neighbors(self, sol: RectanglePackingSolution):
        pass
    
    def evaluate(self, sol) -> float :
        """Evaluates given solution. Needed for stop condition."""
        return len(sol.boxes)
    
    def is_better_solution(self, old_sol: RectanglePackingSolution, new_sol: RectanglePackingSolution) -> bool:
        # never accept more boxes
        if len(new_sol.boxes) > len(old_sol.boxes):
            return False
        # always accept fewer boxes
        if len(new_sol.boxes) < len(old_sol.boxes):
            return True
        
        # accept solutions with fewer boxes that have less than 
        for n in range(2,5):
            old_number_of_boxes_with_few_rects = self._compute_number_of_boxes_with_n_rects(old_sol, n)
            new_number_of_boxes_with_few_rects = self._compute_number_of_boxes_with_n_rects(new_sol, n)
            if new_number_of_boxes_with_few_rects < old_number_of_boxes_with_few_rects:
                return True

        return False

    def _compute_number_of_boxes_with_n_rects(self, sol: RectanglePackingSolution, n: int=5) -> int:
        """Helper function to count number of boxes with less than n rectangles."""
        count = 0
        for box in sol.boxes: 
            if len(box.my_rects) < n: 
                count +=1    
        return count

    def construct_from_order(self, order_ids: List[int]) -> RectanglePackingSolution:
        """Deterministically build a full layout from a permutation of rectangle IDs."""
        boxes: List[Box] = []
        placed_rects: List[Rectangle] = []  # keep the actual objects used in this layout

        for rid in order_ids:
            t = self.rect_templates[rid]           # immutable (L, W)
            placed = False

            # try existing boxes in fixed order
            for b in boxes:
                for y in range(b.box_length):
                    for x in range(b.box_length):
                        r1 = Rectangle(id=t.id, length=t.length, width=t.width)
                        if (x,y) in b.empty_coordinates:
                            if b.rect_fits_here(coordinates=(x, y), rect=r1):
                                b.insert_rect(rect=r1, coordinates=(x, y))
                                placed_rects.append(r1)
                                placed = True
                                break

                            # didn't fit. check if rotated rect fits
                            r2 = Rectangle(id=t.id, length=t.width, width=t.length)
                            if b.rect_fits_here(coordinates=(x, y), rect=r2):
                                # rotate rect before positioning it
                                b.insert_rect(rect=r2, coordinates=(x, y))
                                placed_rects.append(r2)
                                placed = True
                                break
                    if placed:
                        break

            # if none fit, open new box and place at (0,0)
            if not placed:
                nb = Box(self.box_length)
                r0 = Rectangle(id=t.id, length=t.length, width=t.width)
                nb.insert_rect(r0, (0, 0))
                placed_rects.append(r0)
                boxes.append(nb)

        # Build the solution carrying the canonical permutation forward
        return RectanglePackingSolution(
            boxes=boxes,
            box_length=self.box_length,
            rectangles=placed_rects,
            permutation=order_ids
        )

