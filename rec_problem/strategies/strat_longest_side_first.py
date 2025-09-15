# implements selection_strategy
# used by GreedyAlgo.solve() to pick and place next rectangle
# places rectangle
# Resulting RectanglePackingSolution displayed

from core.selection_strategy import SelectionStrategy
from dataclasses import dataclass

@dataclass
class LongestSideFirstStrategy(SelectionStrategy):
    
    def order(self, items) -> list:
        """Orders given rectangles by longest side length"""
        sorted_list = sorted( items, key= lambda r: max(r.width, r.length), reverse=True )
        return sorted_list

