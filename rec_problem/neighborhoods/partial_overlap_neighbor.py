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
    Utilizes an Adjacency Graph to process overlaps in O(N) time instead of O(N^2),
    preventing massive CPU bottlenecks on instances > 500 rectangles.
    """
    def __init__(self, box_length):
        super().__init__(box_length)
        self.cell_counts = {}
        self.overlap_edges = {} # Stores pct: (id1, id2) -> pct
        self.rect_adj = {}      # Adjacency list: id -> set(overlapping_ids)

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
        self.rect_adj[rect.id] = set()

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
                    self.overlap_edges[k] = pct
                    self.rect_adj[rect.id].add(r2.id)
                    self.rect_adj[r2.id].add(rect.id)

    def remove_rect(self, rect) -> None:
        pos = self.my_rects.get(rect)
        if pos is None:
            raise ValueError(f"Rect {rect} not in this box.")
        
        posX, posY = pos

        # O(N) removal using the adjacency list instead of O(N^2) list comprehension
        for r2_id in self.rect_adj.get(rect.id,[]):
            k = (min(rect.id, r2_id), max(rect.id, r2_id))
            self.overlap_edges.pop(k, None)
            if r2_id in self.rect_adj:
                self.rect_adj[r2_id].discard(rect.id)
        
        self.rect_adj.pop(rect.id, None)

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
        new_box.overlap_edges = self.overlap_edges.copy()
        new_box.rect_adj = {k: set(v) for k, v in self.rect_adj.items()}
        return new_box


@dataclass
class PartialOverlapNeighborhood(NeighborGenerator):
    """
    Partial Overlap Geometry-based Local Search.
    Highly optimized with graph-based delta tracking.
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

        chunk_size = 15
        rects = problem.rectangles
        boxes = []
        for i in range(0, len(rects), chunk_size):
            box = OverlapBox(problem.box_length)
            for rect in rects[i:i + chunk_size]:
                box.insert_rect(rect, (0, 0))
            boxes.append(box)

        return RectanglePackingSolution(
            boxes=boxes,
            box_length=problem.box_length,
            rectangles=problem.rectangles
        )

    def _calc_penalty(self, pct, allowed_overlap):
        if pct > allowed_overlap:
            return 10.0 + (pct - allowed_overlap) * 100.0
        elif pct > 0:
            return 0.5 + pct * 0.5
        return 0.0

    def best_improving_neighbor(self, problem, sol, *, first_improvement=True, max_neighbors=500):
        deadline = time.time() + self.time_budget_per_call_seconds if self.time_budget_per_call_seconds > 0 else None

        best_move = None
        best_delta = 0.0  # By tracking ONLY the delta, we bypass O(N^2) penalty summations entirely
        count = 0

        candidates = self._get_move_candidates(sol, self.allowed_overlap)

        for (rect, src_box_idx) in candidates:
            src_box = sol.boxes[src_box_idx]
            n_s = len(src_box.my_rects)
            old_x, old_y = src_box.my_rects[rect]

            # Fast Delta: Retrieve the exact penalty contributed by ONLY the rect that is moving
            src_rect_penalty = 0.0
            if rect.id in src_box.rect_adj:
                for r2_id in src_box.rect_adj[rect.id]:
                    k = (min(rect.id, r2_id), max(rect.id, r2_id))
                    pct = src_box.overlap_edges[k]
                    src_rect_penalty += self._calc_penalty(pct, self.allowed_overlap)

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
                        tgt_rect_penalty = 0.0
                        box_delta = 1.0
                        consolidation_delta = (n_s - n_t - 1) * 0.001
                    elif tgt_box_idx == src_box_idx:
                        n_t = n_s
                        tgt_rect_penalty = self._rect_overlap_penalty_fast(test_rect, px, py, tgt_box, self.allowed_overlap)
                        box_delta = 0.0
                        consolidation_delta = 0.0
                    else:
                        n_t = len(tgt_box.my_rects)
                        tgt_rect_penalty = self._rect_overlap_penalty_fast(test_rect, px, py, tgt_box, self.allowed_overlap)
                        box_delta = 0.0
                        consolidation_delta = (n_s - n_t - 1) * 0.001

                    if n_s == 1 and tgt_box_idx != src_box_idx:
                        box_delta -= 1.0

                    move_penalty_delta = tgt_rect_penalty - src_rect_penalty
                    pos_delta = (px + py - old_x - old_y) * 0.00001
                    
                    move_delta = move_penalty_delta + box_delta + consolidation_delta + pos_delta

                    count += 1
                    if move_delta < best_delta:
                        best_delta = move_delta
                        best_move = (rect, src_box_idx, tgt_box_idx, px, py, rotated)
                        if first_improvement:
                            break
                if count >= max_neighbors or (deadline and time.time() > deadline) or (best_move and first_improvement):
                    break
            if count >= max_neighbors or (deadline and time.time() > deadline) or (best_move and first_improvement):
                break

        if best_move is None:
            if self.allowed_overlap > 0.0:
                self.allowed_overlap = max(0.0, self.allowed_overlap - 0.06)
                idle_sol = RectanglePackingSolution(sol.boxes, sol.box_length, sol.rectangles, getattr(sol, 'permutation', None))
                idle_sol.highlighted_ids = set() 
                return idle_sol
            else:
                compacted = self._compact_all_boxes(sol)
                if len(compacted.boxes) < len(sol.boxes):
                    self._did_final_compact = False
                    return compacted
                if not self._did_final_compact:
                    self._did_final_compact = True
                    return compacted
                if self._restart_count < 10:
                    self._restart_count += 1
                    self.allowed_overlap = 0.1
                    self._did_final_compact = False
                    idle_sol = RectanglePackingSolution(sol.boxes, sol.box_length, sol.rectangles, getattr(sol, 'permutation', None))
                    idle_sol.highlighted_ids = set()
                    return idle_sol
                return None

        self.allowed_overlap = max(0.0, self.allowed_overlap - 0.006)
        return self._apply_move(sol, *best_move, problem.box_length)

    def _rect_overlap_penalty_fast(self, rect, rect_x, rect_y, box, allowed_overlap):
        """
        Extremely optimized collision evaluation using inline AABB boundary checks
        to bypass the severe overhead of Python's built-in min() and max() functions.
        """
        penalty = 0.0
        a1 = rect.width * rect.length
        rw, rl = rect.width, rect.length
        rx_max = rect_x + rw
        ry_max = rect_y + rl
        
        for r2, (x2, y2) in box.my_rects.items():
            if r2.id == rect.id: continue
            
            # Fast AABB collision check before mathematical bounds calculation
            if rect_x < x2 + r2.width and rx_max > x2 and rect_y < y2 + r2.length and ry_max > y2:
                ix_min = rect_x if rect_x > x2 else x2
                ix_max = rx_max if rx_max < x2 + r2.width else x2 + r2.width
                iy_min = rect_y if rect_y > y2 else y2
                iy_max = ry_max if ry_max < y2 + r2.length else y2 + r2.length
                
                shared_area = (ix_max - ix_min) * (iy_max - iy_min)
                a2 = r2.width * r2.length
                pct = shared_area / (a1 if a1 > a2 else a2)
                
                if pct > allowed_overlap:
                    penalty += 10.0 + (pct - allowed_overlap) * 100.0
                else: 
                    penalty += 0.5 + pct * 0.5
        return penalty

    def _get_move_candidates(self, sol, allowed_overlap):
        violating_rects = set()
        
        # O(1) mathematical bypass: If allowed_overlap is 1.0, there are NO hard violations. 
        # This completely skips scanning 125,000 edges per step in the beginning.
        if allowed_overlap < 1.0:
            for bi, box in enumerate(sol.boxes):
                count = 0
                for (id1, id2), p in box.overlap_edges.items():
                    if p > allowed_overlap:
                        violating_rects.add((id1, bi))
                        violating_rects.add((id2, bi))
                        count += 1
                        if count > 50: # Cap dictionary iteration to avoid O(N^2) stalls
                            break

        candidates =[]
        for rid, bi in violating_rects:
            rect = next((r for r in sol.boxes[bi].my_rects if r.id == rid), None)
            if rect: candidates.append((rect, bi))

        straggler_front =[]
        if allowed_overlap == 0.0:
            for bi, box in enumerate(sol.boxes):
                if len(box.my_rects) == 1:
                    for r in box.my_rects:
                        straggler_front.append((r, bi))

        sparse_front =[]
        if not candidates:
            sorted_by_size = sorted(enumerate(sol.boxes), key=lambda item: len(item[1].my_rects))
            for bi, box in sorted_by_size[:7]:
                for r in box.my_rects:
                    sparse_front.append((r, bi))

        all_rects =[]
        for bi, box in enumerate(sol.boxes):
            for r in box.my_rects:
                all_rects.append((r, bi))

        random.shuffle(candidates)
        random.shuffle(all_rects)

        final_candidates = straggler_front + candidates[:50] + sparse_front + all_rects[:50]
        
        seen = set()
        unique_candidates = []
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
            if L <= 15:
                for gx in range(L - rect.width + 1):
                    for gy in range(L - rect.length + 1):
                        positions.add((gx, gy, False))
                for gx in range(L - rect.length + 1):
                    for gy in range(L - rect.width + 1):
                        positions.add((gx, gy, True))
            else:
                for _ in range(50):
                    positions.add((random.randint(0, L - rect.width), random.randint(0, L - rect.length), False))
                    positions.add((random.randint(0, L - rect.length), random.randint(0, L - rect.width), True))

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
        new_boxes =[
            self._bottom_left_repack(list(b.my_rects.keys()), sol.box_length)
            for b in sol.boxes
        ]

        changed = True
        while changed:
            changed = False
            for i in range(len(new_boxes)):
                if len(new_boxes[i].my_rects) != 1:
                    continue
                straggler = next(iter(new_boxes[i].my_rects))
                strag_area = straggler.width * straggler.length
                candidates_j = sorted(
                    [j for j in range(len(new_boxes)) if j != i],
                    key=lambda j: sum(r.width * r.length for r in new_boxes[j].my_rects),
                    reverse=True
                )
                for j in candidates_j:
                    tgt_used = sum(r.width * r.length for r in new_boxes[j].my_rects)
                    if tgt_used + strag_area > sol.box_length ** 2:
                        continue
                    combined = list(new_boxes[j].my_rects.keys()) +[straggler]
                    repacked = self._bottom_left_repack(combined, sol.box_length)
                    if len(repacked.my_rects) == len(combined):
                        new_boxes[j] = repacked
                        new_boxes[i] = None
                        changed = True
                        break
                if changed:
                    break
            new_boxes =[b for b in new_boxes if b is not None]

        new_sol = RectanglePackingSolution(
            boxes=new_boxes, box_length=sol.box_length,
            rectangles=sol.rectangles, permutation=getattr(sol, 'permutation', None)
        )
        new_sol.highlighted_ids = set()
        return new_sol