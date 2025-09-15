# implements optimization_algorithm
# problem-agnostic
# calls selection_strategy
# next step chosen and implemented via SelectionStrategy

from core.selection_strategy import SelectionStrategy
from core.optimization_algorithm import OptimizationAlgo

class GreedyAlgo(OptimizationAlgo):
    pass
    """
    Attributes
        strategy: Strategy  # chosen by user
    """

    def __init__ (self, selection_strategy: SelectionStrategy):
        self.strategy = selection_strategy

    def solve(self, problem):
        items = problem.items_for_greedy()
        order = self.strategy.order(items=items)
        sol = problem.empty_solution()
        for item in order:
            sol = problem.process_item(sol, item)
        return sol
