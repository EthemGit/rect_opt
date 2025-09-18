# abstract class

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List

S = TypeVar("S")  # Solution type

class OptimizationAlgo(ABC, Generic[S]):
    
    @abstractmethod
    def solve(self, problem) -> List[S]:
        """Solves given problem. Returns list of iterative solutions: this allows 
        to show incremental progress towards final solution. """
        pass
