#!/usr/bin/env python3
"""Main benchmark runner script.

Usage:
    uv run python -m benchmarks.run_benchmarks
    uv run python -m benchmarks.run_benchmarks --validation
    uv run python -m benchmarks.run_benchmarks --models
    uv run python -m benchmarks.run_benchmarks --all --iterations 5000
"""

import argparse
import json
import sys
from datetime import datetime

from benchmarks.bench_models import ExporterBenchmarks, ModelBenchmarks
from benchmarks.bench_validation import BenchmarkResult, ValidationBenchmarks


def print_header(title: str) -> None:
    """Print a section header."""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_results(results: list[BenchmarkResult]) -> None:
    """Print benchmark results."""
    for result in results:
        print()
        print(result)


def results_to_dict(results: list[BenchmarkResult]) -> list[dict]:
    """Convert results to dictionary format."""
    return [
        {
            "name": r.name,
            "iterations": r.iterations,
            "total_time_ms": r.total_time_ms,
            "mean_time_ms": r.mean_time_ms,
            "median_time_ms": r.median_time_ms,
            "min_time_ms": r.min_time_ms,
            "max_time_ms": r.max_time_ms,
            "std_dev_ms": r.std_dev_ms,
            "ops_per_second": r.ops_per_second,
        }
        for r in results
    ]


def run_all_benchmarks(iterations: int = 1000, output_json: bool = False) -> dict:
    """Run all benchmarks and return results."""
    all_results = {
        "timestamp": datetime.now().isoformat(),
        "iterations": iterations,
        "benchmarks": {},
    }

    # Validation benchmarks
    print_header("Validation Engine Benchmarks")
    validation = ValidationBenchmarks(iterations=iterations)
    validation_results = validation.run_all()
    print_results(validation_results)
    all_results["benchmarks"]["validation"] = results_to_dict(validation_results)

    # Model benchmarks
    print_header("Model Benchmarks")
    models = ModelBenchmarks(iterations=iterations)
    model_results = models.run_all()
    print_results(model_results)
    all_results["benchmarks"]["models"] = results_to_dict(model_results)

    # Exporter benchmarks
    print_header("Exporter Benchmarks")
    exporters = ExporterBenchmarks(iterations=iterations)
    exporter_results = exporters.run_all()
    print_results(exporter_results)
    all_results["benchmarks"]["exporters"] = results_to_dict(exporter_results)

    # Summary
    print_header("Summary")
    total_benchmarks = len(validation_results) + len(model_results) + len(exporter_results)
    print(f"\n  Total benchmarks run: {total_benchmarks}")
    print(f"  Iterations per benchmark: {iterations}")

    # Find fastest and slowest
    all_bench_results = validation_results + model_results + exporter_results
    fastest = min(all_bench_results, key=lambda r: r.mean_time_ms)
    slowest = max(all_bench_results, key=lambda r: r.mean_time_ms)

    print(f"\n  Fastest: {fastest.name} ({fastest.mean_time_ms:.3f}ms)")
    print(f"  Slowest: {slowest.name} ({slowest.mean_time_ms:.3f}ms)")

    # Highest throughput
    highest_throughput = max(all_bench_results, key=lambda r: r.ops_per_second)
    print(
        f"  Highest throughput: {highest_throughput.name} ({highest_throughput.ops_per_second:.0f} ops/sec)"
    )

    print()
    print("=" * 70)

    return all_results


def run_validation_benchmarks(iterations: int = 1000) -> None:
    """Run only validation benchmarks."""
    print_header("Validation Engine Benchmarks")
    validation = ValidationBenchmarks(iterations=iterations)
    print_results(validation.run_all())
    print()


def run_model_benchmarks(iterations: int = 1000) -> None:
    """Run only model and exporter benchmarks."""
    print_header("Model Benchmarks")
    models = ModelBenchmarks(iterations=iterations)
    print_results(models.run_all())

    print_header("Exporter Benchmarks")
    exporters = ExporterBenchmarks(iterations=iterations)
    print_results(exporters.run_all())
    print()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run dppvalidator performance benchmarks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python -m benchmarks.run_benchmarks --all
  uv run python -m benchmarks.run_benchmarks --validation --iterations 5000
  uv run python -m benchmarks.run_benchmarks --all --json > results.json
        """,
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all benchmarks (default)",
    )
    parser.add_argument(
        "--validation",
        action="store_true",
        help="Run only validation benchmarks",
    )
    parser.add_argument(
        "--models",
        action="store_true",
        help="Run only model and exporter benchmarks",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1000,
        help="Number of iterations per benchmark (default: 1000)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    args = parser.parse_args()

    # Default to --all if no specific benchmark is selected
    if not any([args.all, args.validation, args.models]):
        args.all = True

    print()
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║              dppvalidator Performance Benchmarks                     ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print(f"\n  Iterations: {args.iterations}")

    if args.all:
        results = run_all_benchmarks(iterations=args.iterations, output_json=args.json)
        if args.json:
            print(json.dumps(results, indent=2))
    elif args.validation:
        run_validation_benchmarks(iterations=args.iterations)
    elif args.models:
        run_model_benchmarks(iterations=args.iterations)

    return 0


if __name__ == "__main__":
    sys.exit(main())
