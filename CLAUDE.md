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
- **Permutation-based vs geometry-based neighborhoods**: `NeighborGenerator.is_permutation_based()` determines whether local search starts from `bad_solution()` (one rect per box) or `bad_permutation_solution()` (greedy-like initial packing).
- **Box coordinate system**: `(x, y)` where x is horizontal (width direction), y is vertical (length direction). `rect.width` extends along x, `rect.length` extends along y.

## Workflow

- **Progress tracking**: All open violations, bugs, and completed work are tracked in `PROGRESS.md`. **Read it at the start of every session** before doing anything else.
- **Commit regularly** in logical units with concise messages. No AI co-author tags ever.
- **Headless testing**: Use `benchmark.py` (to be built) to validate algorithms without GUI — measures CPU time, objective values, and solution correctness. This also fulfills the Section 8 benchmarking requirement.
- **Self-validation**: Run headless benchmarks to check correctness and timing rather than asking the user to run the GUI.

## Known Violations (summary — see PROGRESS.md for detail)

| ID | Issue |
|----|-------|
| V1 | `is_permutation_based()` in `NeighborGenerator` leaks problem concept into core |
| V2 | `neighbors()` and `bad_permutation_solution()` in `Problem` are LS-specific |
| V3 | Partial overlap neighborhood is a complete stub |
| V4 | Instance generator lacks separate min/max width and height |
| V5 | GUI uses green colors — must be Yellow/Blue |
| V6 | Benchmark harness (`benchmark.py`) missing entirely |
| B1 | `process_item()` mutates the original Rectangle object |
| B2 | `bad_permutation_solution()` mutates `self.rectangles` |
| B3 | `validate()` not implemented (`x=42` placeholder) |
