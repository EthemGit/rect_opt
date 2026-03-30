"""
benchmark.py — Standalone benchmark harness (Section 8).

Usage:
    python benchmark.py --mode demo      # small/fast, no log file
    python benchmark.py --mode verify    # large/thorough, writes CSV log

Tuple format: (num_instances, num_rects, min_width, min_height, max_width, max_height, box_length)
"""

import argparse
import csv
import multiprocessing as mp
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple

from rec_problem.rectangle_packing_problem import RectanglePackingProblem, RectangleTemplate
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
# Instance generation and caching
# ---------------------------------------------------------------------------

def save_instance_templates(templates: List[RectangleTemplate], csv_path: str) -> None:
    """Save rectangle templates to CSV for reproducible reconstruction."""
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "length", "width"])
        for t in templates:
            writer.writerow([t.id, t.length, t.width])


def load_instance_templates(csv_path: str) -> List[RectangleTemplate]:
    """Load rectangle templates from CSV."""
    templates = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            templates.append(RectangleTemplate(
                id=int(row["id"]),
                length=int(row["length"]),
                width=int(row["width"]),
            ))
    return templates


def generate_and_save_instances(
    spec: Tuple,
    instance_dir: str,
) -> List[str]:
    """
    Generate random rectangle instances and save their templates to CSV files.
    Returns list of CSV file paths (one per instance).
    """
    num_instances, num_rects, min_w, min_h, max_w, max_h, L = spec
    os.makedirs(instance_dir, exist_ok=True)

    csv_paths = []
    for inst_id in range(num_instances):
        # Generate fresh random instance
        problem = RectanglePackingProblem(
            box_length=L,
            rect_number=num_rects,
            min_width=min_w,
            max_width=max_w,
            min_height=min_h,
            max_height=max_h,
        )
        
        # Save its templates
        csv_path = os.path.join(instance_dir, f"instance_{inst_id}.csv")
        templates = list(problem.rect_templates.values())
        save_instance_templates(templates, csv_path)
        csv_paths.append(csv_path)

    return csv_paths


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
    test_instance: int
    number_boxes: int
    cpu_time_seconds: float
    all_rects_positioned: bool
    no_overlap: bool
    is_valid: bool
    error: str = ""


# ---------------------------------------------------------------------------
# Algorithm factory
# ---------------------------------------------------------------------------

def make_algorithm_names() -> List[str]:
    """Return benchmark algorithm names in execution order."""
    names = [
        "Greedy-LargestAreaFirst",
        "Greedy-LongestSideFirst",
        "LocalSearch-Geometry",
        "LocalSearch-RuleBased",
    ]
    if _HAS_PARTIAL_OVERLAP:
        names.append("LocalSearch-PartialOverlap")
    return names


def build_algorithm(algo_name: str, time_limit: float):
    """Create a fresh algorithm instance by name."""
    if algo_name == "Greedy-LargestAreaFirst":
        return GreedyAlgo(LargestAreaFirstStrategy())
    if algo_name == "Greedy-LongestSideFirst":
        return GreedyAlgo(LongestSideFirstStrategy())
    if algo_name == "LocalSearch-Geometry":
        return LocalSearchAlgo(
            GeometryBasedNeighborhood(max_neighbors=500),
            max_iters=20_000,
            stride=1,
            first_improvement=True,
            max_neighbors_per_step=500,
            time_limit_seconds=time_limit,
            no_improve_limit=10,
        )
    if algo_name == "LocalSearch-RuleBased":
        return LocalSearchAlgo(
            RuleBasedNeighborhood(max_neighbors=200),
            max_iters=20_000,
            stride=1,
            first_improvement=True,
            time_limit_seconds=time_limit,
            non_box_improve_accept_limit=10,
        )
    if algo_name == "LocalSearch-PartialOverlap" and _HAS_PARTIAL_OVERLAP:
        return LocalSearchAlgo(
            PartialOverlapNeighborhood(max_neighbors=500),
            max_iters=20_000,
            stride=1,
            first_improvement=True,
            max_neighbors_per_step=500,
            time_limit_seconds=time_limit,
        )
    raise ValueError(f"Unknown algorithm: {algo_name}")


