# abstract class

from abc import ABC, abstractmethod

class OptimizationAlgo(ABC):
    
    @abstractmethod
    def solve(self, problem):
        pass