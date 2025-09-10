# abstract class
# Defines how greedy algorithms select the next item (e.g., rectangle) to place.
# called by greedy_algo
# implemented in greedy_strategy1 and greedy_strategy2


from abc import ABC, abstractmethod
from dataclasses import dataclass
from optimization_algorithm import OptimizationAlgo

@dataclass
class SelectionStrategy(ABC):

    @abstractmethod
    def select_next(self, current_solution, problem):
        """Select next step to perform."""
        pass
    
    @abstractmethod
    def get_algo_type(self) -> OptimizationAlgo:
        pass

    def reset(self):
        """Reset internal state (default: do nothing)."""
        pass