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
        min_width: int,
        max_width: int,
        min_height: int,
        max_height: int,
    ):
        # Sanity checks
        assert box_length > 0, "Box length must be positive"
        assert rect_number > 0, "Number of rectangles must be positive"
        assert 0 < min_width <= max_width, "Invalid width bounds"
        assert 0 < min_height <= max_height, "Invalid height bounds"
        assert max_width <= box_length and max_height <= box_length, "Rect larger than box"

        # initialise attributes
        self.box_length: int = box_length
        self.rectangles: List[Rectangle] = []

        # create random rectangles
        for idx in range(rect_number):
            length = random.randint(min_height, max_height)
            width = random.randint(min_width, max_width)
            
            rect = Rectangle(length=length, width=width, id=idx)
            self.rectangles.append(rect)

        # immutable templates (sizes only) to reconstruct fresh rectangles by id
        self.rect_templates: dict[int, RectangleTemplate] = {
            r.id: RectangleTemplate(id=r.id, length=r.length, width=r.width) for r in self.rectangles
        }

    @classmethod
    def from_templates(cls, box_length: int, templates: List[RectangleTemplate]) -> "RectanglePackingProblem":
        """
        Create a fresh RectanglePackingProblem from a list of RectangleTemplate objects.
        Used by benchmarking to reconstruct problems without the random generation overhead.
        """
        # Create a minimal instance with no rectangles
        problem = cls.__new__(cls)
        problem.box_length = box_length
        problem.rectangles = [Rectangle(id=t.id, length=t.length, width=t.width) for t in templates]
        problem.rect_templates = {t.id: t for t in templates}
        return problem

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
            # only check anchor positions
            for (x, y) in box.get_anchor_positions():
                if box.rect_fits_here(coordinates=(x, y), rect=item):
                    box.insert_rect(rect=item, coordinates=(x, y))
                    return new_sol
                if box.rect_fits_here(coordinates=(x, y), rect=item_rot):
                    box.insert_rect(rect=item_rot, coordinates=(x, y))
                    return new_sol
        # Create new box if we cannot place rect in existing box
        new_box = Box(box_length)
        new_box.insert_rect(rect=item)
        new_sol.boxes.append(new_box)
        return new_sol

    # ----- LOCAL SEARCH -----------------------------------------------------------------------

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
        """
        # accept solutions with fewer boxes that have less than n rects 
        for n in range(2,5):
            old_number_of_boxes_with_few_rects = self._compute_number_of_boxes_with_n_rects(old_sol, n)
            new_number_of_boxes_with_few_rects = self._compute_number_of_boxes_with_n_rects(new_sol, n)
            if new_number_of_boxes_with_few_rects < old_number_of_boxes_with_few_rects:
                return True"""

        # accept if emptiest box got emptier
        if self._get_area_of_emptiest_box(new_sol) < self._get_area_of_emptiest_box(old_sol):
            return True

        return False

    def _get_area_of_emptiest_box(self, sol: RectanglePackingSolution):
        """Returns area of the box with most empty area."""
        boxes = sol.boxes
        min_empty_area = sol.box_length ** 2
        for box in boxes:
            empty_box_area = len(box.empty_coordinates)
            if empty_box_area < min_empty_area:
                min_empty_area = empty_box_area
        return min_empty_area

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
            rect_area = t.length * t.width         # both orientations have same area

            # try existing boxes in fixed order
            # sorted(empty_coordinates) gives row-major (bottom-left-fill) order while
            # skipping occupied cells — better placement quality than full grid scan
            for b in boxes:
                if len(b.empty_coordinates) < rect_area:
                    continue  # not enough free cells — skip
                for (x, y) in b.get_anchor_positions():
                    L1, W1 = t.length, t.width
                    if b.rect_fits_size(coordinates=(x, y), length=L1, width=W1):
                        r1 = Rectangle(id=t.id, length=t.length, width=t.width)
                        b.insert_rect(rect=r1, coordinates=(x, y))
                        placed_rects.append(r1)
                        placed = True
                        break

                    # didn't fit. check if rotated rect fits
                    L2, W2 = t.width, t.length  # rotated
                    if b.rect_fits_size(coordinates=(x, y), length=L2, width=W2):
                        r2 = Rectangle(id=t.id, length=L2, width=W2)
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

