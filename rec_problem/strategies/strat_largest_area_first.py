# implements selection_strategy
# used by GreedyAlgo.solve() to pick next rectangle
# Resulting RectanglePackingSolution displayed

from core.selection_strategy import SelectionStrategy
from rec_problem.rectangle import Rectangle
from rec_problem.box import Box


class LargestAreaFirstStrategy(SelectionStrategy):
    
    def order(self, items) -> list:
        """Orders given rectangles by area"""
        sorted_list = sorted( items, key= lambda r: r.width * r.length, reverse=True )
        return sorted_list
