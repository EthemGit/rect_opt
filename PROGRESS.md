# Project Progress & Requirements Audit

Track open violations, bugs, and completed work across sessions.

---

## Status Legend
- `[ ]` — open / not started
- `[~]` — in progress
- `[x]` — done

---

## VIOLATIONS (must fix to pass)

### V1 — Generic architecture: `is_permutation_based()` leaks problem concept into core `[x]`
**Where:** `core/neighbor_generator.py:23`, `local_search/local_search_algo.py:79`
**Problem:** `LocalSearchAlgo.solve()` calls `neighbor_generator.is_permutation_based()` to choose between `bad_solution()` and `bad_permutation_solution()`. Permutations are a rectangle-packing concept — the generic algorithm layer must not know about them.
**Fix:** Add `initial_solution(problem)` to `NeighborGenerator`. Each concrete neighborhood returns whatever starting solution it needs. `LocalSearchAlgo` just calls `neighbor_generator.initial_solution(problem)`. Remove `is_permutation_based()` entirely.

### V2 — Generic architecture: `neighbors()`, `bad_solution()`, and `bad_permutation_solution()` in `Problem` `[x]`
**Where:** `core/problem.py:39,35`
**Problem:** `neighbors()` is a local-search concept (algorithm-specific) inside the generic `Problem` interface. `bad_permutation_solution()` is also LS-neighborhood-specific in Problem.
**Fix:** Remove `neighbors()` from `Problem` (it's never called anyway — local search goes through `NeighborGenerator`). Move `bad_permutation_solution()` logic into `RuleBasedNeighborhood.initial_solution()`.

### V3 — Partial overlap neighborhood is a stub `[  ]`
**Where:** `rec_problem/neighborhoods/partial_overlap_neighbor.py`
**Problem:** `generate_neighbors()` is just `pass`. Not implemented at all.
**Requirements (Section 5.3):**
- Rectangles may overlap up to a percentage threshold that starts at 100% and decreases over iterations.
- Overlap formula: `(shared area) / max(area_rect1, area_rect2)`.
- Violations are heavily penalized in the objective function.
- Must guarantee a 100% overlap-free valid solution at the end.

### V4 — Instance generator: missing separate width/height bounds `[x]`
**Where:** `rec_problem/rectangle_packing_problem.py:32-38`, `main.py:147-153`
**Problem:** Generator takes a single `rect_min_size`/`rect_max_size` pair. Requirements Section 4 explicitly require separate `min_width, max_width, min_height, max_height`.
**Fix:** Add four parameters to `RectanglePackingProblem.__init__()` and update the GUI spinboxes.

### V5 — GUI colors: Green used instead of Yellow/Blue `[  ]`
**Where:** `main.py:37-38`
**Problem:** `color_new = "#0a7d24"` (dark green) and `color_old = "#b8e6b8"` (light green). Requirements Section 7 explicitly mandate Yellow/Blue for accessibility.
**Fix:** Replace with Yellow (`#f5c400` or similar) for new rects and Blue (`#1a73e8` or similar) for old rects (or swap — just must be Yellow/Blue, not Red/Green).

### V6 — Benchmarking harness missing `[x]`
**Where:** `benchmark.py` (new file).
**Problem:** Section 8 requires a standalone test environment (separate from GUI) that:
- Takes a sequence of tuples `(num_instances, num_rects, min_w, max_w, min_h, max_h, box_length)`.
- Runs all algorithms on each instance.
- Logs objective values and CPU thread time.
- Has a **Demo mode** (small/fast, for live presentation) and **Verification mode** (large/thorough, produces protocol log).

---

## BUGS

### B1 — `process_item()` mutates the original Rectangle `[x]`
**Where:** `rec_problem/rectangle_packing_problem.py:106`
**Problem:** `item.width, item.length = new_width, new_length` modifies the passed-in Rectangle in place. Since `items_for_greedy()` returns `self.rectangles` (the canonical list), this corrupts the problem's rectangle data for all future calls.
**Fix:** Create a rotated copy (`item_rot` already exists) instead of mutating `item`.

### B2 — `bad_permutation_solution()` mutates `self.rectangles` `[x]`
**Where:** `rec_problem/rectangle_packing_problem.py:130`
**Problem:** `self.rectangles = sorted(self.rectangles, ...)` permanently reorders the problem's rectangle list.
**Fix:** Sort a local copy: `rects = sorted(self.rectangles, ...)`.

### B3 — `validate()` not implemented `[x]`
**Where:** `rec_problem/rectangle_packing_solution.py:26-40`
**Problem:** Body is `x=42` — no validation logic. Should check: all rects inside box bounds, no illegal overlaps beyond `permitted_error`.

---

## MINOR / CLEANUP

### M1 — Dead code in `neighbor_generator.py` `[  ]`
**Where:** `core/neighbor_generator.py:54-66`
**Problem:** Lines after `return best` on line 52 are unreachable (leftover from a previous version).

### M2 — String literal used as comment in `rectangle_packing_problem.py` `[  ]`
**Where:** `rec_problem/rectangle_packing_problem.py:179-185`
**Problem:** A multi-line string literal is used as a block comment inside `is_better_solution()`. Should be a proper `#` comment or just deleted.

---

## PERFORMANCE

### P1 — 1000 rectangles within 10 seconds target `[x]`
**Status:** Satisfied on user's notebook (Greedy ~2s for 1000 rects).
**Fixes applied:**
- `Box.get_anchor_positions()`: O(L²) position scan → O(k) anchor scan in `process_item()`, `construct_from_order()`, and `geometry_based_neighbor`.
- `Box.clone()`: replaced `Box(L)` init (creates L² tuples) with `Box.__new__(Box)`.
- `RectanglePackingSolution.clone()`: replaced `copy.deepcopy(boxes)` with `[b.clone() for b in self.boxes]`.

### P2 — Rule-Based LS quality for large instances `[  ]`
**Status:** Open — known limitation, not yet addressed.
**Problem:** For 1000 rects, Rule-Based LS starts at 118 boxes and cannot reduce the count at all (Greedy achieves 96). Root cause: `construct_from_order(1000 rects)` costs ~5-10ms per call; with `time_budget_per_call_seconds=1.5` only ~150 neighbours are evaluated per iteration — far too few to reliably find a move that eliminates a full box. Single permutation swaps create unpredictable cascade effects and the composite-score gradient is very flat for large instances.
**Investigation method:** write a temp script that compares Greedy boxes vs LS boxes for the same seed; confirmed via test on 2026-03-24.
**Potential fixes (not yet applied):**
- Target sparse-box rects more aggressively and try all positions (not a sparse sample).
- Reduce `time_budget_per_call_seconds` to allow more iterations instead of deeper per-call search.
- Multi-element moves: move all rects from the sparsest box earlier in the permutation at once.

---

## BUGS (behaviour)

### B4 — Rule-Based LS terminates after 0–6 steps (stochastic sampling + permanent break) `[x]`
**Where:** `local_search/local_search_algo.py`, `main.py`
**Problem:** `LocalSearchAlgo.solve()` called `break` permanently the first time `best_improving_neighbor` returned `None`. `RuleBasedNeighborhood.generate_neighbors()` samples candidates and insert positions randomly, so `None` means "nothing found in *this* sample", not "true local optimum". Verified: 15/20 retries on the "stuck" final solution found improvements.
**Fix:** Added `no_improve_limit: int = 1` parameter to `LocalSearchAlgo`. The loop now retries up to N times (with different random samples) before breaking. Set to `no_improve_limit=15` for Rule-Based in `main.py`. Deterministic neighborhoods keep the default (1) so behaviour is unchanged.
**Effect:** Accepted improvement steps for 80 rects: 25 → 33; GUI visible steps (stride=5): 6 → 9; full 20s time budget now used.

---

## COMPLETED

### C1 — Dead code in `neighbor_generator.py` removed `[ ]`
*(pending — currently still present, see M1)*

---

## Fix Priority Order

| # | ID | Reason |
|---|---|---|
| 1 | ~~V1+V2~~ | **done** — generic architecture violations removed |
| 2 | ~~B1+B2~~ | **done** — mutation bugs fixed |
| 3 | ~~V4~~ | **done** — 4 separate width/height params in problem + GUI |
| 4 | ~~V6~~ | **done** — `benchmark.py` with demo + verify mode |
| 5 | ~~P1~~ | **done** — Greedy ≤10s for 1000 rects confirmed |
| 6 | ~~B3~~ | **done** — `validate()` implemented with bounds + overlap check |
| 7 | ~~B4~~ | **done** — Rule-Based LS premature termination fixed (`no_improve_limit`) |
| 8 | V3 | Partial overlap neighborhood — most complex to implement |
| 9 | V5 | GUI colors — cosmetic but explicitly required |
| 10 | P2 | Rule-Based quality for 1000 rects — neighbourhood too weak |
| 11 | M1+M2 | Cleanup |
