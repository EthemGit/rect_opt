# rec_problem/neighborhoods/geometry_based_neighbor.py
from core.neighbor_generator import NeighborGenerator
from dataclasses import dataclass

from rec_problem.rectangle import Rectangle

import random

@dataclass
class GeometryBasedNeighborhood(NeighborGenerator):
    """
    Geometry-based neighborhood:
      - For each rectangle, try a small set of geometrically derived target coordinates:
        anchors = (0,0) and positions to the right / below of existing rects in a box.
      - Try moving rect to each existing box and to a new empty box.
    Parameters:
      - max_neighbors: optional cap for neighbors generated (helps performance)
    """
    max_neighbors: int = 200

    def generate_neighbors(self, problem, current_solution):
        """
        Generate neighbor solutions by moving single rectangles to anchor positions.
        Yields Solution objects (each must be a clone).
        Assumes:
          - current_solution.clone() returns a deep copy that can be modified,
          - boxes are in current_solution.boxes (list of Box),
          - Box provides can_place_at(rect, x, y) and insert_rect(rect, x, y) and remove_rect(rect).
        """
        generated = 0  # performance. to compare with max_neighbors and avoid too long runtime

        # Speedup A: build smarter rectangle candidates (last K boxes, largest M)
        candidates = self._build_candidates(current_solution)

        for rect, src_box_idx in candidates:

            # generate move targets: all existing boxes + a new empty box
            target_boxes = list(enumerate(current_solution.boxes))  # list of (idx, box)

            for tgt_box_idx, tgt_box in target_boxes:
                # avoid pushing rect around in same box
                if tgt_box_idx == src_box_idx:
                    continue

                for y in range(tgt_box.box_length):
                    for x in range(tgt_box.box_length):

                        # ----- cheap feasibility pre-check (no clone) -----
                        feasible = False
                        rotated = False
                        rect_rot = Rectangle(id=rect.id, length=rect.width, width=rect.length, is_positioned=rect.is_positioned)
                        #  simple check if target box has space here
                        feasible = tgt_box.rect_fits_here((x, y), rect)
                        # check if rotated rect fits
                        if not feasible:
                            feasible = tgt_box.rect_fits_here((x, y), rect_rot)
                            rotated = feasible
                        if not feasible:
                            continue
                        # ---------------------------------------------------

                        # build a neighbor solution with partial cloning
                        cloned_solution = current_solution.clone_partial(src_box_idx, tgt_box_idx)
                        # find cloned rect inside cloned solution
                        cloned_rect = next(
                            (r for r in cloned_solution.rectangles if getattr(r, "id", None) == getattr(rect, "id", None)),
                            None
                        )
                        if cloned_rect is None:
                            continue

                        # capture target and source boxes BEFORE removal (indices may shift if a box becomes empty)
                        tgt_box_in_clone = cloned_solution.boxes[tgt_box_idx]
                        src_box_in_clone = cloned_solution.boxes[src_box_idx]

                        # remove from its current box in clone
                        src_box_in_clone.remove_rect(cloned_rect)
                        if not src_box_in_clone.my_rects:  # box became empty
                            cloned_solution.boxes.remove(src_box_in_clone)

                        # insert into the cloned/created target box
                        try:
                            if rotated: # apply rotation if needed
                                tgt_box_in_clone.insert_rect(rect_rot, (x,y))
                            else:
                                tgt_box_in_clone.insert_rect(cloned_rect, (x, y))
                        except Exception as e:
                            print(f"WARNING: failure while trying to insert rect ({cloned_rect}) at {(x, y)}. Skipping this neighbor.\
                                Error is: {e} ")

                        generated += 1
                        yield cloned_solution
                        if self.max_neighbors is not None and generated >= self.max_neighbors:
                            return

    def is_permutation_based(self) -> bool:
        """This neighborhood is NOT permutation-based."""
        return False

    # ------- helpers ------------------

        # ---- Speedup patch A helper: pick largest M rects from last K boxes ----
    def _build_candidates(self, solution, K: int = 2, M: int = 25):
        """
        Return a list of (rect, src_box_idx) from the last K boxes.
        Within each such box, take the M largest rectangles (by area).
        """
        boxes = solution.boxes
        if not boxes:
            return []

        # indices of the last K boxes
        K = max(1, min(K, len(boxes)))
        tail_start = len(boxes) - K
        tail_indices = range(tail_start, len(boxes))

        candidates = []
        for bi in tail_indices:
            b = boxes[bi]
            # only placed rects
            rects = [r for r in b.my_rects.keys() if getattr(r, "is_positioned", False)]
            # largest first by area
            rects.sort(key=lambda r: r.width * r.length, reverse=True)
            # take top M
            rects = rects[:M]
            # collect with their source box index
            candidates.extend((r, bi) for r in rects)

        return candidates

    def _build_candidates_random(self, solution):
        """Returns 5 random (rect, src_box_idx) tuples."""
        boxes = solution.boxes
        if not boxes:
            return []

        # collect all positioned rects with their box index
        all_rects = []
        for bi, b in enumerate(boxes):
            rects = [r for r in getattr(b, "my_rects", {}).keys()
                     if getattr(r, "is_positioned", False)]
            # store tuples (rect, box_index)
            all_rects.extend((r, bi) for r in rects)

        if not all_rects:
            return []

        # sample without replacement
        return random.sample(all_rects, k=min(5, len(all_rects)))


