# abstract class
# Defines how greedy algorithms select the next item (e.g., rectangle) to place.
# called by greedy_algo
# implemented in greedy_strategy1 and greedy_strategy2


from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class SelectionStrategy(ABC):

    @abstractmethod
    def order(self, items):
        """Return a permutation or iterator of 'items' in the desired order."""
        pass
