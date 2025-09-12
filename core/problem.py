# abstraktes Problem, das z.B. von rectangle packing Problem implementiert wird

from abc import ABC, abstractmethod


class Problem(ABC):
    pass

    # ----- GREEDY -------        
    @abstractmethod
    def empty_solution(self):  # -> Solution
        pass
    
    @abstractmethod
    def items_for_greedy(self):   # -> List
        """Returns items to sort with greedy algorithm"""
        pass
    
    @abstractmethod
    def process_item(self, sol, item):
        """Processes given item according to problem at hand"""
        pass

    # ----- LOCAL SEARCH -----

    @abstractmethod
    def bad_solution(self):  #    -> Solution
        pass
    
    @abstractmethod
    def neighbors(self, sol):
        pass
    
    @abstractmethod
    def evaluate(self, sol) -> float:
        """Evaluates given solution. Needed for stop condition."""
        pass
