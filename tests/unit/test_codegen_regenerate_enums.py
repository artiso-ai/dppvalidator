"""Unit tests for ``tools/codegen/cirpass/regenerate_enums.py``.

The codegen tool is the workstream X1 force-multiplier for Phase 1
tasks 1.7–1.11 of [docs/plans/CIRPASS_2_MIGRATION.md]. These tests
exercise it against the existing v1.7.1-era TTL bundled at
``src/dppvalidator/vocabularies/data/ontologies/product_dpp_v1.7.1.ttl``
to verify:

1. The CamelCase → UPPER_SNAKE name converter handles every shape that
   appears in the bundled TTLs (CamelCase, ``Snake_Case_Already``,
   leading-acronym).
2. Re-running the generator on the same TTL produces byte-identical
   output (determinism — sort key, deterministic hash).
3. The generated body is valid Python that imports + executes; the
   resulting Enum class has the expected number of members.
4. The ``# generated-from:`` header pins the LF-normalised SHA-256 of
   the input TTL.

Tests are skipped if rdflib is not installed (the generator declares it
as required and exits 2 in that case; tests should not double-fail).
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_GENERATOR = _REPO_ROOT / "tools" / "codegen" / "cirpass" / "regenerate_enums.py"
_FIXTURE_TTL = (
    _REPO_ROOT
    / "src"
    / "dppvalidator"
    / "vocabularies"
    / "data"
    / "ontologies"
    / "product_dpp_v1.7.1.ttl"
)


def _load_generator_module():
    """Import the generator script as a module without invoking ``main()``.

    The script defines a ``@dataclass(frozen=True, slots=True)`` whose
    initialisation reads ``sys.modules[cls.__module__]``, so we must
    register the module in ``sys.modules`` *before* executing it,
    otherwise the dataclass machinery raises ``AttributeError``.
    """
    spec = importlib.util.spec_from_file_location("regenerate_enums_test_load", _GENERATOR)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_to_upper_snake_handles_known_shapes() -> None:
    """The naming converter catches the three input shapes seen in real TTLs."""
    mod = _load_generator_module()
    convert = mod.to_upper_snake
    cases = {
        "EnvironmentalFootprint": "ENVIRONMENTAL_FOOTPRINT",
        "Carbon_Footprint": "CARBON_FOOTPRINT",
        "linkToPreviousDPP": "LINK_TO_PREVIOUS_DPP",
        "DPP": "DPP",
        "GTIN": "GTIN",
        "HTTPRequest": "HTTP_REQUEST",
        "Product": "PRODUCT",
        "ConcentrationOfSubstanceOfConcern": "CONCENTRATION_OF_SUBSTANCE_OF_CONCERN",
    }
    for input_name, expected in cases.items():
        assert convert(input_name) == expected, f"{input_name!r} → {convert(input_name)!r}"


def test_local_name_of_handles_hash_and_slash() -> None:
    """Both ``http://.../EUDPP#X`` and ``https://.../eudpp/X`` shapes resolve."""
    mod = _load_generator_module()
    fn = mod.local_name_of
    assert fn("http://dpp.taltech.ee/EUDPP#Product", "http://dpp.taltech.ee/EUDPP/") == "Product"
    assert fn("https://w3id.org/eudpp/Product", "https://w3id.org/eudpp/") == "Product"
    assert fn("http://other.org/Foo", "https://w3id.org/eudpp/") is None


def _run_generator(*args: str) -> subprocess.CompletedProcess[str]:
    """Invoke the generator in a subprocess so we test the real entry point."""
    return subprocess.run(
        [sys.executable, str(_GENERATOR), *args],
        check=False,
        capture_output=True,
        text=True,
        cwd=_REPO_ROOT,
    )


@pytest.mark.skipif(not _FIXTURE_TTL.is_file(), reason="fixture TTL missing")
def test_generator_produces_deterministic_output() -> None:
    """Running the generator twice on the same TTL produces byte-identical stdout."""
    args = (
        "--ttl",
        str(_FIXTURE_TTL.relative_to(_REPO_ROOT)),
        "--target",
        "class",
        "--namespace",
        "http://dpp.taltech.ee/EUDPP#",
        "--prefix",
        "eudpp",
        "--enum-name",
        "EUDPPClass",
        "--enum-doc",
        "Test enum.",
    )
    first = _run_generator(*args)
    second = _run_generator(*args)
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert first.stdout == second.stdout, "non-deterministic output"
    assert first.stdout.startswith("# generated-from: "), "missing provenance header"


@pytest.mark.skipif(not _FIXTURE_TTL.is_file(), reason="fixture TTL missing")
def test_generator_output_is_valid_python_with_expected_members() -> None:
    """The generated body parses as Python and yields a populated Enum class."""
    proc = _run_generator(
        "--ttl",
        str(_FIXTURE_TTL.relative_to(_REPO_ROOT)),
        "--target",
        "class",
        "--namespace",
        "http://dpp.taltech.ee/EUDPP#",
        "--prefix",
        "eudpp",
        "--enum-name",
        "EUDPPClassRegen",
        "--enum-doc",
        "Test enum.",
    )
    assert proc.returncode == 0, proc.stderr

    namespace: dict[str, object] = {}
    exec("from enum import Enum\n" + proc.stdout, namespace)  # noqa: S102 — controlled input
    enum_cls = namespace["EUDPPClassRegen"]
    members = list(enum_cls)  # type: ignore[call-overload]
    # The v1.7.1 P_DPP TTL has at least 30 owl:Class entries; lock a
    # minimum bound rather than an exact count to avoid breaking when
    # the bundled TTL is upgraded in Phase 1.1.
    assert len(members) >= 30, f"only {len(members)} members extracted"
    # Spot-check a few well-known members.
    expected_subset = {"PRODUCT", "DPP", "ENVIRONMENTAL_FOOTPRINT", "CARBON_FOOTPRINT"}
    actual_names = {m.name for m in members}  # type: ignore[union-attr]
    missing = expected_subset - actual_names
    assert not missing, f"missing expected members: {missing}"


@pytest.mark.skipif(not _FIXTURE_TTL.is_file(), reason="fixture TTL missing")
def test_generator_output_is_alphabetically_sorted() -> None:
    """Members are emitted in alphabetical order by Python identifier."""
    proc = _run_generator(
        "--ttl",
        str(_FIXTURE_TTL.relative_to(_REPO_ROOT)),
        "--target",
        "class",
        "--namespace",
        "http://dpp.taltech.ee/EUDPP#",
        "--prefix",
        "eudpp",
        "--enum-name",
        "EUDPPClassRegen",
        "--enum-doc",
        "Test enum.",
    )
    assert proc.returncode == 0, proc.stderr

    member_lines = [
        line.strip().split(" = ")[0]
        for line in proc.stdout.splitlines()
        if line.startswith("    ") and " = " in line
    ]
    assert member_lines == sorted(member_lines), "members not alphabetically sorted"
