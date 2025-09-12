# implements selection_strategy
# used by GreedyAlgo.solve() to pick next rectangle
# places rectangle
# Resulting RectanglePackingSolution displayed

from core.selection_strategy import SelectionStrategy
from rec_problem.rectangle import Rectangle
from rec_problem.box import Box

class SelectionStrategy1(SelectionStrategy):
    
    def order(self, items, problem, current_solution) -> Rectangle:
        """Orders given rectangles"""
        pass

    def reset(self):
        """Reset internal state (default: do nothing)."""
        pass


