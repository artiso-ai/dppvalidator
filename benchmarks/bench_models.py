"""Benchmarks for model operations."""

from benchmarks.bench_validation import BenchmarkResult, run_benchmark
from dppvalidator.exporters import JSONExporter, JSONLDExporter
from dppvalidator.models import CredentialIssuer, DigitalProductPassport, Measure, Product

# Pre-create objects for benchmarks
PASSPORT = DigitalProductPassport(
    id="https://example.com/dpp/12345",
    issuer=CredentialIssuer(
        id="https://example.com/issuer",
        name="Test Issuer Corp",
    ),
)

PASSPORT_DATA = {
    "id": "https://example.com/dpp/12345",
    "issuer": {
        "id": "https://example.com/issuer",
        "name": "Test Issuer Corp",
    },
}


class ModelBenchmarks:
    """Benchmarks for Pydantic model operations."""

    def __init__(self, iterations: int = 1000):
        self.iterations = iterations

    def bench_passport_creation(self) -> BenchmarkResult:
        """Benchmark passport model creation."""
        return run_benchmark(
            "Passport Creation",
            lambda: DigitalProductPassport(
                id="https://example.com/dpp",
                issuer=CredentialIssuer(id="https://example.com/issuer", name="Test"),
            ),
            self.iterations,
        )

    def bench_passport_validation(self) -> BenchmarkResult:
        """Benchmark passport model validation from dict."""
        return run_benchmark(
            "Passport Validation (from dict)",
            lambda: DigitalProductPassport.model_validate(PASSPORT_DATA),
            self.iterations,
        )

    def bench_passport_dump(self) -> BenchmarkResult:
        """Benchmark passport model dump to dict."""
        return run_benchmark(
            "Passport Dump (to dict)",
            lambda: PASSPORT.model_dump(by_alias=True),
            self.iterations,
        )

    def bench_passport_dump_json(self) -> BenchmarkResult:
        """Benchmark passport model dump to JSON string."""
        return run_benchmark(
            "Passport Dump (to JSON)",
            lambda: PASSPORT.model_dump_json(by_alias=True),
            self.iterations,
        )

    def bench_measure_creation(self) -> BenchmarkResult:
        """Benchmark measure creation."""
        return run_benchmark(
            "Measure Creation",
            lambda: Measure(value=42.5, unit="KGM"),
            self.iterations,
        )

    def bench_product_creation(self) -> BenchmarkResult:
        """Benchmark product creation."""
        return run_benchmark(
            "Product Creation",
            lambda: Product(
                id="https://example.com/product",
                name="Test Product",
                description="A test product",
            ),
            self.iterations,
        )

    def run_all(self) -> list[BenchmarkResult]:
        """Run all model benchmarks."""
        return [
            self.bench_passport_creation(),
            self.bench_passport_validation(),
            self.bench_passport_dump(),
            self.bench_passport_dump_json(),
            self.bench_measure_creation(),
            self.bench_product_creation(),
        ]


class ExporterBenchmarks:
    """Benchmarks for exporter operations."""

    def __init__(self, iterations: int = 1000):
        self.iterations = iterations
        self.json_exporter = JSONExporter()
        self.jsonld_exporter = JSONLDExporter()

    def bench_json_export(self) -> BenchmarkResult:
        """Benchmark JSON export."""
        return run_benchmark(
            "JSON Export",
            lambda: self.json_exporter.export(PASSPORT),
            self.iterations,
        )

    def bench_jsonld_export(self) -> BenchmarkResult:
        """Benchmark JSON-LD export."""
        return run_benchmark(
            "JSON-LD Export",
            lambda: self.jsonld_exporter.export(PASSPORT),
            self.iterations,
        )

    def run_all(self) -> list[BenchmarkResult]:
        """Run all exporter benchmarks."""
        return [
            self.bench_json_export(),
            self.bench_jsonld_export(),
        ]


def main():
    """Run model and exporter benchmarks."""
    print("=" * 60)
    print("Model Benchmarks")
    print("=" * 60)

    model_benchmarks = ModelBenchmarks(iterations=1000)
    for result in model_benchmarks.run_all():
        print()
        print(result)

    print()
    print("=" * 60)
    print("Exporter Benchmarks")
    print("=" * 60)

    exporter_benchmarks = ExporterBenchmarks(iterations=1000)
    for result in exporter_benchmarks.run_all():
        print()
        print(result)

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
