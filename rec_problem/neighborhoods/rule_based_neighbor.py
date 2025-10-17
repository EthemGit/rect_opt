# rec_problem\neighborhoods\rule_based_neighbor.py
from core.neighbor_generator import NeighborGenerator
from dataclasses import dataclass

import random

@dataclass
class RuleBasedNeighborhood(NeighborGenerator):
    """
    Rule-based neighborhood:
      TODO
    Parameters:
      - max_neighbors: optional cap for neighbors generated (helps performance)
    """
    max_neighbors: int = 400

    def generate_neighbors(self, problem, current_solution):
        base = current_solution.permutation          # list of rectangle IDs
        generated = 0

        # Get candidate rectangles (as Rectangle objects)
        candidates = self._build_candidates(current_solution)
        moved_ids = [r.id for r in candidates]
        if not moved_ids:
            return

        moved_set = set(moved_ids)

        while generated < self.max_neighbors:
            # Start from base, remove any of the candidate ids
            new_perm = [rid for rid in base if rid not in moved_set]

            # Insert each candidate at random index
            # (shuffle order so insertion order is randomized too)
            group = moved_ids[:]
            random.shuffle(group)
            for rid in group:
                random_index = random.randint(0, len(new_perm))  # inclusive of end
                new_perm.insert(random_index, rid)

            yield problem.construct_from_order(new_perm)
            generated += 1


    def _build_candidates(self, solution):
        """Returns 5 random rects."""
        boxes = solution.boxes
        if not boxes:
            return []

        # collect all positioned rects from all boxes
        all_rects = []
        for b in boxes:
            rects = [r for r in getattr(b, "my_rects", {}).keys()
                    if getattr(r, "is_positioned", False)]
            all_rects.extend(rects)

        if not all_rects:
            return []

        # sample without replacement
        return random.sample(all_rects, k=min(5, len(all_rects)))


    def is_permutation_based(self) -> bool:
        """This neighborhood is permutation-based."""
        return True