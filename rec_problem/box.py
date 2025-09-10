# repräsentiert eine Box. Hat Rectangles als Attribute

from dataclasses import dataclass, field
from typing import Dict, Tuple

from rectangle import Rectangle

@dataclass
class Box:
    box_length: int
    my_rects: Dict[Rectangle: Tuple[int, int]] = field(default_factory=dict) # maps contained rects to their position within the box

    def insert_rect(self, rect: Rectangle, posX: int, posY: int) -> None:
        # inserts a rect in this box
        rect.is_positioned = True
        self.my_rects[rect] = Tuple[posX, posY]

    def remove_rect(self, rect) -> None:
        # removes a rect from this box
        rect.is_positioned = False
        del self.my_rects[rect]
    
    def get_rect_position(self, rect) -> Tuple[int, int]:
        # returns position of rect within box
        return self.my_rects[rect]