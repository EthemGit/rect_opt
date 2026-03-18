"""
benchmark.py — Standalone benchmark harness (Section 8).

Usage:
    python benchmark.py --mode demo      # small/fast, no log file
    python benchmark.py --mode verify    # large/thorough, writes CSV log

Tuple format: (num_instances, num_rects, min_width, min_height, max_width, max_height, box_length)
"""

import argparse
import csv
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple

from rec_problem.rectangle_packing_problem import RectanglePackingProblem
from greedy.greedy_algo import GreedyAlgo
from local_search.local_search_algo import LocalSearchAlgo
from rec_problem.strategies.strat_largest_area_first import LargestAreaFirstStrategy
from rec_problem.strategies.strat_longest_side_first import LongestSideFirstStrategy
from rec_problem.neighborhoods.geometry_based_neighbor import GeometryBasedNeighborhood
from rec_problem.neighborhoods.rule_based_neighbor import RuleBasedNeighborhood

try:
    from rec_problem.neighborhoods.partial_overlap_neighbor import PartialOverlapNeighborhood
    _HAS_PARTIAL_OVERLAP = True
except Exception:
    _HAS_PARTIAL_OVERLAP = False


# ---------------------------------------------------------------------------
# Benchmark specs
# ---------------------------------------------------------------------------

# (num_instances, num_rects, min_width, min_height, max_width, max_height, box_length)
SMOKE_TUPLES: List[Tuple] = [
    (1,  5, 1, 1,  3,  3,  5),
    (1, 10, 1, 1,  4,  4,  7),
    (1, 20, 1, 1,  5,  5,  8),
]

DEMO_TUPLES: List[Tuple] = [
    (3,  20,  1,  1, 10, 10, 15),
    (3,  50,  2,  2, 15, 15, 20),
    (2, 100,  1,  1, 20, 20, 25),
]

VERIFY_TUPLES: List[Tuple] = [
    (5,  100,  1,  1, 20, 20, 25),
    (5,  250,  2,  2, 30, 30, 40),
    (3,  500,  1,  1, 40, 40, 50),
    (2, 1000,  1,  1, 50, 50, 60),
]


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkResult:
    algo_name: str
    num_rects: int
    box_length: int
    instance_id: int
    objective: int
    cpu_thread_s: float
    valid: bool
    error: str = ""


# ---------------------------------------------------------------------------
# Algorithm factory
# ---------------------------------------------------------------------------

def make_algorithms(time_limit: float) -> List[Tuple[str, callable]]:
    """Return list of (name, factory_fn) pairs. Factory is called fresh per instance."""
    algos = [
        (
            "Greedy-LargestAreaFirst",
            lambda: GreedyAlgo(LargestAreaFirstStrategy()),
        ),
        (
            "Greedy-LongestSideFirst",
            lambda: GreedyAlgo(LongestSideFirstStrategy()),
        ),
        (
            "LocalSearch-Geometry",
            lambda: LocalSearchAlgo(
                GeometryBasedNeighborhood(max_neighbors=500),
                max_iters=20_000,
                stride=1,
                first_improvement=True,
                max_neighbors_per_step=500,
                time_limit_seconds=time_limit,
            ),
        ),
        (
            "LocalSearch-RuleBased",
            lambda: LocalSearchAlgo(
                RuleBasedNeighborhood(max_neighbors=2000),
                max_iters=20_000,
                stride=1,
                first_improvement=True,
                time_limit_seconds=time_limit,
            ),
        ),
    ]

    if _HAS_PARTIAL_OVERLAP:
        algos.append((
            "LocalSearch-PartialOverlap",
            lambda: LocalSearchAlgo(
                PartialOverlapNeighborhood(max_neighbors=500),
                max_iters=20_000,
                stride=1,
                first_improvement=True,
                max_neighbors_per_step=500,
                time_limit_seconds=time_limit,
            ),
        ))

    return algos


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

