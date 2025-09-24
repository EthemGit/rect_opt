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

        # Speedup A: build smarter rectangle candidates (last K boxes, largest M)
        candidates = self._build_candidates(current_solution, K=2, M=25)

        for rect, src_box_idx in candidates:

            # generate move targets: all existing boxes + a new empty box
            target_boxes = list(enumerate(current_solution.boxes))  # list of (idx, box)

            for tgt_idx, tgt_box in target_boxes:
                anchors = tgt_box.get_anchor_positions()
                for (ax, ay) in anchors:

                    # skip (same position) and (same-box moves when the box is a singleton)
                    if tgt_idx == src_box_idx:
                        pos = tgt_box.my_rects.get(rect, None)
                        if pos == (ax, ay) or len(tgt_box.my_rects) == 1:
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

                    # build a neighbor solution with partial cloning
                    nb = current_solution.clone_partial(src_box_idx, tgt_idx)
                    # find cloned rect inside nb
                    cloned_rect = next(
                        (r for r in nb.rectangles if getattr(r, "id", None) == getattr(rect, "id", None)),
                        None
                    )
                    if cloned_rect is None:
                        continue

                    # IMPORTANT: capture target box BEFORE removal (indices may shift if a box becomes empty)
                    tgt_b = nb.boxes[tgt_idx]

                    # remove from its current box in clone
                    for b in nb.boxes[:]:  # iterate over copy so we can delete
                        if cloned_rect in b.my_rects:
                            b.remove_rect(cloned_rect)
                            if not b.my_rects:  # box became empty
                                # delete empty box. otherwise value never decreases -> local search never progresses
                                nb.boxes.remove(b)  
                            break


                    # insert into the cloned/created target box
                    try:
                        tgt_b.insert_rect(cloned_rect, (ax, ay))
                    except Exception as e:
                        print(f"WARNING: failure at when trying to insert rect {cloned_rect} at {(ax,ay)}. Skipping this neighbor.\
                              Error is: {e} ")


                    generated += 1
                    yield nb
                    if self.max_neighbors is not None and generated >= self.max_neighbors:
                        return

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

