from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class SelectionStrategy(ABC):

    @abstractmethod
    def order(self, items):
        """Return a permutation or iterator of 'items' in the desired order."""
        pass
