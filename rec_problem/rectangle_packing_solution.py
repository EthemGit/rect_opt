# Holds rectangles in boxes, computes score
# Stores current placement of rectangles, box assignments, can calculate objective (number of boxes).
# implements solution

from typing import List

from core.solution import Solution
from .rectangle import Rectangle
from .box import Box
import copy

class RectanglePackingSolution(Solution):
    def __init__(self, boxes, box_length, rectangles, permutation=None):
        """ 
        Args:
            problem: RectanglePaackingProblem
                Used to copy attributes rects and box_length.
           """
        self.rectangles: List[Rectangle] = rectangles
        self.boxes: List[Box] = boxes
        self.box_length: int = box_length
        # Canonical order used to (re)build layouts:
        # store as list[int] of rectangle IDs, never as mutable Rectangle instances
        self.permutation = list(permutation) if permutation is not None else [r.id for r in rectangles]
    
    def validate(self, permitted_error: float = 0.0):
        """
        Checks whether solution is permissible.

        Args:
            permitted_error: float
                Permitted overlap as fraction (currently unused; any overlap raises for >0).

        Raises:
            ValueError if any rect is out of bounds or rects overlap beyond permitted_error.
        """
        for box in self.boxes:
            occupied: dict = {}  # cell -> rect_id
            for rect, (px, py) in box.my_rects.items():
                # bounds check
                if px < 0 or py < 0:
                    raise ValueError(
                        f"Rect {rect.id} has negative coordinates ({px},{py})"
                    )
                if px + rect.width > self.box_length:
                    raise ValueError(
                        f"Rect {rect.id} exceeds box width: x={px}, width={rect.width}, box_length={self.box_length}"
                    )
                if py + rect.length > self.box_length:
                    raise ValueError(
                        f"Rect {rect.id} exceeds box length: y={py}, length={rect.length}, box_length={self.box_length}"
                    )
                # overlap check via cell occupation
                for dx in range(rect.width):
                    for dy in range(rect.length):
                        cell = (px + dx, py + dy)
                        if cell in occupied:
                            raise ValueError(
                                f"Overlap: rect {rect.id} vs rect {occupied[cell]} at cell {cell}"
                            )
                        occupied[cell] = rect.id

    def all_rects_positioned(self):
        """ Checks whether all rects are positioned in a box"""
        return all(rect.is_positioned for rect in self.rectangles)

    def get_objective_value(self):
        """ Returns objective value"""
        return len(self.boxes)

    def clone(self):
        """ Creates an identical solution"""
        cloned_boxes = [b.clone() for b in self.boxes]
        copy_sol = RectanglePackingSolution(
            boxes=cloned_boxes,
            box_length=self.box_length,
            rectangles=self.rectangles,
            permutation=self.permutation
        )
        return copy_sol
    
    def clone_partial(self, src_idx: int, tgt_idx: int):
        """
        Clone only the source and target boxes (cheap clone).
        Other boxes are shared. Safe because only src/tgt are mutated.
        This is optimized for local search (no new boxes are ever created).
        """
        new_boxes = list(self.boxes)

        # clone source box
        src_box = self.boxes[src_idx].clone()
        new_boxes[src_idx] = src_box

        # clone target box
        if tgt_idx == src_idx:
            tgt_box = src_box
        else:
            tgt_box = self.boxes[tgt_idx].clone()
            new_boxes[tgt_idx] = tgt_box

        # build new solution
        return RectanglePackingSolution(
            boxes=new_boxes,
            box_length=self.box_length,
            rectangles=self.rectangles,
            permutation=self.permutation
        )
