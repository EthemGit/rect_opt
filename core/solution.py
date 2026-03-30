from abc import ABC, abstractmethod

class Solution(ABC):
    
    @abstractmethod
    def validate(self, permitted_error):
        """Check if the solution is valid.
        e.g. no overlapping rectangles in rectangle packing."""
        pass

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


        
