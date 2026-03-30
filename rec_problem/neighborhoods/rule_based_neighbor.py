from core.neighbor_generator import NeighborGenerator
from dataclasses import dataclass
import random


@dataclass
class RuleBasedNeighborhood(NeighborGenerator):
    """
    Rule-based neighborhood over permutations of rectangle IDs.

    - Candidate IDs are selected from sparse/low-fill boxes first.
    - Within those boxes, larger and more awkward rectangles are prioritized.
    - Insert moves are biased toward earlier permutation positions.

    Acceptance objective:
        1) fewer boxes
        2) closer to largest-area-first permutation
        3) penalise sparse boxes
    """

    max_neighbors: int = 500
    time_budget_per_call_seconds: float = 1.5

    # For guiding search
    focus_sparse_boxes: int = 7
    targeted_candidate_cap: int = 120
    random_candidate_cap: int = 18
    exploration_late_move_prob: float = 0.22
    sparse_fill_threshold: float = 0.35

    _laf_order_key: tuple = ()
    _laf_pos_by_id: dict | None = None

    # Guiding initial solution to make it deliberately, but bounded, bad.
    initial_target_gap_min_ratio: float = 0.14
    initial_target_gap_max_ratio: float = 0.24
    initial_attempts_per_rate: int = 4

    # ------------------------------------------------------------------ #
    #  Core interface                                                     #
    # ------------------------------------------------------------------ #

    def generate_neighbors(self, problem, current_solution):
        perm = current_solution.permutation
        n = len(perm)
        if n == 0:
            return

        perm_index = {rid: i for i, rid in enumerate(perm)}
        generated = 0

        # Priority 1: block moves from sparse boxes (coordinated moves)
        for new_perm, block_ids in self._get_block_moves(current_solution, perm, perm_index):
            sol = problem.construct_from_order(new_perm)
            sol.highlighted_ids = block_ids
            yield sol
            generated += 1
            if generated >= self.max_neighbors:
                return

        # Priority 2: single-rect guided moves
        candidates = self._get_move_candidates(problem, current_solution, perm, perm_index)

        moves = []
        for cid in candidates:
            src_idx = perm_index.get(cid)
            if src_idx is None:
                continue

            for tgt_idx in self._sample_insert_positions(src_idx, n):
                moves.append(("insert", cid, src_idx, tgt_idx))
            for tgt_idx in self._sample_swap_positions(src_idx, n):
                moves.append(("swap", cid, src_idx, tgt_idx))

        random.shuffle(moves)

        for move_type, cid, src_idx, tgt_idx in moves:
            new_perm = list(perm)
            if move_type == "insert":
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
        import time

        self._ensure_laf_reference(problem)

        deadline = (
            time.time() + self.time_budget_per_call_seconds
            if self.time_budget_per_call_seconds > 0
            else None
        )

        base_key = self._objective_key(sol)
        best = None
        best_key = base_key
        count = 0

        for nb in self.generate_neighbors(problem, sol):
            if max_neighbors is not None and count >= max_neighbors:
                break
            if deadline and time.time() > deadline:
                break
            count += 1

            key = self._objective_key(nb)
            if key < best_key:
                best = nb
                best_key = key
                if first_improvement:
                    return best
        return best

    def initial_solution(self, problem):
        """
        Build a deliberately bad start, but avoid catastrophic starts for large n.

        Strategy:
        1) Build a strong reference order (largest-area-first).
        2) Create damaged permutations by swapping large-early with small-late IDs.
        3) Choose a candidate whose box count falls in a target badness gap above
           the reference, so the start is bad yet still recoverable.
        """
        rects_desc = sorted(problem.rectangles, key=lambda r: r.get_area(), reverse=True)
        base_order = [r.id for r in rects_desc]
        area_by_id = {r.id: r.get_area() for r in problem.rectangles}

        base_sol = problem.construct_from_order(base_order)
        base_boxes = len(base_sol.boxes)

        n = len(base_order)
        gap_min_ratio = 0.30
        gap_max_ratio = 0.52
        attempts_per_rate = self.initial_attempts_per_rate + 3
        damage_rates = [0.24, 0.30, 0.36, 0.42, 0.50]

        target_min = base_boxes + max(1, int(round(base_boxes * gap_min_ratio)))
        target_max = base_boxes + max(2, int(round(base_boxes * gap_max_ratio)))
        target_center = (target_min + target_max) / 2.0
        fallback_max_boxes = base_boxes + max(3, int(round(base_boxes * 0.60)))

        best_sol = None
        best_penalty = float("inf")
        worst_bounded_sol = None
        worst_bounded_boxes = -1

        for rate in damage_rates:
            for _ in range(max(1, int(attempts_per_rate))):
                damaged_order = self._build_damaged_order(base_order, area_by_id, rate)
                cand = problem.construct_from_order(damaged_order)
                cand_boxes = len(cand.boxes)

                if target_min <= cand_boxes <= target_max:
                    return cand

                if n <= 500 and cand_boxes > worst_bounded_boxes and cand_boxes <= fallback_max_boxes:
                    worst_bounded_boxes = cand_boxes
                    worst_bounded_sol = cand

                # Prefer candidates above the good baseline and closest to target band center.
                if cand_boxes > base_boxes:
                    penalty = abs(cand_boxes - target_center)
                else:
                    penalty = abs(cand_boxes - target_center) + 1000.0
                if penalty < best_penalty:
                    best_penalty = penalty
                    best_sol = cand

        if n <= 500 and worst_bounded_sol is not None:
            return worst_bounded_sol

        if best_sol is not None:
            return best_sol

        # Last resort: keep requirement-compliant bad start.
        rects_asc = sorted(problem.rectangles, key=lambda r: r.get_area())
        return problem.construct_from_order([r.id for r in rects_asc])

    def _build_damaged_order(self, base_order, area_by_id, damage_rate: float):
        """
        Controlled damage by swapping large-early IDs with small-late IDs.
        This keeps structure from a strong order while making it intentionally worse.
        """
        n = len(base_order)
        if n <= 1:
            return list(base_order)

        new_order = list(base_order)
        if n <= 500:
            boundary_ratio = 0.55
        elif n <= 800:
            boundary_ratio = 0.41
        else:
            boundary_ratio = 0.39
        boundary = max(1, int(n * boundary_ratio))

        early_indices = list(range(0, boundary))
        late_indices = list(range(boundary, n))
        if not early_indices or not late_indices:
            return new_order

        early_sorted = sorted(early_indices, key=lambda i: area_by_id.get(new_order[i], 0), reverse=True)
        late_sorted = sorted(late_indices, key=lambda i: area_by_id.get(new_order[i], 0))

        max_pairs = min(len(early_sorted), len(late_sorted))
        pair_count = min(max_pairs, max(1, int(round(n * damage_rate))))

        # Keep strongest damaging pairs at the top, randomize mild variations per attempt.
        head_take = min(pair_count, max(4, pair_count // 2))
        head_early = early_sorted[:head_take]
        head_late = late_sorted[:head_take]
        random.shuffle(head_early)
        random.shuffle(head_late)

        selected_early = head_early
        selected_late = head_late
        if pair_count > head_take:
            tail_need = pair_count - head_take
            selected_early += random.sample(early_sorted[head_take:], min(tail_need, len(early_sorted) - head_take))
            selected_late += random.sample(late_sorted[head_take:], min(tail_need, len(late_sorted) - head_take))

        selected_early = selected_early[:pair_count]
        selected_late = selected_late[:pair_count]

        for i_early, i_late in zip(selected_early, selected_late):
            new_order[i_early], new_order[i_late] = new_order[i_late], new_order[i_early]

        if n <= 500 and damage_rate >= 0.30:
            rounds = max(1, int(damage_rate * 8))
            max_start = max(0, boundary - 6)
            for _ in range(rounds):
                if max_start <= 0:
                    break
                seg_len = min(boundary, max(6, int(n * 0.06)))
                start = random.randint(0, max(0, boundary - seg_len))
                seg = new_order[start : start + seg_len]
                random.shuffle(seg)
                new_order[start : start + seg_len] = seg
        elif n > 500 and damage_rate >= 0.30:
            rounds = max(1, int(damage_rate * 2))
            for _ in range(rounds):
                seg_len = max(8, int(n * 0.03))
                start = random.randint(0, max(0, boundary - seg_len))
                seg = new_order[start : start + seg_len]
                random.shuffle(seg)
                new_order[start : start + seg_len] = seg

        return new_order

    # ------------------------------------------------------------------ #
    #  Helpers                                                            #
    # ------------------------------------------------------------------ #

    def _objective_key(self, sol) -> tuple:
        """
        Objective key:
        1) fewer boxes
        2) closer to largest-area-first permutation
        3) lower sparse-penalty
        """
        return (
            len(sol.boxes),
            self._distance_to_laf(sol.permutation),
            self._sparse_penalty(sol),
        )

    def _ensure_laf_reference(self, problem):
        laf_order = tuple(r.id for r in sorted(problem.rectangles, key=lambda r: (-r.get_area(), r.id)))
        if laf_order == self._laf_order_key and self._laf_pos_by_id is not None:
            return

        self._laf_order_key = laf_order
        self._laf_pos_by_id = {rid: idx for idx, rid in enumerate(laf_order)}

    def _distance_to_laf(self, perm) -> int:
        if not self._laf_pos_by_id or not perm:
            return 0

        return sum(abs(idx - self._laf_pos_by_id.get(rid, idx)) for idx, rid in enumerate(perm))

    def _sparse_penalty(self, sol) -> float:
        if not sol.boxes:
            return 0.0

        box_area = sol.box_length * sol.box_length
        threshold = self.sparse_fill_threshold
        penalty = 0.0
        for box in sol.boxes:
            used_area = box_area - len(box.empty_coordinates)
            fill = used_area / box_area
            if fill < threshold:
                deficit = threshold - fill
                penalty += deficit * deficit
        return penalty

    def _get_block_moves(self, solution, perm, perm_index):
        """
        Yield coordinated block moves:
        1) insert whole sparse-box block earlier
        2) swap sparse-box block with earlier small-rectangle block
        """
        boxes = solution.boxes
        if not boxes:
            return

        # Find sparsest box (fewest rects or lowest fill).
        box_area = solution.box_length * solution.box_length
        worst_box = min(
            boxes,
            key=lambda b: (
                len(b.my_rects),
                (box_area - len(b.empty_coordinates)) / box_area,
            ),
        )

        if not worst_box.my_rects or len(worst_box.my_rects) > 15:
            return

        # Extract block IDs in current permutation order.
        block_rect_ids = sorted(
            (r.id for r in worst_box.my_rects.keys()),
            key=lambda rid: perm_index.get(rid, 0),
        )

        # Determine current block boundaries in permutation.
        block_indices = sorted(perm_index[rid] for rid in block_rect_ids)
        if not block_indices:
            return

        min_idx = min(block_indices)
        # Try explicit swap with earlier small rectangles first.
        area_by_id = {r.id: r.get_area() for r in solution.rectangles}
        block_set = set(block_rect_ids)
        earlier_ids = [rid for rid in perm[:min_idx] if rid not in block_set]
        if not earlier_ids:
            return

        small_earlier_ids = sorted(
            earlier_ids,
            key=lambda rid: (area_by_id.get(rid, 10**9), perm_index.get(rid, 0)),
        )
        swap_size = min(len(block_rect_ids), len(small_earlier_ids))
        if swap_size <= 0:
            return

        selected_small_ids = sorted(
            small_earlier_ids[:swap_size],
            key=lambda rid: perm_index.get(rid, 0),
        )
        selected_large_ids = block_rect_ids[:swap_size]

        large_positions = sorted(perm_index[rid] for rid in selected_large_ids)
        small_positions = sorted(perm_index[rid] for rid in selected_small_ids)

        new_perm = list(perm)
        for pos, rid in zip(small_positions, selected_large_ids):
            new_perm[pos] = rid
        for pos, rid in zip(large_positions, selected_small_ids):
            new_perm[pos] = rid

        moved_ids = set(selected_large_ids) | set(selected_small_ids)
        yield new_perm, moved_ids

        # Then generate insertion-based block moves.
        insertion_points = []
        if min_idx > 0:
            insertion_points.append(0)
            if min_idx > 2:
                insertion_points.append(min_idx // 3)
            insertion_points.append(max(0, min_idx - 2))

        for tgt_insert_pos in set(insertion_points):
            if tgt_insert_pos == min_idx:
                continue  # Skip no-op

            # Build new permutation: remove block, insert earlier.
            new_perm = [rid for rid in perm if rid not in block_rect_ids]
            new_perm[tgt_insert_pos : tgt_insert_pos] = block_rect_ids
            yield new_perm, set(block_rect_ids)

    def _get_move_candidates(self, problem, solution, perm, perm_index) -> list:
        """
        Guided candidate selection:
        1) Focus on sparse/low-fill boxes.
        2) Prioritize larger and awkward rectangles from those boxes.
        3) Keep a random tail for exploration.
        """
        targeted_ids = self._get_targeted_candidates(problem, solution, perm_index)
        seen = set(targeted_ids)

        # Keep the strongest guided head deterministic and diversify the tail.
        if len(targeted_ids) > 40:
            head = targeted_ids[:20]
            tail_pool = targeted_ids[20:]
            tail_take = min(20, len(tail_pool))
            tail = random.sample(tail_pool, tail_take)
            targeted_ids = head + tail

        random_ids = []
        if perm and self.random_candidate_cap > 0:
            sample_size = min(len(perm), self.random_candidate_cap * 3)
            for rid in random.sample(perm, sample_size):
                if rid in seen:
                    continue
                random_ids.append(rid)
                seen.add(rid)
                if len(random_ids) >= self.random_candidate_cap:
                    break

        return targeted_ids + random_ids

    def _get_targeted_candidates(self, problem, solution, perm_index) -> list:
        boxes = solution.boxes
        if not boxes:
            return []

        box_area = solution.box_length * solution.box_length

        # Worst boxes first: few rects, then lowest fill.
        ranked_boxes = sorted(
            boxes,
            key=lambda box: (
                len(box.my_rects),
                (box_area - len(box.empty_coordinates)) / box_area,
            ),
        )

        candidates = []
        for box in ranked_boxes[: self.focus_sparse_boxes]:
            rects = list(box.my_rects.keys())
            rects.sort(
                key=lambda r: (
                    -r.get_area(),
                    -max(r.length, r.width),
                    -abs(r.length - r.width),
                    -perm_index.get(r.id, 0),
                )
            )
            candidates.extend(r.id for r in rects)

        # Keep only top guided IDs to limit branching.
        if len(candidates) > self.targeted_candidate_cap:
            return candidates[: self.targeted_candidate_cap]
        return candidates

    def _sample_insert_positions(self, src_idx: int, n: int) -> list:
        """
        Strongly directional insertions:
        - mostly earlier positions
        - rarely include a couple of later positions for escape
        """
        if n <= 1:
            return []

        positions = []

        # Bias: earlier insertion points only.
        if src_idx > 0:
            n_samples = min(src_idx, 6)
            step = max(1, src_idx // n_samples)
            positions.extend(range(0, src_idx, step))
            positions.append(src_idx - 1)

        # Exploration: occasionally include a couple of later points.
        if src_idx + 1 < n and random.random() < self.exploration_late_move_prob:
            positions.append(src_idx + 1)
            positions.append(n - 1)

        unique = []
        seen = set()
        for idx in positions:
            if idx < 0 or idx >= n or idx == src_idx:
                continue
            if idx in seen:
                continue
            seen.add(idx)
            unique.append(idx)
        return unique

    def _sample_swap_positions(self, src_idx: int, n: int) -> list:
        """
        Minimal swap diversification:
        - earlier-only swaps
        - very small set to keep runtime tight
        """
        if src_idx <= 0:
            return []

        positions = []

        # Mostly earlier swaps.
        n_samples = min(src_idx, 3)
        step = max(1, src_idx // n_samples)
        positions.extend(range(0, src_idx, step))

        # Rare late swap for escape.
        if src_idx < n - 1 and random.random() < 0.08:
            positions.append(src_idx + 1)

        unique = []
        seen = set()
        for idx in positions:
            if idx < 0 or idx >= n or idx == src_idx:
                continue
            if idx in seen:
                continue
            seen.add(idx)
            unique.append(idx)
        return unique
