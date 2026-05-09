"""Phase 1 audit gate: EUDPP-LD output for the canonical v0.7 fixture is bit-stable.

Phase 1 / third exit criterion in
[`docs/plans/CIRPASS_2_MIGRATION.md`](../../docs/plans/CIRPASS_2_MIGRATION.md):

> Golden EUDPP-LD diff approved by reviewer.

This test runs the canonical v0.7 UNTP DPP fixture through
:func:`dppvalidator.exporters.eudpp_jsonld.export_eudpp_jsonld_dict`
and compares the result against a committed snapshot. When the
snapshot is missing (first run after a Phase 1 namespace bump or term
rename), the test writes it and fails — the maintainer reviews the
fresh output predicate-by-predicate and re-runs.

Snapshot location:
``tests/fixtures/golden/eudpp_ld_export__untp_v0_7.json``.

What the gate covers
--------------------

The EUDPP-LD output is the highest-leverage observable Phase 1
behaviour: every Phase 1.4 namespace rebase, Phase 1.6 term-mapping
audit, and Phase 1.7–1.11 enum regen surfaces here. A predicate-by-
predicate review of the snapshot diff is what flips the third Phase 1
exit-criterion box to ``[x]``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dppvalidator.exporters.eudpp_jsonld import export_eudpp_jsonld_dict
from dppvalidator.models.v0_7 import DigitalProductPassport as DigitalProductPassportV07

_REPO_ROOT = Path(__file__).resolve().parents[2]
_FIXTURE = _REPO_ROOT / "tests" / "fixtures" / "valid" / "untp-dpp-instance-0.7.0.json"
_SNAPSHOT = _REPO_ROOT / "tests" / "fixtures" / "golden" / "eudpp_ld_export__untp_v0_7.json"


def _load_fixture() -> DigitalProductPassportV07:
    """Parse the canonical v0.7 fixture into a Pydantic model."""
    raw = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    return DigitalProductPassportV07.model_validate(raw)


def _write_snapshot_for_review(snapshot: dict) -> None:
    """Capture the current output as the new golden snapshot."""
    _SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    _SNAPSHOT.write_text(
        json.dumps(snapshot, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def test_eudpp_ld_export_matches_golden_snapshot() -> None:
    """The EUDPP-LD export of the canonical v0.7 fixture is bit-stable.

    On first run (or after an intentional Phase 1.x change to namespace
    / term mapping / enum content), the snapshot file is missing —
    the test writes it and fails so the maintainer reviews the diff
    via ``git diff`` predicate-by-predicate before re-running.
    """
    passport = _load_fixture()
    # ``export_eudpp_jsonld_dict`` is typed against the v0.6
    # ``DigitalProductPassport`` shim but accepts the v0.7 model at
    # runtime via duck-typing. Phase 1 task 1.13 wired up the
    # canonical-IRI emission for both shapes.
    actual = export_eudpp_jsonld_dict(passport)  # ty: ignore[invalid-argument-type]

    # Stable serialisation for diff: sort keys, indent=2.
    actual_normalised = json.loads(json.dumps(actual, sort_keys=True))

    if not _SNAPSHOT.is_file():
        _write_snapshot_for_review(actual_normalised)
        pytest.fail(
            f"Wrote new EUDPP-LD golden snapshot at {_SNAPSHOT.relative_to(_REPO_ROOT)}; "
            f"review the file (predicate-by-predicate) and re-run the test. "
            f"This is the Phase 1 third-exit-criterion audit gate — sign-off "
            f"by a reviewer flips the criterion to [x] in "
            f"docs/plans/CIRPASS_2_MIGRATION.md."
        )

    expected = json.loads(_SNAPSHOT.read_text(encoding="utf-8"))
    if actual_normalised != expected:
        # Render a human-readable diff hint without dumping the entire
        # 100-line JSON to the assertion message.
        actual_keys = set(json.dumps(actual_normalised, sort_keys=True).split('"'))
        expected_keys = set(json.dumps(expected, sort_keys=True).split('"'))
        new_tokens = sorted(actual_keys - expected_keys)[:20]
        gone_tokens = sorted(expected_keys - actual_keys)[:20]
        pytest.fail(
            "EUDPP-LD export drifted from the golden snapshot.\n"
            f"  golden: {_SNAPSHOT.relative_to(_REPO_ROOT)}\n"
            f"  fixture: {_FIXTURE.relative_to(_REPO_ROOT)}\n"
            f"  + tokens (sample): {new_tokens}\n"
            f"  − tokens (sample): {gone_tokens}\n"
            "If the change is intentional, re-capture the snapshot by deleting "
            "it and re-running this test."
        )


def test_canonical_iri_emission() -> None:
    """Every emitted EUDPP IRI in the export uses the canonical W3ID prefix.

    Phase 1.4 + 1.13 cardinal: emitted predicate IRIs live under
    ``https://w3id.org/eudpp#`` (term namespace), never under the
    legacy per-publisher hosts. This test runs orthogonally to the
    golden-diff gate — it catches IRI regressions even when the
    snapshot was last captured before the rebase landed.
    """
    passport = _load_fixture()
    payload = json.dumps(export_eudpp_jsonld_dict(passport))  # ty: ignore[invalid-argument-type]

    # Legacy hosts must not appear anywhere in the export.
    for legacy in ("dpp.taltech.ee", "dpp.cea.fr"):
        assert legacy not in payload, (
            f"Found legacy EUDPP host {legacy!r} in exported JSON-LD. "
            f"Phase 1.4 rebased these onto https://w3id.org/eudpp/."
        )
