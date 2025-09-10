# implements selection_strategy
# used by GreedyAlgo.solve() to pick next rectangle


import SelectionStrategy
from rec_problem.rectangle import Rectangle
from rec_problem.box import Box
from core.optimization_algorithm import OptimizationAlgo
from greedy_algo import GreedyAlgo

class SelectionStrategy2(SelectionStrategy):
    
    def select_next(self, current_solution, problem) -> Rectangle:
        """Select next step to perform."""
        pass

    def reset(self):
        """Reset internal state (default: do nothing)."""
        pass

    def get_algo_type(self) -> OptimizationAlgo:
        return type(GreedyAlgo)
