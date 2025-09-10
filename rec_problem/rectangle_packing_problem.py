# Aufgabe: generates instances, validates inputs
# Manages problem parameters (box size, rectangle list), creates instances, validates solutions.
# Not necessarily tied to interface (could be helper class)

from typing import List
import random

from core.problem import Problem
from rectangle import Rectangle

class RectanglePackingProblem(Problem):
    """
    Erstellt zufällige Menge an Rectangles basierend auf Attributen (User-Input von GUI)
    Speichert Box-Länge basierend auf User-Input
    
    Attribute:
        - Box-Länge
        - Menge von Rectangles
    """

    def __init__(
        self, 
        box_length: int,
        rect_number: int,
        rect_min_size: int,
        rect_max_size: int
    ):
        # Sanity checks
        assert box_length > 0, "Box length must be positive"
        assert rect_number > 0, "Number of rectangles must be positive"
        assert 0 < rect_min_size <= rect_max_size, "Invalid rectangle size bounds"

        # Attribute initialisieren
        self.box_length: int = box_length
        self.rectangles: List[Rectangle] = []

        # Random Rectangles erstellen
        for _ in range(rect_number):
            length = random.randint(rect_min_size, rect_max_size)
            width = random.randint(rect_min_size, rect_max_size)
            
            rect = Rectangle(length=length, width=width)
            self.rectangles.append(rect)
        

