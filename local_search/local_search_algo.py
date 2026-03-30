from core.optimization_algorithm import OptimizationAlgo
from typing import Optional

class LocalSearchAlgo(OptimizationAlgo):
    """
    Problem-agnostic Local Search.
    - neighbor_generator: an instance of core.neighbor_generator.NeighborGenerator
    - max_iters: safety cap
    - stride: append a solution to the GUI history every N accepted steps
    - first_improvement: whether to accept first improving neighbor (fast) or best (slower)
    """

    def __init__(self, neighbor_generator, max_iters: int = 1000, stride: int = 1, first_improvement: bool = True, max_neighbors_per_step: Optional[int] = None, time_limit_seconds: float = 0.0, no_improve_limit: int = 1, non_box_improve_accept_limit: int = 0):
        self.neighbor_generator = neighbor_generator
        self.max_iters = int(max_iters)
        self.stride = int(stride)
        self.first_improvement = bool(first_improvement)
        self.max_neighbors_per_step = max_neighbors_per_step
        self.time_limit_seconds = time_limit_seconds
        # no_improve_limit: how many consecutive None-returns from best_improving_neighbor
        # are tolerated before stopping. For deterministic neighborhoods use 1 (default).
        # For stochastic neighborhoods (e.g. rule-based with random sampling) use >1
        # so the algorithm retries with a different random sample before giving up.
        self.no_improve_limit = max(1, int(no_improve_limit))
        # non_box_improve_accept_limit: max consecutive accepted moves that do not
        # reduce box count. 0 disables the cap.
        self.non_box_improve_accept_limit = max(0, int(non_box_improve_accept_limit))

    def _attach_step_metadata(self, sol):
        """Attach neighborhood metadata needed by the GUI to a solution snapshot."""
        allowed_overlap = getattr(self.neighbor_generator, "allowed_overlap", None)
        if allowed_overlap is not None:
            try:
                sol.allowed_overlap = float(allowed_overlap)
            except (TypeError, ValueError):
                pass
        
        # Capture compacting and reheating flags if present
        is_compacting = getattr(sol, "is_compacting", False)
        is_reheating = getattr(sol, "is_reheating", False)
        if is_compacting:
            sol.is_compacting = True
        if is_reheating:
            sol.is_reheating = True


    def solve(self, problem):
        """
        Starts with the initial solution provided by the neighbor generator and iteratively
        asks the neighbor generator for improving neighbors until no improvement
        is possible or max_iters is reached.
        Returns a list of solutions (for GUI / step visualization).
        """
        import time
        start_time = time.time()

        sol = self.neighbor_generator.initial_solution(problem)
        self._attach_step_metadata(sol)
        sols = [sol]
        it = 0
        consecutive_no_improve = 0
        consecutive_non_box_improve_accepts = 0
        steps_since_last_record = 0
        accumulated_highlights = set()
        pending_compacting = False
        pending_reheating = False
        while it < self.max_iters:
            if self.time_limit_seconds and (time.time() - start_time) > self.time_limit_seconds:
                break
            improved = self.neighbor_generator.best_improving_neighbor(
                problem, sol,
                first_improvement=self.first_improvement,
                max_neighbors=self.max_neighbors_per_step
            )
            if improved is None:
                consecutive_no_improve += 1
                if consecutive_no_improve >= self.no_improve_limit:
                    break
                # Stochastic neighborhood: retry with a different random sample
                continue

            consecutive_no_improve = 0
            if hasattr(improved, 'highlighted_ids'):
                accumulated_highlights |= improved.highlighted_ids

            old_boxes = len(sol.boxes)
            new_boxes = len(improved.boxes)
            if new_boxes < old_boxes:
                consecutive_non_box_improve_accepts = 0
            else:
                consecutive_non_box_improve_accepts += 1

            sol = improved
            self._attach_step_metadata(sol)
            steps_since_last_record += 1

            # Carry compaction/reheating state until the next recorded GUI step.
            pending_compacting = pending_compacting or bool(getattr(sol, 'is_compacting', False))
            pending_reheating = pending_reheating or bool(getattr(sol, 'is_reheating', False))

            if steps_since_last_record >= self.stride:
                if accumulated_highlights and hasattr(sol, 'highlighted_ids'):
                    sol.highlighted_ids = accumulated_highlights
                if pending_compacting:
                    sol.is_compacting = True
                if pending_reheating:
                    sol.is_reheating = True
                sols.append(sol)
                steps_since_last_record = 0
                accumulated_highlights = set()
                pending_compacting = False
                pending_reheating = False

            it += 1

            if self.non_box_improve_accept_limit > 0 and consecutive_non_box_improve_accepts >= self.non_box_improve_accept_limit:
                break

        # ensure final solution included
        if sols[-1] is not sol:
            if accumulated_highlights and hasattr(sol, 'highlighted_ids'):
                sol.highlighted_ids = accumulated_highlights
            pending_compacting = pending_compacting or bool(getattr(sol, 'is_compacting', False))
            pending_reheating = pending_reheating or bool(getattr(sol, 'is_reheating', False))
            if pending_compacting:
                sol.is_compacting = True
            if pending_reheating:
                sol.is_reheating = True
            self._attach_step_metadata(sol)
            sols.append(sol)
        
        # Option A: Force final cleanup if solution is invalid (e.g., due to timeout)
        final_sol = sols[-1] if sols else None
        if final_sol:
            try:
                final_sol.validate(permitted_error=0.0)
            except ValueError:
                # Final solution is invalid; force compaction if neighbor generator supports it
                if hasattr(self.neighbor_generator, '_compact_all_boxes'):
                    try:
                        compacted = self.neighbor_generator._compact_all_boxes(final_sol)
                        # Only replace if compaction resulted in a valid, non-empty solution
                        try:
                            compacted.validate(permitted_error=0.0)
                            sols[-1] = compacted
                        except ValueError:
                            pass  # Keep original if compaction didn't fix it
                    except Exception:
                        pass  # Keep original if compaction failed
        
        return sols
