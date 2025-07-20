# abstract class
# Defines how greedy algorithms select the next item (e.g., rectangle) to place.
# called by greedy_algo
# implemented in greedy_strategy1 and greedy_strategy2


from abc import ABC

class SelectionStrategy(ABC):

    @abstractmethod
    def select_next(self, rectangles_remaining, current_solution):
        """Select and return the next rectangle to place from rectangles_remaining.
        Must remove the selected rectangle from rectangles_remaining."""
        pass

    def reset(self):
        """Reset internal state (default: do nothing)."""
        pass