"""
Test: Partial Overlap Neighborhood — Quality Regression
=======================================================
Reproduces the bug reported 2026-03-16:
  box_length=10, 100 rects, min_size=1, max_size=5 yields a poor final
  solution (12 boxes) with straggler boxes containing only 1–2 rectangles.

Expected correct behavior:
  1. The final solution must be OVERLAP-FREE (allowed_overlap decays to 0).
  2. No box in the final solution may contain exactly 1 rectangle, because
     a single rectangle can always be consolidated into another box that has
     free capacity (the penalty for opening a new box is 1.0, which dominates
     any small overlap penalty).
  3. Box count should be at most ceil(total_rect_area / box_area) + 2,
     i.e. close to the theoretical minimum.

Run:
    python -m pytest tests/test_partial_overlap_quality.py -v
or:
    python tests/test_partial_overlap_quality.py
"""

import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rec_problem.rectangle_packing_problem import RectanglePackingProblem
from rec_problem.neighborhoods.partial_overlap_neighbor import (
    PartialOverlapNeighborhood,
    OverlapBox,
)
from local_search.local_search_algo import LocalSearchAlgo


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _has_overlap(box) -> bool:
    """Return True if any two rectangles in the box share area."""
    rects = list(box.my_rects.items())
    for i, (r1, (x1, y1)) in enumerate(rects):
        for r2, (x2, y2) in rects[i + 1 :]:
            ix0 = max(x1, x2)
            ix1 = min(x1 + r1.width, x2 + r2.width)
            iy0 = max(y1, y2)
            iy1 = min(y1 + r1.length, y2 + r2.length)
            if ix0 < ix1 and iy0 < iy1:
                return True
    return False


def _solution_has_overlaps(sol) -> list:
    """Return list of (box_idx, rect_ids) for every box that still has overlaps."""
    bad = []
    for i, box in enumerate(sol.boxes):
        if _has_overlap(box):
            ids = [r.id for r in box.my_rects]
            bad.append((i, ids))
    return bad


def _straggler_boxes(sol, max_rects: int = 1) -> list:
    """Return indices of boxes that contain ≤ max_rects rectangles."""
    return [i for i, b in enumerate(sol.boxes) if len(b.my_rects) <= max_rects]


def _theoretical_min_boxes(problem) -> int:
    """ceil(total rect area / box area)."""
    import math
    total = sum(r.width * r.length for r in problem.rectangles)
    return math.ceil(total / (problem.box_length ** 2))


# ---------------------------------------------------------------------------
# Test parameters — identical to the GUI run that exposed the bug
# ---------------------------------------------------------------------------

BOX_LENGTH = 10
NUM_RECTS = 100
MIN_SIZE = 1
MAX_SIZE = 5
SEED = 0           # seed=0 consistently reproduces stragglers (9/10 seeds affected)
MAX_ITERS = 2000
TIME_LIMIT = 9.0   # seconds (same as GUI)


def build_and_run(seed=SEED, time_limit=TIME_LIMIT):
    random.seed(seed)
    problem = RectanglePackingProblem(
        box_length=BOX_LENGTH,
        rect_number=NUM_RECTS,
        rect_min_size=MIN_SIZE,
        rect_max_size=MAX_SIZE,
    )
    ng = PartialOverlapNeighborhood(max_neighbors=500)
    algo = LocalSearchAlgo(
        ng,
        max_iters=MAX_ITERS,
        stride=1,
        first_improvement=True,
        max_neighbors_per_step=2000,
        time_limit_seconds=time_limit,
    )
    solutions = algo.solve(problem)
    final = solutions[-1]
    return problem, final, ng


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_final_solution_is_overlap_free():
    """
    The allowed_overlap parameter decays to 0 during search.
    Therefore the final solution must contain zero overlapping pairs.
    """
    problem, final, ng = build_and_run()
    bad_boxes = _solution_has_overlaps(final)
    assert bad_boxes == [], (
        f"Final solution still contains overlaps in {len(bad_boxes)} box(es): "
        f"{bad_boxes[:3]}…  allowed_overlap at termination = {ng.allowed_overlap}"
    )


