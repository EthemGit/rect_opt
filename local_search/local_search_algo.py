# implements optimization_algorithm
# calls neighbor_generator
# solve implementation repeatedly generates neighbors via NeighborGenerator & accepts better neighbors. Resulting RectanglePackingSolution returned/displayed

from core.optimization_algorithm import OptimizationAlgo
import math

class LocalSearchAlgo(OptimizationAlgo):
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
        sols = [sol]
        
        max_steps = 100
        number_rects = len(sol.rectangles)
        stride = math.ceil(number_rects / max_steps)
        
        idx = 0
        
        while True:
            improved = self.nb.best_improving_neighbor(problem, sol) 
            if improved is None: break

            if idx  % stride == 0 or len(sol.boxes) != len(improved.boxes):
                sols.append(improved)

            sol = improved
            idx += 1

        # append last solution
        if sols[-1] is not sol:
            sols.append(sol)
            
        return sols
