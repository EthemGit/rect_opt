# abstraktes Problem, das z.B. von rectangle packing Problem implementiert wird

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List

S = TypeVar("S")  # Solution type
I = TypeVar("I")  # Item type

class Problem(ABC, Generic[S, I]):

    # ----- GREEDY -------        
    @abstractmethod
    def empty_solution(self) -> S:
        """Return an initial empty solution of type S"""
        pass
    
    @abstractmethod
    def items_for_greedy(self) -> List[I]:
        """Returns items to sort with greedy algorithm"""
        pass
    
    @abstractmethod
    def process_item(self, sol: S, item: I) -> S:
        """Process item and return a new/modified solution of type S"""
        pass

    # ----- LOCAL SEARCH -----
    @abstractmethod
    def bad_solution(self) -> S:
        """Return a (bad) starting solution for local search"""
        pass
    
    @abstractmethod
    def neighbors(self, sol: S):
        """Return neighbours of the given solution (list of S)"""
        pass
    
    @abstractmethod
    def evaluate(self, sol: S) -> float:
        """Evaluates given solution. Needed for stop condition."""
        pass

