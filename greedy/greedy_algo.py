# implements optimization_algorithm
# problem-agnostic
# calls selection_strategy
# next step chosen and implemented via SelectionStrategy

from core.optimization_algorithm import OptimizationAlgo

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
        sol = problem.empty_solution()
        sols = []
        sols.append(sol)
        for item in order:
            sol = problem.process_item(sols[-1], item)
            sols.append(sol)
        return sols
