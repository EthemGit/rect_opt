# abstract class
# Represents a state, can be improved or mutated



from abc import ABC, abstractmethod

class Solution(ABC):
    
    @abstractmethod
    def get_objective_value(self):
        """Return the objective value of the solution (to be minimized).
        e.g. number of boxes used in rectangle packing."""
        pass
    
    @abstractmethod
    def clone(self):
        """Return a deep copy of the solution.
        Used to explore neighbors without modifying the original solution."""
        pass

    @abstractmethod
    def is_feasible(self):
        """Check if the solution satisfies all problem constraints.
        e.g. rectangles do not overlap and fit within the boxes."""
        pass

    @abstractmethod
    def apply_change(self, change):
        """Apply a given modification (change) to the solution.
        Used by local search when moving to a neighbor solution."""
        pass

    @abstractmethod
    def get_state(self):
        """Return the internal state of the solution for visualization or logging.
        e.g. positions of rectangles and contents of boxes."""
        pass

        
