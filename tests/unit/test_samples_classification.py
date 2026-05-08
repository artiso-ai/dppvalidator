"""Phase 5: pinned version detection on the vendored real-world samples.

The Phase 5 plan calls for re-running ``scripts/fetch_dpp_samples.py``
and regenerating ``tests/fixtures/samples_report.md`` to confirm the
new detection logic classifies samples correctly. The fetch step is
network-bound; this module is the durable, offline form of the
"verify detection still works" check.

It walks every sample under ``tests/fixtures/samples/``, asks
:func:`detect_schema_version` what version it thinks the payload is,
and asserts the answer is one registered in ``SCHEMA_REGISTRY``. The
specific classification per sample is also asserted against a pinned
expectation map so a regression in URL-pattern detection trips the
suite immediately.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dppvalidator.schemas.registry import SCHEMA_REGISTRY
from dppvalidator.validators.detection import detect_schema_version

_SAMPLES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "samples"


# Pinned classifications for the currently-vendored samples. Adding a
# new sample to ``tests/fixtures/samples/`` requires extending this map
# (or marking the file as not-applicable in
# ``_NOT_DPP_SAMPLES`` below).
_EXPECTED_VERSIONS: dict[str, str] = {
    "BatteryPassDataModel_BatteryPass_GeneralProductInformation-payload.json": "0.6.1",
    "batterypass_BatteryPassDataModel_CarbonFootprintForBatteries-ld.json": "0.6.1",
    "batterypass_BatteryPassDataModel_Circularity-ld.json": "0.6.1",
    "batterypass_BatteryPassDataModel_GeneralProductInformation-ld.json": "0.6.1",
    "batterypass_BatteryPassDataModel_MaterialComposition-ld.json": "0.6.1",
    "eclipse-tractusx_sldt-semantic-models_BatteryPass.json": "0.6.1",
    "nfc-forum_org_long-dpp-example.json": "0.6.1",
    "opensource_unicc_org_untp-digital-facility-record-v0.3.9.json": "0.6.1",
    "opensource_unicc_org_untp-digital-product-passport-v0.3.10.json": "0.6.1",
    "schemas_testing_breathable-t-shirt.json": "0.6.1",
    "test_uncefact_org_DigitalIdentityAnchor-instance-0.6.1.json": "0.6.1",
    "test_uncefact_org_untp-dpp-instance-0.6.0.json": "0.6.0",
    "untp-verifiable-credentials_s3_amazonaws_com_bc075c5f-2304-4b3f-bb24-46d9fa9a8e60.json": "0.6.0",
}


def _sample_files() -> list[Path]:
    """All sample files currently vendored for the detection test."""
    return sorted(_SAMPLES_DIR.glob("*.json"))


@pytest.mark.parametrize(
    "sample_path",
    _sample_files(),
    ids=lambda p: p.name,
)
def test_sample_detects_to_known_version(sample_path: Path) -> None:
    """Every sample must classify to a version present in the registry.

    A regression here means either:
    - The detection regex no longer matches a URL it used to.
    - A sample file's contents drifted (in which case re-pull it).
    """
    data = json.loads(sample_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{sample_path.name} is not a JSON object"
    detected = detect_schema_version(data)
    assert detected in SCHEMA_REGISTRY, (
        f"{sample_path.name} detected as {detected!r}, which is not in "
        f"SCHEMA_REGISTRY ({list(SCHEMA_REGISTRY)!r})."
    )


@pytest.mark.parametrize(
    ("sample_path", "expected"),
    [(_SAMPLES_DIR / name, version) for name, version in _EXPECTED_VERSIONS.items()],
    ids=lambda val: val.name if isinstance(val, Path) else str(val),
)
def test_sample_pinned_classification(sample_path: Path, expected: str) -> None:
    """Each sample's detected version matches the pinned expectation."""
    if not sample_path.is_file():
        pytest.skip(f"sample no longer present: {sample_path.name}")
    data = json.loads(sample_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    detected = detect_schema_version(data)
    assert detected == expected, (
        f"{sample_path.name}: expected {expected!r}, got {detected!r}. "
        "Either the sample contents drifted or the detection regex changed; "
        "update the pinned expectation if this is intentional."
    )


def test_every_sample_has_pinned_expectation() -> None:
    """Drift catch: adding a sample without updating the pinned map fails.

    Without this check, a new sample could land with whatever
    classification the detection happens to give it, masking a real
    regression on existing samples.
    """
    on_disk = {p.name for p in _sample_files()}
    pinned = set(_EXPECTED_VERSIONS.keys())
    new_samples = on_disk - pinned
    assert not new_samples, (
        f"Vendored sample(s) without pinned classification: "
        f"{sorted(new_samples)}.\n"
        "Add them to _EXPECTED_VERSIONS in this file with the version "
        "they should detect to."
    )
