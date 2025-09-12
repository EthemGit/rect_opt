# abstract class

from abc import ABC, abstractmethod

from problem import Problem
from solution import Solution

class OptimizationAlgo(ABC):
    @abstractmethod
    def solve(self, problem: Problem, initialSolution: Solution):
        pass

    @abstractmethod
    def reset(self):
        """Reset internal state (default: do nothing)."""
        pass