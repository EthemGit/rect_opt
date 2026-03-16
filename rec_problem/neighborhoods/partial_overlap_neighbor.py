# rec_problem/neighborhoods/partial_overlap_neighbor.py

from core.neighbor_generator import NeighborGenerator
from dataclasses import dataclass, field
from rec_problem.rectangle import Rectangle
from rec_problem.box import Box
from rec_problem.rectangle_packing_solution import RectanglePackingSolution
import random
import time

class OverlapBox(Box):
    """
    Specialized Box strictly for the Partial Overlap Neighborhood.
    Allows placing rectangles overlapping each other while precisely
    tracking cell occupancies and intersection percentages.
    """
    def __init__(self, box_length):
        super().__init__(box_length)
        self.cell_counts = {}
        self.overlap_pcts = {}

    def insert_rect(self, rect: Rectangle, coordinates=(0,0)) -> None:
        posX, posY = coordinates
        if (posX < 0 or posY < 0 or
            posX + rect.width > self.box_length or
            posY + rect.length > self.box_length
        ):
            raise ValueError(f"Rectangle does not fit in box at ({posX}, {posY})")

        for x in range(rect.width):
            for y in range(rect.length):
                c = (posX + x, posY + y)
                self.cell_counts[c] = self.cell_counts.get(c, 0) + 1
                if self.cell_counts[c] == 1:
                    self.empty_coordinates.discard(c)

        rect.is_positioned = True
        self.my_rects[rect] = (posX, posY)

        a1 = rect.width * rect.length
        for r2, (x2, y2) in list(self.my_rects.items()):
            if r2.id == rect.id:
                continue
            a2 = r2.width * r2.length
            ix_min = max(posX, x2)
            ix_max = min(posX + rect.width, x2 + r2.width)
            if ix_min < ix_max:
                iy_min = max(posY, y2)
                iy_max = min(posY + rect.length, y2 + r2.length)
                if iy_min < iy_max:
                    shared_area = (ix_max - ix_min) * (iy_max - iy_min)
                    pct = shared_area / max(a1, a2)
                    k = (min(rect.id, r2.id), max(rect.id, r2.id))
                    self.overlap_pcts[k] = pct

    def remove_rect(self, rect) -> None:
        pos = self.my_rects.get(rect)
        if pos is None:
            raise ValueError(f"Rect {rect} not in this box.")
        
        posX, posY = pos

        keys_to_remove =[k for k in self.overlap_pcts if rect.id in k]
        for k in keys_to_remove:
            del self.overlap_pcts[k]

        for x in range(rect.width):
            for y in range(rect.length):
                c = (posX + x, posY + y)
                self.cell_counts[c] -= 1
                if self.cell_counts[c] == 0:
                    del self.cell_counts[c]
                    self.empty_coordinates.add(c)

        rect.is_positioned = False
        del self.my_rects[rect]

    def clone(self):
        new_box = OverlapBox(self.box_length)
        new_box.my_rects = self.my_rects.copy()
        new_box.empty_coordinates = self.empty_coordinates.copy()
        new_box.cell_counts = self.cell_counts.copy()
        new_box.overlap_pcts = self.overlap_pcts.copy()
        return new_box