def _isolated_algo_worker(
    algo_name: str,
    time_limit: float,
    box_length: int,
    templates: List[RectangleTemplate],
    out_q,
) -> None:
    """Run one algorithm in an isolated child process and return a serializable payload."""
    try:
        problem = RectanglePackingProblem.from_templates(box_length=box_length, templates=templates)
        algo = build_algorithm(algo_name, time_limit)

        t0_cpu = time.thread_time()
        solutions = algo.solve(problem)
        cpu_s = time.thread_time() - t0_cpu

        final_sol = solutions[-1]
        objective = len(final_sol.boxes)

        expected_ids = {t.id for t in templates}
        placed_ids = [r.id for b in final_sol.boxes for r in b.my_rects.keys()]
        placed_id_set = set(placed_ids)
        all_rects_positioned = (
            len(placed_ids) == len(expected_ids)
            and placed_id_set == expected_ids
        )

        no_overlap = True
        error_parts = []
        try:
            final_sol.validate(permitted_error=0.0)
        except Exception as exc:
            no_overlap = False
            error_parts.append(f"overlap/bounds: {exc}")

        if not all_rects_positioned:
            missing = len(expected_ids - placed_id_set)
            duplicates = len(placed_ids) - len(placed_id_set)
            error_parts.append(
                f"incomplete placement: missing_ids={missing}, duplicate_ids={duplicates}"
            )

        valid = all_rects_positioned and no_overlap
        error = "; ".join(error_parts)

        out_q.put({
            "cpu_time_seconds": cpu_s,
            "number_boxes": objective,
            "all_rects_positioned": all_rects_positioned,
            "no_overlap": no_overlap,
            "is_valid": valid,
            "error": error,
        })
    except Exception as exc:
        out_q.put({
            "cpu_time_seconds": -1.0,
            "number_boxes": -1,
            "all_rects_positioned": False,
            "no_overlap": False,
            "is_valid": False,
            "error": str(exc),
        })


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

def run_spec(
    spec: Tuple,
    time_limit: float,
    results: List[BenchmarkResult],
    instance_cache_dir: str = "./.benchmark_instances",
    verbose: bool = True,
) -> None:
    num_instances, num_rects, min_w, min_h, max_w, max_h, L = spec
    algorithm_names = make_algorithm_names()
    mp_ctx = mp.get_context("spawn")

    if verbose:
        print(
            f"\n=== Spec: {num_instances}×{num_rects} rects, "
            f"w=[{min_w},{max_w}], h=[{min_h},{max_h}], L={L} ==="
        )

    # Generate and save instances (excludes this from algorithm timing)
    if verbose:
        print(f"  Generating and saving {num_instances} instances...")
    csv_paths = generate_and_save_instances(spec, instance_cache_dir)

    # For each instance, load fresh and time each algorithm
    for inst_id, csv_path in enumerate(csv_paths):
        templates = load_instance_templates(csv_path)

        for algo_name in algorithm_names:
            out_q = mp_ctx.Queue()
            p = mp_ctx.Process(
                target=_isolated_algo_worker,
                args=(algo_name, time_limit, L, templates, out_q),
            )
            p.start()

            # Keep a hard cap so verify cannot hang forever if a worker gets stuck.
            worker_timeout = max(60.0, time_limit * 8.0)
            p.join(worker_timeout)

            if p.is_alive():
                p.terminate()
                p.join()
                payload = {
                    "cpu_time_seconds": worker_timeout,
                    "number_boxes": -1,
                    "all_rects_positioned": False,
                    "no_overlap": False,
                    "is_valid": False,
                    "error": f"Worker timeout after {worker_timeout:.1f}s",
                }
            else:
                if out_q.empty():
                    payload = {
                        "cpu_time_seconds": -1.0,
                        "number_boxes": -1,
                        "all_rects_positioned": False,
                        "no_overlap": False,
                        "is_valid": False,
                        "error": f"Worker exited with code {p.exitcode} without payload",
                    }
                else:
                    payload = out_q.get()

            cpu_s = float(payload.get("cpu_time_seconds", -1.0))
            objective = int(payload.get("number_boxes", -1))
            all_rects_positioned = bool(payload.get("all_rects_positioned", False))
            no_overlap = bool(payload.get("no_overlap", False))
            valid = bool(payload.get("is_valid", False))
            error = str(payload.get("error", ""))

            status = (
                f"OK (all_rects={all_rects_positioned}, no_overlap={no_overlap})"
                if valid
                else f"INVALID (all_rects={all_rects_positioned}, no_overlap={no_overlap}): {error}"
            )
            if verbose:
                print(
                    f"  {algo_name:<32}  inst={inst_id}"
                    f"  boxes={objective}  cpu={cpu_s:.3f}s  {status}"
                )

            results.append(BenchmarkResult(
                algo_name=algo_name,
                num_rects=num_rects,
                box_length=L,
                test_instance=inst_id,
                number_boxes=objective,
                cpu_time_seconds=cpu_s,
                all_rects_positioned=all_rects_positioned,
                no_overlap=no_overlap,
                is_valid=valid,
                error=error,
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
        valid_rs = [r for r in rs if r.is_valid and r.number_boxes >= 0]
        if valid_rs:
            avg_obj = sum(r.number_boxes for r in valid_rs) / len(valid_rs)
            min_obj = min(r.number_boxes for r in valid_rs)
            max_obj = max(r.number_boxes for r in valid_rs)
            avg_cpu = sum(r.cpu_time_seconds for r in valid_rs) / len(valid_rs)
            max_cpu = max(r.cpu_time_seconds for r in valid_rs)
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
            "algo", "num_rects", "box_length", "test_instance",
            "number_boxes", "cpu_time_seconds", "all_rects_positioned", "no_overlap", "is_valid", "error",
        ])
        for r in results:
            writer.writerow([
                r.algo_name, r.num_rects, r.box_length, r.test_instance,
                r.number_boxes, f"{r.cpu_time_seconds:.6f}",
                r.all_rects_positioned, r.no_overlap, r.is_valid, r.error,
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
