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

### V4 — Instance generator: missing separate width/height bounds `[  ]`
**Where:** `rec_problem/rectangle_packing_problem.py:32-38`, `main.py:147-153`
**Problem:** Generator takes a single `rect_min_size`/`rect_max_size` pair. Requirements Section 4 explicitly require separate `min_width, max_width, min_height, max_height`.
**Fix:** Add four parameters to `RectanglePackingProblem.__init__()` and update the GUI spinboxes.

### V5 — GUI colors: Green used instead of Yellow/Blue `[  ]`
**Where:** `main.py:37-38`
**Problem:** `color_new = "#0a7d24"` (dark green) and `color_old = "#b8e6b8"` (light green). Requirements Section 7 explicitly mandate Yellow/Blue for accessibility.
**Fix:** Replace with Yellow (`#f5c400` or similar) for new rects and Blue (`#1a73e8` or similar) for old rects (or swap — just must be Yellow/Blue, not Red/Green).

### V6 — Benchmarking harness missing `[  ]`
**Where:** Nowhere — `benchmark.py` does not exist.
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

### B3 — `validate()` not implemented `[  ]`
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

### P1 — 1000 rectangles within 10 seconds target `[  ]`
**Status:** UNTESTED — no benchmark harness yet. After V6 is done, run verification mode.
**Risk areas:**
- `process_item()` and `construct_from_order()` iterate all L² cells per box per rectangle → O(n × b × L²).
- `Box.empty_coordinates` starts as a full set of L² cells — for large L this is expensive to copy.
- `clone()` does `copy.deepcopy(self.boxes)` — deep copy of all boxes each greedy step (only needed for the GUI step list).

---

## COMPLETED

### C1 — Dead code in `neighbor_generator.py` removed `[ ]`
*(pending — currently still present, see M1)*

---

## Fix Priority Order

| # | ID | Reason |
|---|---|---|
| 1 | V1+V2 | Core architecture — examiner checks this first; easiest to fail on |
| 2 | B1+B2 | Silent correctness bugs that affect all algorithms |
| 3 | V4 | Instance generator fix is small and unblocks benchmark |
| 4 | V6 | Benchmark harness — needed to prove performance and validate correctness |
| 5 | P1 | Run benchmark; tune if needed |
| 6 | V3 | Partial overlap neighborhood — most complex to implement |
| 7 | V5 | GUI colors — cosmetic but explicitly required |
| 8 | B3 | Validate() — needed for benchmark correctness checking |
| 9 | M1+M2 | Cleanup |
