from dataclasses import dataclass
from core.item import Item

@dataclass(eq=False)
class Rectangle(Item):
    id: int
    length: int
    width: int
    is_positioned: bool = False  # whether this rect has already been put into a box

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Rectangle) and self.id == other.id
    
    def get_area(self):
        return self.length*self.width
    