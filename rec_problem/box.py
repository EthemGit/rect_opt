# repräsentiert eine Box. Hat Rectangles als Attribute

from typing import Dict, Tuple, Set, List
from rec_problem.rectangle import Rectangle
from core.item import Item

class Box(Item):
    def __init__(self, box_length):
        self.box_length = box_length

        # Maps each contained rect to coordinates of its upper left corner within box
        self.my_rects: Dict[Rectangle, Tuple[int, int]] = {}

        # Set of all empty position (at start: all)
        self.empty_coordinates: Set = {
            (x,y) for x in range(box_length) for y in range(box_length) 
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
                
        # Update set of empty coordinates
        for x in range(rect.width):
            for y in range(rect.length):
                self.empty_coordinates.remove((x+posX, y+posY))

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
        
        for x in range(rect.width):
            for y in range(rect.length):
                self.empty_coordinates.add((x+posX, y+posY))

        # remove rect
        rect.is_positioned = False
        del self.my_rects[rect]
    
    def get_rect_position(self, rect) -> Tuple[int, int]:
        # returns position of rect within box
        return self.my_rects[rect]
    
    def rect_fits_here(self, coordinates: Tuple[int, int], rect) -> bool:
            """ Checks whether whole of given rect fits at specific coordinates in given box.
            
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
                    if not cell in self.empty_coordinates:
                        return False

            return True
    
    # get all rects in this box
    def get_rects(self) -> List[Rectangle]:
        return list(self.my_rects.keys())

    # compute anchor positions for placing new rects
    def get_anchor_positions(self) -> Set[Tuple[int, int]]:
        """Return potential 'anchor' positions for trying new placements.
        Anchors are positions aligned to existing rects (right/below)."""
        anchors = set()
        for rect, (x, y) in self.my_rects.items():
            anchors.add((x + rect.width, y))      # right edge
            anchors.add((x, y + rect.length))     # bottom edge
        return anchors

    # lightweight clone (instead of deepcopy)
    def clone(self) -> "Box":
        new_box = Box(self.box_length)
        # Copy occupied rects
        new_box.my_rects = self.my_rects.copy()
        new_box.empty_coordinates = self.empty_coordinates.copy()
        return new_box
