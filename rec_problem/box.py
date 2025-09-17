# repräsentiert eine Box. Hat Rectangles als Attribute

from typing import Dict, Tuple
from rec_problem.rectangle import Rectangle
from core.item import Item

class Box(Item):
    def __init__(self, box_length):
        self.box_length = box_length

        # Maps each contained rect to coordinates of its upper left corner within box
        self.my_rects: Dict[Rectangle, Tuple[int, int]] = {}

        # Maps each field to number of rects occupying it
        self.field_occupation: Dict[Tuple[int, int], int] = {
            (x, y): 0 for x in range(box_length) for y in range(box_length)
        }

    def insert_rect(self, rect: Rectangle, coordinates=(0,0)) -> None:
        """Inserts a rect in this box."""
        # check bounds
        posX, posY = coordinates
        if (posX < 0 or posY < 0 or
            posX + rect.width > self.box_length or
            posY + rect.length > self.box_length
        ):
            raise ValueError(
                f"Rectangle with size ({rect.length}, {rect.width}) does not fit inside box of length {self.box_length} at ({posX}, {posY}) "
            )
        
        # Update map of occupied fields
        for x in range(rect.width):
            for y in range(rect.length):
                self.field_occupation[(x+posX, y+posY)] += 1

        # Insert rect
        rect.is_positioned = True
        self.my_rects[rect] = (posX, posY)

    def remove_rect(self, rect) -> None:
        """Removes given rect from this box."""
        # get previous position
        pos = self.my_rects[rect]
        if pos == None:
            raise ValueError(f"Rect {rect} not in this box.")
            
        posX, posY = pos
        
        # update map of occupied fields
        for x in range(rect.width):
            for y in range(rect.length):
                if (self.field_occupation[(x+posX, y+posY)] > 0):
                    self.field_occupation[(x+posX, y+posY)] -= 1
                else:
                    raise ValueError("Mysteriously a rect exists here but field occupation = 0")
        
        # remove rect
        rect.is_positioned = False
        del self.my_rects[rect]
    
    def get_rect_position(self, rect) -> Tuple[int, int]:
        # returns position of rect within box
        return self.my_rects[rect]
    
    def rect_fits_here(self, coordinates: Tuple[int, int], rect) -> bool:
            """ Checks whether given rect fits at specific coordinates in given box.
            
            Attributes:
                coordinates: Tuple(int, int)
                    The coordinates we check whether the rect fits in.
                rect: Rectangle
                    The rectangle to be put into the box.
            """
            # Check boundaries
            x, y = coordinates
            if x < 0 or y < 0:
                return False
            if (x + rect.width) > self.box_length:
                return False
            if (y + rect.length) > self.box_length:
                return False
            
            # Check that there is no other rectangle in space occupied by coordinates + given rect
            for dx in range(rect.width):
                for dy in range(rect.length):
                    cell = (x+dx, y+dy)
                    if self.field_occupation.get(cell, 0) != 0:
                        return False

            return True
    