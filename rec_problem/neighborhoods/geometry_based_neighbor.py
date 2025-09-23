# rec_problem/neighborhoods/geometry_based_neighbor.py
from core.neighbor_generator import NeighborGenerator
from dataclasses import dataclass

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

        # Iterate rectangles that are currently positioned
        for rect in current_solution.rectangles:
            # we only move rectangles that are placed (skip unplaced for now)
            if not getattr(rect, "is_positioned", False):
                continue

            # find current box index for rect
            src_box_idx = None
            for i, b in enumerate(current_solution.boxes):
                if rect in b.my_rects:
                    src_box_idx = i
                    break
            if src_box_idx is None:
                continue

            # generate move targets: all existing boxes + a new empty box
            target_boxes = list(enumerate(current_solution.boxes))  # list of (idx, box)

            for tgt_idx, tgt_box in target_boxes:
                anchors = tgt_box.get_anchor_positions()
                for (ax, ay) in anchors:
                    # skip trivial same position
                    pos = tgt_box.my_rects.get(rect, None)
                    if pos == (ax, ay) and tgt_idx == src_box_idx:
                        continue
                    # skip attempts to replace a rect that is alone in its box
                    if tgt_idx == src_box_idx and len(tgt_box.my_rects) == 1:
                        continue

                    # ----- cheap feasibility pre-check (no clone) -----
                    feasible = False
                    if tgt_idx != src_box_idx:  # moving to another box
                        #  simple check if target box has space here
                        if tgt_box.rect_fits_here((ax, ay), rect):
                            feasible = True
                    else:  # moving within same box: candidate cells must be empty or belong to the rect itself

                        curx, cury = tgt_box.my_rects.get(rect)
                        # boundary quick-check
                        if ax < 0 or ay < 0 or (ax + rect.width) > tgt_box.box_length or (ay + rect.length) > tgt_box.box_length:
                            feasible = False
                        else:
                            cur_cells = {  # all grid cells currently occupied by the rect
                                (curx + dx, cury + dy) for dx in range(rect.width) for dy in range(rect.length)
                            }
                            cand_cells = {  # all grid grid cells the rectangle would occupy if moved
                                (ax + dx, ay + dy) for dx in range(rect.width) for dy in range(rect.length)
                            }
                            blocked = False
                            for cell in cand_cells:
                                if cell not in tgt_box.empty_coordinates and cell not in cur_cells:
                                    blocked = True
                                    break
                            feasible = not blocked

                    if not feasible:
                        continue
                    # ---------------------------------------------------

                    # perform move on a cloned solution
                    nb = current_solution.clone()
                    # find cloned rect (match by id to be safe)
                    cloned_rect = next((r for r in nb.rectangles if getattr(r, "id", None) == getattr(rect, "id", None)), None)
                    if cloned_rect is None:
                        continue

                    """ get the box where we want to insert the rect into. this has to be done here, BEFORE removing the 
                    rect from its current box and potentially deleting empty box. if done afterwards, the index may shift
                    which leads to hard-to-debug errors.""" 
                    tgt_b = nb.boxes[tgt_idx]

                    # remove from its current box in clone
                    for b in nb.boxes[:]:  # iterate over copy so we can delete
                        if cloned_rect in b.my_rects:
                            b.remove_rect(cloned_rect)
                            if not b.my_rects:  # box became empty
                                # delete empty box. otherwise value never decreases -> local search never progresses
                                nb.boxes.remove(b)  
                            break


                    # insert into target box in clone
                    try:
                        tgt_b.insert_rect(cloned_rect, (ax, ay))
                    except Exception:
                        # insertion failed unexpectedly; skip
                        continue

                    generated += 1
                    yield nb
                    if self.max_neighbors is not None and generated >= self.max_neighbors:
                        return

            # place rect in a new box at (0,0)
            if rect.width <= problem.box_length and rect.length <= problem.box_length:
                nb = current_solution.clone()
                cloned_rect = next((r for r in nb.rectangles if getattr(r,"id",None) == getattr(rect,"id",None)), None)
                if cloned_rect is None:
                    continue

                # remove from old box in cloned solution
                for b in nb.boxes[:]:  # iterate over copy so we can delete
                    if cloned_rect in b.my_rects:
                        b.remove_rect(cloned_rect)
                        if not b.my_rects:  # box became empty
                            # delete empty box. otherwise value never decreases -> local search never progresses
                            nb.boxes.remove(b)  
                        break

                # create new box, put rect at (0,0)
                from rec_problem.box import Box
                new_box = Box(box_length=problem.box_length)
                # use rect_fits_here with (0,0) to be consistent
                if new_box.rect_fits_here((0, 0), cloned_rect):
                    new_box.insert_rect(cloned_rect, (0, 0))
                    nb.boxes.append(new_box)
                    generated += 1
                    yield nb
                    if self.max_neighbors is not None and generated >= self.max_neighbors:
                        return
