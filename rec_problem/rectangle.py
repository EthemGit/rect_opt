# repräsentiert ein Rechteck

from dataclasses import dataclass
from core.item import Item

@dataclass(unsafe_hash=True)
class Rectangle(Item):
    length: int
    width: int
    is_positioned: bool = False  # whether this rect has already been put into a box

