# rec_problem/neighborhoods/rule_based_neighbor.py
from core.neighbor_generator import NeighborGenerator
from dataclasses import dataclass
import random


@dataclass
class RuleBasedNeighborhood(NeighborGenerator):
    """
    Rule-based neighborhood: operates on permutations of rectangle IDs.
    Layout is rebuilt deterministically via problem.construct_from_order().

    Move strategy — diverse permutation exploration:
      - Targeted: rects from the sparsest boxes (most likely to be emptied).
      - Exploratory: random rects from across the permutation.
      - Moves are bidirectional: rects can move earlier (higher priority)
        OR later (lower priority, freeing prime slots for larger rects).
      - All moves are shuffled so the time budget samples broadly.

    Composite score (minimized):
      Fitness = B - (Σ fill_i²) / B, where fill_i = used_area_i / L².
      Squaring rewards polarization and creates a gradient toward box elimination.

    Highlighting:
      Each yielded solution has .highlighted_ids = {rect_id} set to the single
      rect that was moved in the permutation.
    """
    max_neighbors: int = 500
    time_budget_per_call_seconds: float = 1.5  # max seconds per best_improving_neighbor call

    # ------------------------------------------------------------------ #
    #  Core interface                                                      #
    # ------------------------------------------------------------------ #

    def generate_neighbors(self, problem, current_solution):
        perm = current_solution.permutation  # list of rect IDs
        n = len(perm)
        if n == 0:
            return

        perm_index = {rid: i for i, rid in enumerate(perm)}
        candidates = self._get_move_candidates(current_solution, perm)

        # Collect all moves, then shuffle for diversity across the time budget
        moves = []
        for cid in candidates:
            src_idx = perm_index.get(cid)
            if src_idx is None:
                continue
            for tgt_idx in self._sample_insert_positions(src_idx, n):
                moves.append(('insert', cid, src_idx, tgt_idx))
            for tgt_idx in self._sample_swap_positions(src_idx, n):
                moves.append(('swap', cid, src_idx, tgt_idx))

        random.shuffle(moves)

        generated = 0
        for move_type, cid, src_idx, tgt_idx in moves:
            new_perm = list(perm)
            if move_type == 'insert':
                new_perm.pop(src_idx)
                new_perm.insert(tgt_idx, cid)
            else:
                new_perm[src_idx], new_perm[tgt_idx] = new_perm[tgt_idx], new_perm[src_idx]
            sol = problem.construct_from_order(new_perm)
            sol.highlighted_ids = {cid}
            yield sol
            generated += 1
            if generated >= self.max_neighbors:
                return

    def best_improving_neighbor(self, problem, sol, *, first_improvement: bool = True, max_neighbors: int = 500):
        """
        Override to use composite score (box count + consolidation tiebreaker).
        Stops after self.time_budget_per_call_seconds to prevent a single long call
        from consuming the outer loop's entire time budget.
        """
        import time
        deadline = time.time() + self.time_budget_per_call_seconds if self.time_budget_per_call_seconds > 0 else None

        base_score = self._composite_score(sol)
        best = None
        best_score = base_score
        count = 0
        for nb in self.generate_neighbors(problem, sol):
            if max_neighbors is not None and count >= max_neighbors:
                break
            if deadline and time.time() > deadline:
                break
            count += 1
            score = self._composite_score(nb)
            if score < best_score:
                best = nb
                best_score = score
                if first_improvement:
                    return best
        return best

    def initial_solution(self, problem):
        """
        Deliberately bad start: smallest-area-first packing.
        Small rects pack inefficiently, producing many boxes.
        """
        rects = sorted(problem.rectangles, key=lambda r: r.get_area())
        # rects = problem.rectangles # use random ordering
        order_ids = [r.id for r in rects]
        return problem.construct_from_order(order_ids)

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _composite_score(self, sol) -> float:
        """
        Lower is better.
        Fitness = B - (Σ fill_i²) / B
        where fill_i = used_area_i / L² ∈ [0, 1].
        Squaring rewards polarization: one box at 99% + one at 1%
        scores better than two boxes at 50%, guiding toward box elimination.
        """
        if not sol.boxes:
            return 0
        B = len(sol.boxes)
        L2 = sol.box_length * sol.box_length
        sum_sq = sum(((L2 - len(b.empty_coordinates)) / L2) ** 2 for b in sol.boxes)
        return B - sum_sq / B

    def _get_move_candidates(self, solution, perm) -> list:
        """
        Return rect IDs to try as move candidates.
        Mix of targeted (sparsest boxes) and random exploration.
        """
        # Targeted: rects from sparsest boxes
        sparse = self._get_sparse_box_candidates(solution)
        seen = set(sparse)

        # Random: sample rects from across the full permutation
        n = len(perm)
        n_random = min(50, n)
        random_ids = []
        for idx in random.sample(range(n), min(n_random + len(seen), n)):
            rid = perm[idx]
            if rid not in seen:
                random_ids.append(rid)
                seen.add(rid)
            if len(random_ids) >= n_random:
                break

        # Interleave targeted and random for diversity
        result = []
        si, ri = 0, 0
        while si < len(sparse) or ri < len(random_ids):
            if si < len(sparse):
                result.append(sparse[si])
                si += 1
            if ri < len(random_ids):
                result.append(random_ids[ri])
                ri += 1
        return result

    def _get_sparse_box_candidates(self, solution) -> list:
        """
        Return rect IDs from the 3 boxes with the fewest rects (sparsest).
        """
        boxes = solution.boxes
        if not boxes:
            return []
        sorted_boxes = sorted(boxes, key=lambda b: len(b.my_rects))
        candidate_ids = []
        for box in sorted_boxes[:7]:
            for rect in box.my_rects.keys():
                candidate_ids.append(rect.id)
        return candidate_ids

    def _sample_insert_positions(self, src_idx: int, n: int) -> list:
        """
        Return a spread of target positions for insertion (bidirectional).
        Positions in [0, src_idx) move the rect earlier (higher placement priority).
        Positions in [src_idx+1, n) move it later (lower priority, freeing prime slots).
        """
        positions = []
        # Earlier positions
        if src_idx > 0:
            n_samples = min(src_idx, 5)
            step = max(1, src_idx // n_samples)
            positions.extend(range(0, src_idx, step))
            if src_idx - 1 not in positions:
                positions.append(src_idx - 1)
        # Later positions (in popped-array indexing: src_idx = same spot, so start at src_idx+1)
        later_end = n  # popped array has n-1 elements, valid insert indices 0..n-1
        if src_idx + 1 < later_end:
            remaining = later_end - src_idx - 1
            n_samples = min(remaining, 5)
            step = max(1, remaining // n_samples)
            positions.extend(range(src_idx + 1, later_end, step))
        return sorted(set(positions))

    def _sample_swap_positions(self, src_idx: int, n: int) -> list:
        """
        Return a spread of target positions for swapping (bidirectional).
        """
        positions = []
        # Earlier
        if src_idx > 0:
            n_samples = min(src_idx, 3)
            step = max(1, src_idx // n_samples)
            positions.extend(range(0, src_idx, step))
        # Later
        if src_idx < n - 1:
            remaining = n - src_idx - 1
            n_samples = min(remaining, 3)
            step = max(1, remaining // n_samples)
            positions.extend(range(src_idx + 1, n, step))
        return positions
