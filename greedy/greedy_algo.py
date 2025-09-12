# implements optimization_algorithm
# problem-agnostic
# calls selection_strategy
# next step chosen and implemented via SelectionStrategy

from core.selection_strategy import SelectionStrategy
import OptimizationAlgo

class GreedyAlgo(OptimizationAlgo):
    pass
    """
    Attributes
        strategy: Strategy  # chosen by user
    """

    def __init__ (self, selection_strategy: SelectionStrategy):
        self.strategy = selection_strategy

    def solve(self, problem, empty_solution):
        items = problem.items_for_greedy(empty_solution) 
        order = self.strategy.order(items, problem, empty_solution)
        sol = empty_solution
        for item in order:
            sol = problem.place_item(sol, item)
        return sol
