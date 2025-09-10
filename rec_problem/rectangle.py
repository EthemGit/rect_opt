# repräsentiert ein Rechteck

from dataclasses import dataclass

@dataclass
class Rectangle:
    length: int
    width: int
    is_positioned: bool = False  # whether this rect has already been put into a box

