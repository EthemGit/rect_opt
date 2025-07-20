# abstract class

from abc import ABC, abstractmethod

class OptimizationAlgo(ABC):
    @abstractmethod
    def solve(self, initialSolution):
        pass

    @abstractmethod
    def step(currentSolution):
        """Performs a single iteration step for debugging/GUI"""
        pass 

    def reset(self):
        """Reset internal state (default: do nothing)."""
        pass