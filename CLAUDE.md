# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A rectangle bin-packing optimizer with a Tkinter GUI. Users generate random rectangles, choose an algorithm (Greedy or Local Search) with a strategy/neighborhood, then step through intermediate solutions visually. Full requirements are in `optalgos_project_requirements.md`.

## Running

```bash
python main.py
```

No external dependencies beyond Python 3.10+ standard library. No build system.

## Critical Project Rules (from requirements)

1. **Generic architecture is mandatory for passing.** Algorithm implementations (`core/`) must contain ZERO problem-specific code. The problem (`rec_problem/`) must contain ZERO algorithm-specific code. Everything connects through interfaces/abstract classes.
2. **Performance target:** Every algorithm must handle **1000 rectangles within 10 seconds** on a standard notebook. Solutions must look visually optimal.
3. **GUI accessibility:** Use **Yellow/Blue** instead of Red/Green for color distinctions (color blindness). Important elements drawn large/thick in strong colors, unimportant elements pale/gray.
4. **Local Search must start from deliberately bad initial solutions** to demonstrate convincing improvements.
5. **Test environment (benchmarking)** must be separate from GUI — takes tuples of (num_instances, num_rects, min/max side lengths, box_length), runs all algorithms, logs objective values and CPU thread time. Needs demo mode (small, fast) and verification mode (large, thorough).
6. **Instance generator** should support separate min/max for both side lengths (the requirements specify min_width, max_width, min_height, max_height — currently only one min/max pair is implemented).

## Architecture

The codebase uses a **generic core / concrete problem** split:

### Core layer (`core/`) — problem-agnostic abstractions

- `Problem[S, I]` — abstract problem defining `empty_solution()`, `items_for_greedy()`, `process_item()`, `bad_solution()`, `evaluate()`, etc.
- `Solution` — abstract with `validate()`, `get_objective_value()`, `clone()`
- `OptimizationAlgo[S]` — abstract algorithm with `solve(problem) -> List[S]` (returns list of intermediate solutions for GUI stepping)
- `SelectionStrategy` — abstract greedy ordering with `order(items)`
- `NeighborGenerator` — abstract local search neighborhood with `generate_neighbors(problem, solution)` and a default `best_improving_neighbor()` helper
- `Item` — empty marker base class for Rectangle and Box

### Rectangle packing layer (`rec_problem/`) — concrete implementations

- `RectanglePackingProblem` — generates random rectangles, implements all `Problem` methods including `construct_from_order()` for permutation-based neighborhoods
- `RectanglePackingSolution` — holds `boxes: List[Box]`, `box_length`, `rectangles`, and `permutation` (list of rect IDs). Has both `clone()` (deep copy) and `clone_partial(src, tgt)` (only clones two boxes, shares rest — performance optimization for local search)
- `Rectangle` — dataclass with `id`, `length`, `width`; hashed/compared by `id`
- `Box` — tracks placed rects via `my_rects: Dict[Rectangle, (x,y)]` and `empty_coordinates: Set` (all unoccupied grid cells). Provides `insert_rect()`, `remove_rect()`, `rect_fits_here()`, `get_anchor_positions()`

### Algorithms

- `greedy/greedy_algo.py` — `GreedyAlgo`: iterates items in strategy-defined order, calls `problem.process_item()` per rectangle
- `local_search/local_search_algo.py` — `LocalSearchAlgo`: starts from a bad solution, repeatedly calls `neighbor_generator.best_improving_neighbor()`. Supports first-improvement vs best-improvement mode

### Neighborhoods (`rec_problem/neighborhoods/`)

- `geometry_based_neighbor.py` — moves single rects to anchor positions in other boxes; uses `clone_partial()` for speed
- `partial_overlap_neighbor.py` — allows partial overlaps during search
- `rule_based_neighbor.py` — permutation-based; swaps rect IDs in the permutation then rebuilds via `problem.construct_from_order()`

### Greedy strategies (`rec_problem/strategies/`)

- `strat_largest_area_first.py` — sorts rectangles by area descending
- `strat_longest_side_first.py` — sorts by longest side descending

### GUI (`main.py`)

- `PackingGUI` — Tkinter app. Main window has controls + rectangle table (left) and algorithm/strategy chooser (right). Solutions render in a pop-up `Toplevel` window with prev/next navigation, step slider, and zoom.

## Key Design Patterns

- **`solve()` returns `List[Solution]`**: Every algorithm returns a list of intermediate solutions so the GUI can animate progress step-by-step.
- **Objective = `len(sol.boxes)`**: Minimizing the number of boxes used. `evaluate()` returns box count.
- **`is_better_solution()`** uses a tiebreaker beyond box count: prefers solutions with fewer boxes containing < N rects (consolidation heuristic).
- **`no_improve_limit` in `LocalSearchAlgo`**: For stochastic neighborhoods (Rule-Based uses random candidate sampling), a single `None` return from `best_improving_neighbor` does not mean a true local optimum — just that this random sample found nothing. `no_improve_limit` (default 1, set to 15 for Rule-Based in GUI) controls how many consecutive `None` returns are tolerated before the loop terminates. Deterministic neighborhoods keep the default (1).
- **Box coordinate system**: `(x, y)` where x is horizontal (width direction), y is vertical (length direction). `rect.width` extends along x, `rect.length` extends along y.

## Workflow

- **Progress tracking**: All open violations, bugs, and completed work are tracked in `PROGRESS.md`. **Read it at the start of every session** before doing anything else.
- **Commit when I tell you to.** Use concise commit messages. No AI co-author tags ever.
- When i report a bug, do not start by trying to fix it. Instead, start by writing a test that reproduces the bug. Then, have subagents try to fix the bug and prove it with a passing test.
- **Headless testing**: Use `benchmark.py` to validate algorithms without GUI — measures CPU time, objective values, and solution correctness.
- **Self-validation workflow (mandatory):**
  1. Before fixing any issue, write a small throwaway Python script (temp file in project root) that **proves the bug exists** via printed output.
  2. Apply the fix.
  3. Re-run (or extend) the same script to **prove the fix works**.
  4. Delete the temp file.
  - Use only `print()` and `sys.path.insert(0, '.')` — no test frameworks needed.
  - Avoid Unicode in print strings on Windows (use ASCII only — no arrows, checkmarks, etc.).
  - Never ask the user to run the GUI to verify correctness; self-validate headlessly instead.

## Known Violations (summary — see PROGRESS.md for detail)

| ID | Status | Issue                                                                          |
| -- | ------ | ------------------------------------------------------------------------------ |
| V1 | done   | `is_permutation_based()` leaked problem concept into core                      |
| V2 | done   | `neighbors()` and `bad_permutation_solution()` were LS-specific in `Problem`  |
| V3 | open   | Partial overlap neighborhood is a complete stub                                |
| V4 | done   | Instance generator lacked separate min/max width and height                    |
| V5 | open   | GUI uses green colors — must be Yellow/Blue                                   |
| V6 | done   | Benchmark harness (`benchmark.py`) was missing                                |
| B1 | done   | `process_item()` mutated the original Rectangle object                        |
| B2 | done   | `bad_permutation_solution()` mutated `self.rectangles`                        |
| B3 | done   | `validate()` not implemented                                                  |
| B4 | done   | Rule-Based LS terminated after 0–6 steps due to permanent break on `None`     |
| P2 | open   | Rule-Based LS quality collapses for 1000 rects (118 vs 96 boxes from Greedy)  |
