Solution for the "Optimierungsalgorithmen" (winter semester 2025/2026) programming assignment. The project implements generic optimization algorithms (Greedy & Local Search) and applies them to a 2D rectangle packing / bin packing problem with a simple GUI and a separate benchmarking environment.

## Collaboration
All code in this repository was created exclusively in pair programming sessions by the two authors, Gözde and Ethem.

## 1. Problem Overview
We are given
- A set of rectangles with integer side lengths
- A box size L × L, L ∈ ℕ

Rectangles must be placed openly disjoint inside boxes. For this purpose, they may be rotated by 90°. They may touch at edges/corners, but not overlap in area.

### Goal:
Place all rectangles into as few L × L boxes as possible.

This is a variant of a 2D bin packing problem and is NP-hard, so we rely on heuristics.


## 2. Implemented Algorithms
The core design goal is generic algorithm implementations: the Greedy and Local Search algorithms do not contain problem-specific logic. Instead, they communicate with the rectangle packing problem via interfaces / abstractions, so they could in principle be reused for other optimization problems.

### Greedy Algorithms
Two different selection strategies (orderings of rectangles) are implemented (). 
1. __Largest-Area First__: Sort rectangles by decreasing area.
2. __Longest-Side First__: Sort rectangles by decreasing side length.

Given an ordering, the algorithm places rectangles sequentially into boxes using a placement heuristic that maintains feasibility.

### Local Search
Three neighborhood structures are implemented:
1. __Geometry-based neighborhood__: This works directly on valid placements. It generates neighbors by moving rectangles inside the same box and between boxes.
2. __Rule-based neighborhood__: This operates on permutations of rectangles rather than placements. A given permutation is decoded by a packing procedure (similar to Greedy). Neighborhood moves perform small modifications of the permutation (e.g. swaps, shifts), especially targeting rectangles in sparse boxes.
3. __Overlap-allowing neighborhood (to be completed)__: This starts with a relaxed constraint: rectangles may overlap up to a high percentage. Over time, the maximum allowed overlap is decreased. Overlaps are penalized in the objective function. At the end, the algorithm enforces a fully overlap-free placement.


## 3. Instance Generator
A configurable instance generator creates random problem instances:
Inputs:
- number of rectangles
- box length
- lower and upper bounds for rectangle height and width

Each rectangle’s side lengths are drawn uniformly at random in the given intervals, independently for width and height.


## 4. GUI
The project includes a simple GUI that lets you:
- Generate new random instances with custom parameters
- Choose Algorithm (Greedy + Selection Strategy or Local Search + Neighborhood)
- Run algorithms multiple times on the same instance
- Visualize the resulting placements in the boxes

Changes between iterations are shown as standstill images, skipping tiny, uninteresting changes. Colors and sizes are chosen so that important elements stand out. Note that the GUI is meant for demonstration and teaching, not for pixel-perfect industrial visualization.


## 5. Benchmarking / Testing
A test environment will be implemented (to be completed).


## 6. Project Structure
At the top level the repository looks like this:

```
rect_opt-main/
├── main.py
├── core/
├── greedy/
├── local_search/
├── rec_problem/
├── requirements.txt
├── README.md
└── __init__.py
```

### Top-level files
- __main.py__ : Entry point of the application. Contains the main() function that launches the GUI. Wires together the rectangle packing problem with the Greedy and Local Search algorithms.
- __requirements.txt__ : Currently empty. The project only uses the Python standard library (including tkinter).
- __init__.py : Marks the repository root as a Python package so that modules can be imported if needed.
- __README.md__ : Project documentation (this file).

### core/ – Generic optimization framework
Contains problem-independent abstractions that make the algorithms reusable:
- __problem.py__ : abstract Problem base class defining the interface for greedy and local search.
- __solution.py__ : base class / helpers for solution objects.
- __item.py__ : generic “item” abstraction used by greedy algorithms.
- __selection_strategy.py__ : base class for selection strategies (how items are ordered for greedy).
- __neighbor_generator.py__ : base class for neighborhood generators, including helpers such as best_improving_neighbor.
- __optimization_algorithm.py__ : base class for optimization algorithms with a common solve(...) interface.

### greedy/ – Greedy algorithm
Implements the generic greedy algorithm:
- __greedy_algo.py__: takes a Problem and a SelectionStrategy, processes items in a chosen order and builds a solution step by step. Returns the sequence of intermediate solutions (used by the GUI for visualization).

### local_search/ – Local search driver
Implements the generic local search engine:
- __local_search_algo.py__: runs local search on any Problem using a NeighborGenerator. Supports settings such as maximum iterations, number of neighbors per step, first/best improvement, and time limits. Returns a trajectory of solutions for visualization in the GUI.

### rec_problem/ – Rectangle packing problem
Problem-specific implementation for the rectangle packing / bin packing task:
- __rectangle.py__ : defines rectangles (size, id, position, rotation).
- __box.py__ : represents a box of size L × L and handles placement of rectangles.
- __rectangle_packing_solution.py__ : concrete solution class storing boxes and placements.
- __rectangle_packing_problem.py__ : implements the Problem interface for this packing problem, including: random instance generation, evaluation of solutions, greedy placement, reconstruction from permutations (for rule-based neighborhoods).
- __neighborhoods/__ : geometry-based, partial-overlap, and rule-based neighbor generators for local search.
- __strategies/__ : greedy selection strategies such as “largest area first” and “longest side first`.


## 7. Usage
Right now the project is GUI-driven. There is no separate CLI/benchmark script yet; both Greedy and Local Search algorithms are controlled via the GUI in main.py.

### Prerequisites
The project uses only the standard library (no external pip dependencies).
- Python 3.10+
- Tkinter

### Start the GUI
From the repository root:
```
python main.py
```
This opens the rectangle packing GUI window.

### Working with the GUI
Once the GUI is open, the main workflow is:
1. __Set problem parameters (top control bar)__: box length, rectangle count, rect size min/max. These values are passed directly to RectanglePackingProblem(box_length, rect_number, rect_min_size, rect_max_size).
2. __Choose the algorithm family__: Greedy or Local Search
3. __Choose the specific strategy / neighborhood__: (For Greedy: Largest-Area-First or Longest-Side-First, For Local Search: Geometry-Based or Partial Overlap or Rule-Based)
4. __Run the Algorithm by clicking "Start"__. Internally, this instantiates the appropriate Problem, GreedyAlgo or LocalSearchAlgo.
5. __Inspect solutions__: A separate window shows the packing. Use the slider / step bar at the bottom to scroll through the sequence of solutions and observe how the number of boxes changes over time.


## 8. License
All rights reserved.

This project is submitted as part of the course "Optimierungsalgorithmen".
This code is provided for viewing and educational purposes only. Any other use, including copying, modifying, distributing, or using the code for any purpose, is strictly prohibited without prior written permission from the authors.

