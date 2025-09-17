# abstract class

from abc import ABC, abstractmethod

class OptimizationAlgo(ABC):
    
    @abstractmethod
    def solve(self, problem, initialSolution):
        pass

    @abstractmethod
    def reset(self):
        """Reset internal state (default: do nothing)."""
        pass