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

        prev_val = problem.evaluate(sol)

        for idx, item in enumerate(order):
            new_sol = problem.process_item(sol, item)
            new_val = problem.evaluate(new_sol)

            # Append solution if stride reached or box count changed
            if idx % stride == 0 or new_val != prev_val:
                sols.append(new_sol)
                prev_val = new_val

            sol = new_sol

        # append last solution
        if sols[-1] is not sol:
            sols.append(sol)

        return sols
