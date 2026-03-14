# Optimization Algorithms (OptAlgos) - Project Requirements

## 1. Project Overview

This project involves implementing optimization algorithms to solve a specific 2D bin-packing-like problem. The primary focus is on a strictly **generic software architecture**, visual representation (GUI), and performance tuning.

* **Allowed Languages:** Java, C, C++, C#, Python, Scala.
* **Core Algorithms to Implement:**
  1. Local Search (must start from decidedly *bad* initial solutions to demonstrate convincing improvements).
  2. Greedy Algorithm.

## 2. STRICT REQUIREMENT: Generic Architecture

**This is crucial for passing the assignment:** The algorithms must be implemented in a completely generic way.

* **Separation of Concerns:** The algorithm implementations must NOT contain any problem-specific information, nor any specific neighborhood definitions or selection strategies.
* **Interchangeability:** The algorithms must work out-of-the-box if applied to a completely different, unforeseen optimization problem.
* **No Algorithm Logic in Problem:** The implementation of the optimization problem must not contain anything specific to the algorithms, neighborhoods, or selection strategies.
* **Implementation Strategy:** Use Polymorphism (Interfaces) or Generics/Templates (e.g., C++, Java). The details of the problem and neighborhoods must be hidden behind interfaces.

## 3. Algorithmic Problem Formulation

* **Input:** A finite set of rectangles with integer side lengths, and an integer box length $L$. (No rectangle side will be larger than $L$).
* **Placement Rules:**
  * Rectangles must be placed axis-parallel in the plane.
  * Rectangles must be *open disjoint* (they may share corners and edge segments, but no inner points / no overlaps).
  * Rectangles can be rotated by 90 degrees.
  * Every rectangle must be placed completely inside a square of length $L$ (called a "Box").
* **Objective:** Minimize the total number of Boxes needed to place all rectangles.

## 4. Instance Generator

Create a generator that takes the following inputs:

* Box length $L$
* Number of rectangles to generate
* Upper and lower bounds for *both* side lengths (e.g., min_width, max_width, min_height, max_height).
* **Behavior:** Generates rectangles with uniformly distributed random side lengths within the given intervals. All random decisions must be stochastically independent.

## 5. Local Search & Neighborhoods

Implement the following three distinct neighborhood structures:

1. **Geometry-based:** Directly shift rectangles within a box or between different boxes.
   * *Heuristic tweak allowed:* You can alter the objective function to reward moves that don't strictly decrease the box count but bring the system closer to an improvement (e.g., rewarding the removal of rectangles from already sparsely populated boxes).
2. **Rule-based:** Instead of working on valid 2D placements, the Local Search operates on *permutations* of the rectangles.
   * The placement is then done deterministically by inserting rectangles into boxes according to the permutation order (similar to a greedy approach).
   * The neighborhood is defined by small modification steps on the permutation array itself.
3. **Partial Overlaps Allowed:** Adapt the geometry-based neighborhood.
   * Rectangles are allowed to overlap based on a percentage.
   * *Formula:* Overlap = (Shared Area) / max(Area_Rect1, Area_Rect2).
   * *Progression:* Starts at 100% allowed (making optimal solutions easy to find), reduces over time.
   * Violations are heavily penalized in the objective function. Must guarantee a 100% overlap-free valid solution at the very end.

## 6. Greedy Algorithm Strategies

* Formulate and implement **two fundamentally different selection strategies** (the order in which rectangles are picked for placement).
* Implement the logic for how exactly a picked rectangle is placed open-disjointly among already placed rectangles.

## 7. GUI and Visualization Rules

Implement a simple GUI to repeatedly generate instances and visualize the algorithm's progress.

* **User Controls:** Set number of rectangles, min/max side lengths, box length $L$, pick algorithm, pick neighborhood/strategy.
* **Animation / Stepping:**
  * Show placements between iterations as still frames.
  * Skip intermediate steps automatically to avoid overwhelming the viewer with rapid, microscopic changes. The transition between frames must be insightful.
* **Strict Visual Design Guidelines:**
  * **Size & Clarity:** Placements must be large and clearly arranged. Avoid overlapping UI information.
  * **Focus:** Important elements must be drawn larger/thicker and in strong colors. Draw them *last* (z-index) so they aren't covered. Unimportant elements should be pale, ideally neutral light gray.
  * **Contrast:** Use high contrast to distinguish elements. Use low contrast (monochromatic or bichromatic gradients) for continuous data. Use two colors and a neutral zero-color for positive/negative scales.
  * **Accessibility:** Account for color blindness (especially Red/Green). **Use Yellow/Blue** instead, as they have different brightness levels in RGB.
  * **UX:** Design the UI so an examiner who has never seen it can instantly understand it. Small details must be unmistakable.

## 8. Test Environment (Benchmarking)

Write an independent test environment (separate from the GUI).

* **Parameters:** A sequence of tuples: `(Number of Instances, Number of Rectangles, min side length 1, min side length 2, max side length 1, max side length 2, Box length L)`.
* **Behavior:** Generates the specified amount of instances per tuple. Applies each algorithm to each instance.
* **Logging:** Record the achieved objective values and the exact runtime (**CPU thread time**).
* **Execution Modes:**
  1. *Demo Mode:* Small/few instances, completes in a few minutes for live presentation.
  2. *Verification Mode:* Large/many instances for rigorous correctness testing (outputs a protocol log).

## 9. Performance & Tuning Target

* The "pure" algorithms from lectures will be too slow. You MUST optimize/tune them.
* *Example tuning:* Don't evaluate the entire neighborhood; use heuristics to evaluate only the most promising neighbors.
* **Ultimate Goal:** Every algorithm must be able to process instances of up to **1000 rectangles within 10 seconds** on a standard notebook. The resulting solution must be visually optimal ("cannot be improved by the naked eye").