@dataclass
class PartialOverlapNeighborhood(NeighborGenerator):
    """
    Partial Overlap Geometry-based Local Search:
    - Allows overlaps that decay to 0%.
    - Mathematically rewards consolidation to eliminate sparse boxes.
    """
    max_neighbors: int = 500
    time_budget_per_call_seconds: float = 1.5
    allowed_overlap: float = field(default=1.0, init=False) 

    def generate_neighbors(self, problem, current_solution):
        yield from[]

    def initial_solution(self, problem):
        self.allowed_overlap = 1.0
        self._did_final_compact = False
        self._restart_count = 0
        box = OverlapBox(problem.box_length)
        for rect in problem.rectangles:
            box.insert_rect(rect, (0, 0))

        return RectanglePackingSolution(
            boxes=[box],
            box_length=problem.box_length,
            rectangles=problem.rectangles
        )

    def _calc_penalty(self, pct, allowed_overlap):
        """
        Mathematical Hierarchy:
        1. Illegal Overlap: > 10.0 (Instantly triggers opening a new box, which costs 1.0)
        2. Legal Overlap: 0.5 (Discourages overlaps, but prevents opening new boxes for legal ones)
        """
        if pct > allowed_overlap:
            return 10.0 + (pct - allowed_overlap) * 100.0
        elif pct > 0:
            return 0.5 + pct * 0.5
        return 0.0

    def best_improving_neighbor(self, problem, sol, *, first_improvement=True, max_neighbors=500):
        base_score = self._composite_score(sol, self.allowed_overlap)
        best_move = None
        best_score = base_score
        count = 0
        deadline = time.time() + self.time_budget_per_call_seconds if self.time_budget_per_call_seconds > 0 else None

        candidates = self._get_move_candidates(sol, self.allowed_overlap)

        for (rect, src_box_idx) in candidates:
            src_box = sol.boxes[src_box_idx]
            n_s = len(src_box.my_rects)
            old_x, old_y = src_box.my_rects[rect]

            src_penalty_with = sum(self._calc_penalty(p, self.allowed_overlap) for p in src_box.overlap_pcts.values())
            src_penalty_without = sum(self._calc_penalty(p, self.allowed_overlap) for k, p in src_box.overlap_pcts.items() if rect.id not in k)

            target_boxes = list(enumerate(sol.boxes))
            target_boxes.append((-1, None))
            random.shuffle(target_boxes)

            for tgt_box_idx, tgt_box in target_boxes:
                if tgt_box_idx == src_box_idx:
                    positions = self._sample_positions(tgt_box, rect, problem.box_length, same_box=True, old_pos=(old_x, old_y), allowed_overlap=self.allowed_overlap)
                elif tgt_box is None:
                    positions = [(0, 0, False)]
                else:
                    positions = self._sample_positions(tgt_box, rect, problem.box_length, allowed_overlap=self.allowed_overlap)

                for (px, py, rotated) in positions:
                    if count >= max_neighbors or (deadline and time.time() > deadline):
                        break

                    test_rect = Rectangle(id=rect.id, length=rect.width, width=rect.length) if rotated else rect

                    if tgt_box is None:
                        n_t = 0
                        tgt_penalty_with = 0.0
                        tgt_penalty_without = 0.0
                        box_delta = 1.0
                        consolidation_delta = (n_s - n_t - 1) * 0.001
                    elif tgt_box_idx == src_box_idx:
                        n_t = n_s
                        tgt_penalty_without = src_penalty_without
                        tgt_penalty_with = tgt_penalty_without + self._rect_overlap_penalty_fast(test_rect, px, py, tgt_box, self.allowed_overlap)
                        box_delta = 0.0
                        consolidation_delta = 0.0
                    else:
                        n_t = len(tgt_box.my_rects)
                        tgt_penalty_without = sum(self._calc_penalty(p, self.allowed_overlap) for p in tgt_box.overlap_pcts.values())
                        tgt_penalty_with = tgt_penalty_without + self._rect_overlap_penalty_fast(test_rect, px, py, tgt_box, self.allowed_overlap)
                        box_delta = 0.0
                        # Consolidation math: moving to denser box yields a negative (improving) score up to -0.3 max.
                        consolidation_delta = (n_s - n_t - 1) * 0.001

                    if n_s == 1 and tgt_box_idx != src_box_idx:
                        box_delta -= 1.0

                    move_penalty_delta = (tgt_penalty_with - tgt_penalty_without) - (src_penalty_with - src_penalty_without)
                    pos_delta = (px + py - old_x - old_y) * 0.00001
                    
                    move_score = base_score + move_penalty_delta + box_delta + consolidation_delta + pos_delta

                    count += 1
                    if move_score < best_score:
                        best_score = move_score
                        best_move = (rect, src_box_idx, tgt_box_idx, px, py, rotated)
                        if first_improvement:
                            break
                if count >= max_neighbors or (deadline and time.time() > deadline) or (best_move and first_improvement):
                    break
            if count >= max_neighbors or (deadline and time.time() > deadline) or (best_move and first_improvement):
                break

        if best_move is None:
            if self.allowed_overlap > 0.0:
                self.allowed_overlap = max(0.0, self.allowed_overlap - 0.02)
                idle_sol = RectanglePackingSolution(sol.boxes, sol.box_length, sol.rectangles, getattr(sol, 'permutation', None))
                idle_sol.highlighted_ids = set() 
                return idle_sol
            else:
                compacted = self._compact_all_boxes(sol)
                if len(compacted.boxes) < len(sol.boxes):
                    # Compaction eliminated straggler boxes — reset so we compact again
                    # after the next round of search finds another local optimum.
                    self._did_final_compact = False
                    return compacted
                if not self._did_final_compact:
                    self._did_final_compact = True
                    return compacted
                # Both compact rounds produced no box-count improvement.
                # Restart with a small overlap bump to escape the local optimum.
                if self._restart_count < 10:
                    self._restart_count += 1
                    self.allowed_overlap = 0.1
                    self._did_final_compact = False
                    idle_sol = RectanglePackingSolution(sol.boxes, sol.box_length, sol.rectangles, getattr(sol, 'permutation', None))
                    idle_sol.highlighted_ids = set()
                    return idle_sol
                return None

        self.allowed_overlap = max(0.0, self.allowed_overlap - 0.002)
        return self._apply_move(sol, *best_move, problem.box_length)

    def _composite_score(self, sol, allowed_overlap):
        score = len(sol.boxes)
        penalty = 0.0
        consolidation = 0.0
        pos_score = 0.0
        
        for box in sol.boxes:
            consolidation -= (len(box.my_rects) ** 2) * 0.0005
            for rect, (x, y) in box.my_rects.items():
                pos_score += (x + y) * 0.00001
            for p in box.overlap_pcts.values():
                penalty += self._calc_penalty(p, allowed_overlap)
                
        return score + penalty + consolidation + pos_score

    def _rect_overlap_penalty_fast(self, rect, rect_x, rect_y, box, allowed_overlap):
        penalty = 0.0
        a1 = rect.width * rect.length
        for r2, (x2, y2) in box.my_rects.items():
            if r2.id == rect.id: continue
            a2 = r2.width * r2.length
            ix_min = max(rect_x, x2)
            ix_max = min(rect_x + rect.width, x2 + r2.width)
            if ix_min < ix_max:
                iy_min = max(rect_y, y2)
                iy_max = min(rect_y + rect.length, y2 + r2.length)
                if iy_min < iy_max:
                    shared_area = (ix_max - ix_min) * (iy_max - iy_min)
                    pct = shared_area / max(a1, a2)
                    penalty += self._calc_penalty(pct, allowed_overlap)
        return penalty

    def _get_move_candidates(self, sol, allowed_overlap):
        violating_rects = set()
        for bi, box in enumerate(sol.boxes):
            for k, p in box.overlap_pcts.items():
                if p > allowed_overlap:
                    violating_rects.add((k[0], bi))
                    violating_rects.add((k[1], bi))

        candidates =[]
        for rid, bi in violating_rects:
            rect = next((r for r in sol.boxes[bi].my_rects if r.id == rid), None)
            if rect: candidates.append((rect, bi))

        # Single-rect straggler boxes (highest priority at endgame, ao==0 only)
        straggler_front = []
        if allowed_overlap == 0.0:
            for bi, box in enumerate(sol.boxes):
                if len(box.my_rects) == 1:
                    for r in box.my_rects:
                        straggler_front.append((r, bi))

        # Sparsest boxes: included when there are no active violations
        # (endgame consolidation). Putting them BEFORE violations during
        # the overlap-resolution phase would cause the algorithm to ignore
        # the large illegal-overlap box, stalling progress.
        sparse_front = []
        if not candidates:
            sorted_by_size = sorted(enumerate(sol.boxes), key=lambda item: len(item[1].my_rects))
            for bi, box in sorted_by_size[:7]:
                for r in box.my_rects:
                    sparse_front.append((r, bi))

        # Random exploration pool
        all_rects = []
        for bi, box in enumerate(sol.boxes):
            for r in box.my_rects:
                all_rects.append((r, bi))

        random.shuffle(candidates)
        random.shuffle(all_rects)

        # Merge: stragglers → violations → sparse (endgame only) → random
        final_candidates = straggler_front + candidates[:50] + sparse_front + all_rects[:50]
        
        seen = set()
        unique_candidates =[]
        for c in final_candidates:
            if c[0].id not in seen:
                seen.add(c[0].id)
                unique_candidates.append(c)

        return unique_candidates

    def _sample_positions(self, box, rect, L, same_box=False, old_pos=None, allowed_overlap=1.0):
        positions = set()
        if not same_box or old_pos != (0, 0):
            positions.add((0, 0, False))
            positions.add((0, 0, True))

        rects = list(box.my_rects.items())
        if len(rects) > 10:
            rects = random.sample(rects, 10)

        for r, (rx, ry) in rects:
            px, py = rx + r.width, ry
            if px + rect.width <= L and py + rect.length <= L: positions.add((px, py, False))
            if px + rect.length <= L and py + rect.width <= L: positions.add((px, py, True))

            px, py = rx, ry + r.length
            if px + rect.width <= L and py + rect.length <= L: positions.add((px, py, False))
            if px + rect.length <= L and py + rect.width <= L: positions.add((px, py, True))
                
            px, py = rx - rect.width, ry
            if px >= 0 and py + rect.length <= L: positions.add((px, py, False))
            px = rx - rect.length
            if px >= 0 and py + rect.width <= L: positions.add((px, py, True))

            px, py = rx, ry - rect.length
            if py >= 0 and px + rect.width <= L: positions.add((px, py, False))
            py = ry - rect.width
            if py >= 0 and px + rect.length <= L: positions.add((px, py, True))

        for _ in range(30):
            positions.add((random.randint(0, L - rect.width), random.randint(0, L - rect.length), False))
            positions.add((random.randint(0, L - rect.length), random.randint(0, L - rect.width), True))

        if allowed_overlap == 0.0:
            for gx in range(L - rect.width + 1):
                for gy in range(L - rect.length + 1):
                    positions.add((gx, gy, False))
            for gx in range(L - rect.length + 1):
                for gy in range(L - rect.width + 1):
                    positions.add((gx, gy, True))

        if same_box and old_pos:
            positions.discard((old_pos[0], old_pos[1], False))

        return list(positions)

    def _apply_move(self, sol, rect, src_box_idx, tgt_box_idx, px, py, rotated, box_length):
        new_boxes =[b.clone() for b in sol.boxes]
        src_box = new_boxes[src_box_idx]

        cloned_rect = next((r for r in src_box.my_rects if r.id == rect.id), None)
        if not cloned_rect:
            return sol

        src_box.remove_rect(cloned_rect)

        if rotated:
            cloned_rect = Rectangle(id=cloned_rect.id, length=cloned_rect.width, width=cloned_rect.length, is_positioned=True)

        if tgt_box_idx == -1:
            tgt_box = OverlapBox(box_length)
            new_boxes.append(tgt_box)
        else:
            tgt_box = src_box if tgt_box_idx == src_box_idx else new_boxes[tgt_box_idx]

        tgt_box.insert_rect(cloned_rect, (px, py))

        new_boxes =[b for b in new_boxes if len(b.my_rects) > 0]

        new_sol = RectanglePackingSolution(
            boxes=new_boxes, box_length=box_length, 
            rectangles=sol.rectangles, permutation=getattr(sol, 'permutation', None)
        )
        new_sol.highlighted_ids = {cloned_rect.id}
        return new_sol

    def _bottom_left_repack(self, rects, box_length):
        """Pack rects into a fresh OverlapBox using bottom-left fill (area-desc order)."""
        new_box = OverlapBox(box_length)
        for rect in sorted(rects, key=lambda r: r.width * r.length, reverse=True):
            placed = False
            for y in range(box_length):
                if placed: break
                for x in range(box_length):
                    if new_box.rect_fits_here((x, y), rect):
                        new_box.insert_rect(rect, (x, y))
                        placed = True
                        break
            if not placed:
                rect_rot = Rectangle(id=rect.id, length=rect.width, width=rect.length, is_positioned=True)
                for y in range(box_length):
                    if placed: break
                    for x in range(box_length):
                        if new_box.rect_fits_here((x, y), rect_rot):
                            new_box.insert_rect(rect_rot, (x, y))
                            placed = True
                            break
        return new_box

    def _compact_all_boxes(self, sol):
        """Repack every box with bottom-left fill and return as the final solution step.
        Also tries to eliminate single-rect straggler boxes by fitting them into other boxes."""
        new_boxes = [
            self._bottom_left_repack(list(b.my_rects.keys()), sol.box_length)
            for b in sol.boxes
        ]

        # Eliminate straggler boxes (1 rect) by repacking a target box that
        # has enough free area to absorb the straggler.
        changed = True
        while changed:
            changed = False
            for i in range(len(new_boxes)):
                if len(new_boxes[i].my_rects) != 1:
                    continue
                straggler = next(iter(new_boxes[i].my_rects))
                strag_area = straggler.width * straggler.length
                # Sort candidates: densest boxes that still have room
                candidates_j = sorted(
                    [j for j in range(len(new_boxes)) if j != i],
                    key=lambda j: sum(r.width * r.length for r in new_boxes[j].my_rects),
                    reverse=True
                )
                for j in candidates_j:
                    tgt_used = sum(r.width * r.length for r in new_boxes[j].my_rects)
                    if tgt_used + strag_area > sol.box_length ** 2:
                        continue  # not enough total area
                    combined = list(new_boxes[j].my_rects.keys()) + [straggler]
                    repacked = self._bottom_left_repack(combined, sol.box_length)
                    if len(repacked.my_rects) == len(combined):
                        new_boxes[j] = repacked
                        new_boxes[i] = None
                        changed = True
                        break
                if changed:
                    break
            new_boxes = [b for b in new_boxes if b is not None]

        new_sol = RectanglePackingSolution(
            boxes=new_boxes, box_length=sol.box_length,
            rectangles=sol.rectangles, permutation=getattr(sol, 'permutation', None)
        )
        new_sol.highlighted_ids = set()
        return new_sol