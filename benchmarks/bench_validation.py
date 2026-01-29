"""Benchmarks for the validation engine."""

import statistics
import time
from dataclasses import dataclass

from dppvalidator.models import CredentialIssuer, DigitalProductPassport
from dppvalidator.validators import ValidationEngine


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""

    name: str
    iterations: int
    total_time_ms: float
    mean_time_ms: float
    median_time_ms: float
    min_time_ms: float
    max_time_ms: float
    std_dev_ms: float
    ops_per_second: float

    def __str__(self) -> str:
        return (
            f"{self.name}:\n"
            f"  Iterations: {self.iterations}\n"
            f"  Total: {self.total_time_ms:.2f}ms\n"
            f"  Mean: {self.mean_time_ms:.3f}ms\n"
            f"  Median: {self.median_time_ms:.3f}ms\n"
            f"  Min: {self.min_time_ms:.3f}ms\n"
            f"  Max: {self.max_time_ms:.3f}ms\n"
            f"  Std Dev: {self.std_dev_ms:.3f}ms\n"
            f"  Throughput: {self.ops_per_second:.1f} ops/sec"
        )


def run_benchmark(name: str, func, iterations: int = 1000) -> BenchmarkResult:
    """Run a benchmark and collect timing statistics."""
    times: list[float] = []

    # Warmup
    for _ in range(min(10, iterations // 10)):
        func()

    # Actual benchmark
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms

    total_time = sum(times)
    mean_time = statistics.mean(times)
    median_time = statistics.median(times)
    min_time = min(times)
    max_time = max(times)
    std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
    ops_per_sec = iterations / (total_time / 1000) if total_time > 0 else 0

    return BenchmarkResult(
        name=name,
        iterations=iterations,
        total_time_ms=total_time,
        mean_time_ms=mean_time,
        median_time_ms=median_time,
        min_time_ms=min_time,
        max_time_ms=max_time,
        std_dev_ms=std_dev,
        ops_per_second=ops_per_sec,
    )


# Sample data for benchmarks
MINIMAL_PASSPORT_DATA = {
    "id": "https://example.com/dpp/12345",
    "issuer": {
        "id": "https://example.com/issuer",
        "name": "Test Issuer",
    },
}

FULL_PASSPORT_DATA = {
    "id": "https://example.com/dpp/12345",
    "type": ["DigitalProductPassport", "VerifiableCredential"],
    "issuer": {
        "id": "https://example.com/issuer",
        "name": "Test Issuer Corp",
    },
    "credentialSubject": {
        "id": "https://example.com/product/abc",
        "product": {
            "id": "https://example.com/product/abc",
            "name": "Test Product",
            "description": "A test product for benchmarking purposes",
        },
    },
}

INVALID_PASSPORT_DATA = {
    "invalid_field": "value",
    "another": 123,
}


class ValidationBenchmarks:
    """Benchmarks for ValidationEngine."""

    def __init__(self, iterations: int = 1000):
        self.iterations = iterations
        self.engine_model = ValidationEngine(layers=["model"])
        self.engine_semantic = ValidationEngine(layers=["semantic"])
        self.engine_all = ValidationEngine(layers=["model", "semantic"])

    def bench_model_validation_minimal(self) -> BenchmarkResult:
        """Benchmark model validation with minimal passport."""
        return run_benchmark(
            "Model Validation (Minimal)",
            lambda: self.engine_model.validate(MINIMAL_PASSPORT_DATA),
            self.iterations,
        )

    def bench_model_validation_full(self) -> BenchmarkResult:
        """Benchmark model validation with full passport."""
        return run_benchmark(
            "Model Validation (Full)",
            lambda: self.engine_model.validate(FULL_PASSPORT_DATA),
            self.iterations,
        )

    def bench_model_validation_invalid(self) -> BenchmarkResult:
        """Benchmark model validation with invalid data."""
        return run_benchmark(
            "Model Validation (Invalid)",
            lambda: self.engine_model.validate(INVALID_PASSPORT_DATA),
            self.iterations,
        )

    def bench_semantic_validation(self) -> BenchmarkResult:
        """Benchmark semantic validation."""
        # Create a valid passport object for semantic validation
        passport = DigitalProductPassport(
            id="https://example.com/dpp",
            issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
        )
        return run_benchmark(
            "Semantic Validation",
            lambda: self.engine_semantic.validate(passport.model_dump(by_alias=True)),
            self.iterations,
        )

    def bench_full_validation(self) -> BenchmarkResult:
        """Benchmark full validation pipeline."""
        return run_benchmark(
            "Full Validation (Model + Semantic)",
            lambda: self.engine_all.validate(MINIMAL_PASSPORT_DATA),
            self.iterations,
        )

    def bench_engine_creation(self) -> BenchmarkResult:
        """Benchmark engine creation overhead."""
        return run_benchmark(
            "Engine Creation",
            lambda: ValidationEngine(layers=["model", "semantic"]),
            self.iterations,
        )

    def run_all(self) -> list[BenchmarkResult]:
        """Run all validation benchmarks."""
        return [
            self.bench_model_validation_minimal(),
            self.bench_model_validation_full(),
            self.bench_model_validation_invalid(),
            self.bench_semantic_validation(),
            self.bench_full_validation(),
            self.bench_engine_creation(),
        ]


def main():
    """Run validation benchmarks."""
    print("=" * 60)
    print("Validation Engine Benchmarks")
    print("=" * 60)

    benchmarks = ValidationBenchmarks(iterations=1000)
    results = benchmarks.run_all()

    for result in results:
        print()
        print(result)

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