def test_no_single_rect_straggler_boxes():
    """
    A box containing exactly 1 rectangle is a 'straggler'.
    The algorithm's box-elimination incentive (box_delta = -1.0) is strong
    enough that stragglers should always be consolidated into an existing box.

    This test reproduces the reported bug: the screenshot shows Box 8 with
    just one 1×4 rectangle that was never merged into another box.
    """
    problem, final, ng = build_and_run()
    stragglers = _straggler_boxes(final, max_rects=1)
    assert stragglers == [], (
        f"Final solution has {len(stragglers)} straggler box(es) with exactly 1 rect "
        f"(box indices: {stragglers}).  Total boxes: {len(final.boxes)}.  "
        f"allowed_overlap at termination: {ng.allowed_overlap}"
    )


def test_box_count_near_theoretical_minimum():
    """
    The final box count should be at most theoretical_minimum + 3.
    For 100 rects of sizes 1-5 in a 10×10 box the theoretical min is
    typically 8-10; the algorithm should reach within 3 of that.
    """
    problem, final, ng = build_and_run()
    theory_min = _theoretical_min_boxes(problem)
    max_acceptable = theory_min + 3
    actual = len(final.boxes)
    assert actual <= max_acceptable, (
        f"Box count {actual} is too far from theoretical minimum {theory_min}. "
        f"Max acceptable: {max_acceptable}.  "
        f"allowed_overlap at termination: {ng.allowed_overlap}"
    )


def test_allowed_overlap_reaches_zero():
    """
    The search must tighten allowed_overlap all the way to 0.0 before it can
    terminate with `None`.  If it terminates early the solution may still
    contain overlapping rectangles, which would be invalid.
    """
    problem, final, ng = build_and_run()
    assert ng.allowed_overlap == 0.0, (
        f"Algorithm terminated with allowed_overlap = {ng.allowed_overlap} > 0.  "
        f"The search ended before overlaps were fully eliminated."
    )


# ---------------------------------------------------------------------------
# Manual runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import time

    print(f"Running with seed={SEED}, {NUM_RECTS} rects, "
          f"box_length={BOX_LENGTH}, sizes {MIN_SIZE}–{MAX_SIZE}\n")

    t0 = time.time()
    problem, final, ng = build_and_run()
    elapsed = time.time() - t0

    theory = _theoretical_min_boxes(problem)
    print(f"Elapsed     : {elapsed:.1f}s")
    print(f"Final boxes : {len(final.boxes)}  (theory min ~ {theory})")
    print(f"allowed_overlap at end: {ng.allowed_overlap}")

    bad = _solution_has_overlaps(final)
    print(f"Boxes with overlaps   : {len(bad)}")

    stragglers = _straggler_boxes(final, max_rects=1)
    print(f"Single-rect stragglers: {len(stragglers)}  (indices: {stragglers})")

    two_rect = _straggler_boxes(final, max_rects=2)
    print(f"<=2-rect boxes        : {len(two_rect)}  (indices: {two_rect})")

    print()
    print("Box sizes:", sorted([len(b.my_rects) for b in final.boxes], reverse=True))

    print()
    failures = []
    for name, fn in [
        ("overlap-free", test_final_solution_is_overlap_free),
        ("no stragglers", test_no_single_rect_straggler_boxes),
        ("box count",     test_box_count_near_theoretical_minimum),
        ("overlap->0",    test_allowed_overlap_reaches_zero),
    ]:
        try:
            fn()
            print(f"  PASS  {name}")
        except AssertionError as e:
            print(f"  FAIL  {name}: {e}")
            failures.append(name)

    sys.exit(1 if failures else 0)
