# implements optimization_algorithm
# problem-agnostic
# calls selection_strategy
# next step chosen and implemented via SelectionStrategy

from core.optimization_algorithm import OptimizationAlgo
import math

class GreedyAlgo(OptimizationAlgo):
    """
    
    Attributes
        strategy: Strategy  # chosen by user
    """

    def __init__ (self, selection_strategy):
        self.strategy = selection_strategy

    def solve(self, problem):
        items = problem.items_for_greedy()
        order = self.strategy.order(items=items)
        number_rects = len(order)
        
        max_steps = 100
        stride = math.ceil(number_rects / max_steps)

        sol = problem.empty_solution()
        sols = [sol]

        for idx, item in enumerate(order):
            new_sol = problem.process_item(sol, item)

            # Append solution if stride reached or new box added
            if idx % stride == 0 or len(sol.boxes) != len(new_sol.boxes):
                sols.append(new_sol)
            sol = new_sol

        # append last solution
        if sols[-1] is not sol:
            sols.append(sol)

        return sols
