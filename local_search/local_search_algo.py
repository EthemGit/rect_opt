# local_search/local_search_algo.py
from core.optimization_algorithm import OptimizationAlgo

class LocalSearchAlgo(OptimizationAlgo):
    """
    Problem-agnostic Local Search.
    - neighbor_generator: an instance of core.neighbor_generator.NeighborGenerator
    - max_iters: safety cap
    - stride: how often to append intermediate solutions for the GUI
    - first_improvement: whether to accept first improving neighbor (fast) or best (slower)
    """

    def __init__(self, neighbor_generator, max_iters: int = 1000, stride: int = 1, first_improvement: bool = True, max_neighbors_per_step: int = None):
        self.neighbor_generator = neighbor_generator
        self.max_iters = int(max_iters)
        self.stride = int(stride)
        self.first_improvement = bool(first_improvement)
        self.max_neighbors_per_step = max_neighbors_per_step


    def solve(self, problem):
        """
        Starts with a bad solution provided by problem.bad_solution() and iteratively
        asks the neighbor generator for improving neighbors until no improvement
        is possible or max_iters is reached.
        Returns a list of solutions (for GUI / step visualization).
        """
        sol = problem.bad_solution()
        sols = [sol]
        it = 0
        while it < self.max_iters:
            improved = self.neighbor_generator.best_improving_neighbor(
                problem, sol,
                first_improvement=self.first_improvement,
                max_neighbors=self.max_neighbors_per_step
            )
            if improved is None:
                break

            # record depending on stride or when a new box count was achieved
            if it % self.stride == 0 or len(improved.boxes) != len(sol.boxes):
                sols.append(improved)

            sol = improved
            it += 1

        # ensure final solution included
        if sols[-1] is not sol:
            sols.append(sol)
        return sols