def run_spec(
    spec: Tuple,
    time_limit: float,
    results: List[BenchmarkResult],
    verbose: bool = True,
) -> None:
    num_instances, num_rects, min_w, min_h, max_w, max_h, L = spec
    algorithms = make_algorithms(time_limit)

    if verbose:
        print(
            f"\n=== Spec: {num_instances}×{num_rects} rects, "
            f"w=[{min_w},{max_w}], h=[{min_h},{max_h}], L={L} ==="
        )

    for inst_id in range(num_instances):
        problem = RectanglePackingProblem(
            box_length=L,
            rect_number=num_rects,
            min_width=min_w,
            max_width=max_w,
            min_height=min_h,
            max_height=max_h,
        )

        for algo_name, algo_factory in algorithms:
            algo = algo_factory()
            t0 = time.thread_time()
            try:
                solutions = algo.solve(problem)
                cpu_s = time.thread_time() - t0

                final_sol = solutions[-1]
                objective = len(final_sol.boxes)

                valid = True
                error = ""
                try:
                    final_sol.validate(permitted_error=0.0)
                except Exception as e:
                    valid = False
                    error = str(e)

                status = "OK" if valid else f"INVALID: {error}"
                if verbose:
                    print(
                        f"  {algo_name:<32}  inst={inst_id}"
                        f"  boxes={objective}  cpu={cpu_s:.3f}s  {status}"
                    )

                results.append(BenchmarkResult(
                    algo_name=algo_name,
                    num_rects=num_rects,
                    box_length=L,
                    instance_id=inst_id,
                    objective=objective,
                    cpu_thread_s=cpu_s,
                    valid=valid,
                    error=error,
                ))

            except Exception as exc:
                cpu_s = time.thread_time() - t0
                if verbose:
                    print(f"  {algo_name:<32}  inst={inst_id}  ERROR: {exc}")
                results.append(BenchmarkResult(
                    algo_name=algo_name,
                    num_rects=num_rects,
                    box_length=L,
                    instance_id=inst_id,
                    objective=-1,
                    cpu_thread_s=cpu_s,
                    valid=False,
                    error=str(exc),
                ))


# ---------------------------------------------------------------------------
# Summary + CSV
# ---------------------------------------------------------------------------

def print_summary(results: List[BenchmarkResult]) -> None:
    grouped = defaultdict(list)
    for r in results:
        grouped[r.algo_name].append(r)

    print("\n--- Summary ---")
    for algo_name, rs in grouped.items():
        valid_rs = [r for r in rs if r.valid and r.objective >= 0]
        if valid_rs:
            avg_obj = sum(r.objective for r in valid_rs) / len(valid_rs)
            min_obj = min(r.objective for r in valid_rs)
            max_obj = max(r.objective for r in valid_rs)
            avg_cpu = sum(r.cpu_thread_s for r in valid_rs) / len(valid_rs)
            max_cpu = max(r.cpu_thread_s for r in valid_rs)
            invalid_count = len(rs) - len(valid_rs)
            suffix = f"  ({invalid_count} invalid)" if invalid_count else ""
            print(
                f"  {algo_name:<32}  avg={avg_obj:.1f}  min={min_obj}"
                f"  max={max_obj}  avg_cpu={avg_cpu:.3f}s  max_cpu={max_cpu:.3f}s{suffix}"
            )
        else:
            print(f"  {algo_name:<32}  (no valid results)")


def save_csv(results: List[BenchmarkResult], filename: str) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "algo", "num_rects", "box_length", "instance_id",
            "objective", "cpu_thread_s", "valid", "error",
        ])
        for r in results:
            writer.writerow([
                r.algo_name, r.num_rects, r.box_length, r.instance_id,
                r.objective, f"{r.cpu_thread_s:.6f}", r.valid, r.error,
            ])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Rectangle Packing Benchmark Harness")
    parser.add_argument(
        "--mode",
        choices=["smoke", "demo", "verify"],
        default="demo",
        help="smoke = tiny/instant sanity check; demo = small/fast (no log); verify = large/thorough (writes CSV log)",
    )
    args = parser.parse_args()

    if args.mode == "smoke":
        tuples = SMOKE_TUPLES
        time_limit = 2.0
        log_file = None
        print("=== SMOKE MODE ===")
    elif args.mode == "demo":
        tuples = DEMO_TUPLES
        time_limit = 5.0
        log_file = None
        print("=== DEMO MODE ===")
    else:
        tuples = VERIFY_TUPLES
        time_limit = 10.0
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"benchmark_verify_{ts}.csv"
        print(f"=== VERIFY MODE  (log -> {log_file}) ===")

    results: List[BenchmarkResult] = []
    for spec in tuples:
        run_spec(spec, time_limit, results, verbose=True)

    print_summary(results)

    if log_file:
        save_csv(results, log_file)
        print(f"\nLog saved to: {log_file}")


if __name__ == "__main__":
    main()
