# local_search/local_search_algo.py
from core.optimization_algorithm import OptimizationAlgo

"""
Explanation of the different limits involved in using the Local Search Algo:

    1. max_neighbors (on GeometryBasedNeighborhood)
        Meaning: max number of neighbors that a single call to generate_neighbors() will ever yield
        Example: if there are theoretically 20.000 moves for a rect, but max_neighbors=500, it stops at 500 moves
        Effect: limits how many moves we consider
        Good value: 200-600 for speed. up to 5.000 when not time-constrained

    2. max_iters (on LocalSearchAlgo)
        Meaning: maximum number of iterations the local search will run
            each iteration: generate neighbors → pick one (first/best improvement) → move → update current solution
        Effect: limits the length of the search.
        When to tweak:
            If the search runs out of iterations before time runs out, raise it.
            If the search runs too long, lower it.
        Usually you keep this high and let time be the limiting factor.
    
    3. First_improvement
        A strategy flag.
            If True, stop scanning neighbors as soon as we find a better solution.
            If False, evaluate all neighbors and pick best.
        Always keep True, except for testing purposes when not time-constrained.

    4. max_neighbors_per_step (on LocalSearchAlgo)
        Meaning: even if neighborhood generator could yield more, cut off after this many per iteration.
        Effect: prevents exploding runtime at huge neighborhoods
        Good value: 200-600
    -----------------------
    Which to tune for quality/speed:

        max_neighbors: tune this per-neighborhood. Lower → faster but fewer options.
        max_iters: keep large (e.g. 20,000+) so it’s not the limiting factor; runtime will cap it anyway.
        first_improvement: almost always True for big instances.
        max_neighbors_per_step: use as a runtime safeguard (e.g. 500).

    -----------------------
    Example:
        For 1000 rects in ≤10s:
            max_neighbors=300–500
            max_iters=20_000 (doesn’t hurt, will just stop on time)
            first_improvement=True
            max_neighbors_per_step=500

        This way:
            Each iteration scans at most ~500 moves.
            Stops at the first improvement, so most iterations are cheap.
            With 10 seconds, you’ll get many thousands of iterations.
            You won’t waste time exploring millions of low-value neighbors.
"""

class LocalSearchAlgo(OptimizationAlgo):
    """
    Problem-agnostic Local Search.
    - neighbor_generator: an instance of core.neighbor_generator.NeighborGenerator
    - max_iters: safety cap
    - stride: how often to append intermediate solutions for the GUI
    - first_improvement: whether to accept first improving neighbor (fast) or best (slower)
    """

    def __init__(self, neighbor_generator, max_iters: int = 1000, stride: int = 1, first_improvement: bool = True, max_neighbors_per_step: int = None, time_limit_seconds: float = 0.0):
        self.neighbor_generator = neighbor_generator
        self.max_iters = int(max_iters)
        self.stride = int(stride)
        self.first_improvement = bool(first_improvement)
        self.max_neighbors_per_step = max_neighbors_per_step
        self.time_limit_seconds = time_limit_seconds


    def solve(self, problem):
        """
        Starts with the initial solution provided by the neighbor generator and iteratively
        asks the neighbor generator for improving neighbors until no improvement
        is possible or max_iters is reached.
        Returns a list of solutions (for GUI / step visualization).
        """
        import time
        start_time = time.time()

        sol = self.neighbor_generator.initial_solution(problem)
        sols = [sol]
        it = 0
        improvements_since_last_record = 0
        while it < self.max_iters:
            if self.time_limit_seconds and (time.time() - start_time) > self.time_limit_seconds:
                break
            improved = self.neighbor_generator.best_improving_neighbor(
                problem, sol,
                first_improvement=self.first_improvement,
                max_neighbors=self.max_neighbors_per_step
            )
            if improved is None:
                break

            if problem.evaluate(improved) < problem.evaluate(sol):
                improvements_since_last_record += 1
                if improvements_since_last_record >= self.stride:
                    sols.append(improved)
                    improvements_since_last_record = 0

            sol = improved
            it += 1

        # ensure final solution included
        if sols[-1] is not sol:
            sols.append(sol)
        return sols
