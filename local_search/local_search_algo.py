# implements optimization_algorithm
# calls neighbor_generator
# solve implementation repeatedly generates neighbors via NeighborGenerator & accepts better neighbors. Resulting RectanglePackingSolution returned/displayed

from core.optimization_algorithm import OptimizationAlgo

class LocalSearchAlgo(OptimizationAlgo):
    pass
    """
    def solve(initialBadSolution):
        # repeatedly generates neighbors via NeighborGenerator
        # accepts better neighbors
        
        - bekommt schlechte Lösung
        - was ist nächster besserer Nachbar
        - schlussbedingungn: kein besserer Nachbar
        - return solution an main
    """

    def __init__(self, neighborhood):
        self.nb = neighborhood

    def solve(self, problem):
        sol = problem.bad_solution()
        while True:
            improved = self.nb.best_improving_neighbor(problem, sol) 
            if improved is None: break
            sol = improved
        return sol

