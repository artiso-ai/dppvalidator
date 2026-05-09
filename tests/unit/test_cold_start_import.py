"""Phase 3 task 3.14 — ``import dppvalidator`` does not eagerly load CIRPASS.

Cross-cutting workstream X3 (cold-start budget) requires that
importing the top-level package not pull the CIRPASS reference-
structure surface eagerly. CIRPASS classes are large enough that
adding them to the eager-import set would noticeably regress the
cold-start time for UNTP-only consumers.

The test runs ``import dppvalidator`` in a fresh subprocess (so
prior test imports don't pollute ``sys.modules``) and asserts that
``dppvalidator.models.cirpass`` did *not* land in ``sys.modules``.
"""

from __future__ import annotations

import subprocess
import sys

# The set of submodules that must NOT load on a bare ``import
# dppvalidator``. Add new entries here when a new family / pilot
# package lands and should follow the same lazy-import rule.
_FORBIDDEN_EAGER_IMPORTS = (
    "dppvalidator.models.cirpass",
    "dppvalidator.models.cirpass.v1_3",
)


def test_top_level_import_does_not_load_cirpass() -> None:
    """A fresh ``import dppvalidator`` leaves ``models.cirpass`` unloaded.

    Running in a subprocess ensures we get a clean ``sys.modules`` —
    pytest's collection earlier in this run may have imported the
    CIRPASS package via ``test_models_cirpass_v1_3``, but the cold-
    start contract is about *first* import in a fresh interpreter.
    """
    code = (
        "import sys; "
        "import dppvalidator; "
        "loaded = sorted(m for m in sys.modules "
        "if m.startswith('dppvalidator.models.cirpass')); "
        "print('|'.join(loaded))"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
    )
    eagerly_loaded = [m for m in proc.stdout.strip().split("|") if m]
    assert not eagerly_loaded, (
        f"``import dppvalidator`` eagerly loaded the CIRPASS surface: "
        f"{eagerly_loaded}. Cross-cutting workstream X3 (cold-start "
        f"budget) requires this to be lazy. Check "
        f"``src/dppvalidator/models/__init__.py`` and any other "
        f"entry-point that may have re-exported CIRPASS classes."
    )


def test_explicit_cirpass_import_works() -> None:
    """The lazy-import contract doesn't *prevent* the import — it just
    requires explicit caller intent.
    """
    code = (
        "from dppvalidator.models.cirpass.v1_3 import ReferencePassport; "
        "print(ReferencePassport.__name__)"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
    )
    assert proc.stdout.strip() == "ReferencePassport"


def test_top_level_import_loads_untp_models() -> None:
    """The lazy-CIRPASS contract does *not* affect the UNTP eager
    re-export surface — those remain accessible from the top-level
    ``dppvalidator.models`` (back-compat for every UNTP caller).
    """
    code = (
        "import dppvalidator.models as m; "
        "names = sorted(n for n in dir(m) "
        "if n in {'DigitalProductPassport', 'Product', 'Material'}); "
        "print('|'.join(names))"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
    )
    expected = "DigitalProductPassport|Material|Product"
    assert proc.stdout.strip() == expected, (
        f"Expected UNTP eager re-exports {expected!r}, got {proc.stdout.strip()!r}"
    )


def test_forbidden_eager_imports_list_is_complete() -> None:
    """Pin the forbidden-imports list against accidental thinning.

    Any addition to ``models/cirpass/`` that's exposed at module
    level should be in :data:`_FORBIDDEN_EAGER_IMPORTS` so a bare
    ``import dppvalidator`` doesn't start pulling it eagerly.
    """
    assert "dppvalidator.models.cirpass" in _FORBIDDEN_EAGER_IMPORTS
    assert "dppvalidator.models.cirpass.v1_3" in _FORBIDDEN_EAGER_IMPORTS
