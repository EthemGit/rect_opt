# Aufgabe: generates instances, validates inputs
# Manages problem parameters (box size, rectangle list), creates instances, validates solutions.
# Not necessarily tied to interface (could be helper class)

from dataclasses import dataclass
from typing import List
import random

from core.problem import Problem
from rectangle import Rectangle
from box import Box

@dataclass
class RectanglePackingProblem(Problem):
    """
    Erstellt zufällige Menge an Rectangles und 
    Liste mit einer Box basierend auf Attributen (User-Input von GUI)
    
    Attribute:
        - Menge von Boxen
        - Menge von Rectangles
    """

    """
    -- Anzahl Rechtecke
    -- beide minimalen und maximalen Seitenlängen für die zufällige Erzeugung
    -- Boxlänge L     für jede zu generierende Instanz festlegen
    """

    boxes: List[Box]
    rectangles: List[Rectangle]

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

        # Boxes initialisieren
        

        # Random Rectangles erstellen
        

        """
        
        """

