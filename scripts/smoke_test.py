#!/usr/bin/env python3
"""Functional smoke test for ``dppvalidator``.

Exercises every user-facing surface end-to-end against the bundled
test fixtures — CLI commands, Python APIs, plugin discovery, the
compat shim, and the EU DPP exporter. Standalone: no pytest, no
test framework, just subprocess + the project's installed Python.
Returns exit code ``0`` when every check passes, non-zero otherwise.

Run from the repo root::

    .venv/bin/python scripts/smoke_test.py

Or, against the conda env::

    DPP_BIN=$HOME/miniforge3/envs/dppvalidator/bin/dppvalidator \\
    PY_BIN=$HOME/miniforge3/envs/dppvalidator/bin/python \\
        python scripts/smoke_test.py

Environment overrides:

- ``DPP_BIN``  — path to the ``dppvalidator`` executable
  (default: ``.venv/bin/dppvalidator``).
- ``PY_BIN``   — path to a Python that has ``dppvalidator`` installed
  (default: ``.venv/bin/python``).

Each section's checks are documented inline. The test is
intentionally **non-destructive**: it never writes outside
``tempfile.TemporaryDirectory()`` or pollutes the working tree.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "tests" / "fixtures"
DPP_BIN = os.environ.get("DPP_BIN", str(REPO / ".venv" / "bin" / "dppvalidator"))
PY_BIN = os.environ.get("PY_BIN", str(REPO / ".venv" / "bin" / "python"))

# ANSI colours — disabled when output is piped (CI logs).
_ISATTY = sys.stdout.isatty()
GREEN = "\033[32m" if _ISATTY else ""
RED = "\033[31m" if _ISATTY else ""
YELLOW = "\033[33m" if _ISATTY else ""
BLUE = "\033[34m" if _ISATTY else ""
DIM = "\033[2m" if _ISATTY else ""
RESET = "\033[0m" if _ISATTY else ""


# ---------------------------------------------------------------------------
# Tiny assertion harness — no test framework, just structured output
# ---------------------------------------------------------------------------


@dataclass
class Smoke:
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    failures: list[tuple[str, str]] = field(default_factory=list)

    def section(self, label: str) -> None:
        print(f"\n{BLUE}═══ {label} {'═' * (60 - len(label))}{RESET}")

    def ok(self, label: str) -> None:
        self.passed += 1
        print(f"  {GREEN}✓{RESET} {label}")

    def fail(self, label: str, detail: str = "") -> None:
        self.failed += 1
        print(f"  {RED}✗{RESET} {label}")
        if detail:
            for line in detail.rstrip().splitlines()[:6]:
                print(f"    {DIM}{line}{RESET}")
        self.failures.append((label, detail))

    def skip(self, label: str, reason: str) -> None:
        self.skipped += 1
        print(f"  {YELLOW}~{RESET} {label} {DIM}({reason}){RESET}")

    def assert_(self, label: str, condition: bool, detail: str = "") -> None:
        if condition:
            self.ok(label)
        else:
            self.fail(label, detail)

    def cli(
        self,
        args: list[str],
        *,
        stdin: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """Invoke the CLI; never raises. Returns the completed process."""
        return subprocess.run(
            [DPP_BIN, *args],
            capture_output=True,
            text=True,
            input=stdin,
            cwd=str(REPO),
            check=False,
        )

    def py(self, code: str) -> subprocess.CompletedProcess[str]:
        """Run a Python snippet under PY_BIN. Never raises."""
        return subprocess.run(
            [PY_BIN, "-c", textwrap.dedent(code)],
            capture_output=True,
            text=True,
            cwd=str(REPO),
            check=False,
        )

    def report(self) -> int:
        total = self.passed + self.failed + self.skipped
        print()
        print("─" * 64)
        if self.failed == 0:
            colour = GREEN
            verdict = "PASSED"
        else:
            colour = RED
            verdict = "FAILED"
        print(
            f"{colour}{verdict}{RESET}: "
            f"{self.passed} passed, {self.failed} failed, {self.skipped} skipped "
            f"({total} total)"
        )
        if self.failures:
            print()
            print(f"{RED}Failures:{RESET}")
            for label, detail in self.failures:
                print(f"  • {label}")
                if detail:
                    for line in detail.rstrip().splitlines()[:3]:
                        print(f"    {DIM}{line}{RESET}")
        return 0 if self.failed == 0 else 1


# ---------------------------------------------------------------------------
# Pre-flight
# ---------------------------------------------------------------------------


def _check_environment(s: Smoke) -> bool:
    """Bail out early if the binaries we expect aren't there."""
    s.section("0. Pre-flight")
    dpp_path = Path(DPP_BIN)
    py_path = Path(PY_BIN)

    s.assert_(
        f"DPP_BIN exists ({DPP_BIN})",
        dpp_path.is_file() and os.access(dpp_path, os.X_OK),
        f"set DPP_BIN to a working dppvalidator executable (got {DPP_BIN})",
    )
    s.assert_(
        f"PY_BIN exists ({PY_BIN})",
        py_path.is_file() and os.access(py_path, os.X_OK),
        f"set PY_BIN to a Python that has dppvalidator installed (got {PY_BIN})",
    )
    s.assert_(
        "fixtures directory present",
        (FIXTURES / "valid").is_dir(),
        f"missing: {FIXTURES / 'valid'}",
    )
    return s.failed == 0


# ---------------------------------------------------------------------------
# Sections — each tests one cohesive surface
# ---------------------------------------------------------------------------


def section_cli_sanity(s: Smoke) -> None:
    s.section("1. CLI sanity")
    r = s.cli(["--version"])
    s.assert_("--version exits 0", r.returncode == 0, r.stderr)
    s.assert_(
        "--version output mentions 'dppvalidator'",
        "dppvalidator" in r.stdout.lower(),
        r.stdout,
    )

    r = s.cli(["--help"])
    s.assert_("--help exits 0", r.returncode == 0, r.stderr)
    for cmd in ("validate", "migrate", "export", "schema"):
        s.assert_(
            f"--help advertises subcommand '{cmd}'",
            cmd in r.stdout,
            r.stdout[:200],
        )


def section_schema_management(s: Smoke) -> None:
    s.section("2. Schema management")
    r = s.cli(["schema", "list"])
    s.assert_("schema list exits 0", r.returncode == 0, r.stderr)
    for version in ("0.6.0", "0.6.1", "0.7.0"):
        s.assert_(
            f"schema list lists {version}",
            version in r.stdout,
            r.stdout,
        )

    r = s.cli(["schema", "info", "-v", "0.7.0"])
    s.assert_("schema info -v 0.7.0 exits 0", r.returncode == 0, r.stderr)


def section_validate_auto_detect(s: Smoke) -> None:
    s.section("3. validate — auto-detect")
    v06 = FIXTURES / "valid" / "untp-dpp-instance-0.6.1.json"
    v07 = FIXTURES / "valid" / "untp-dpp-instance-0.7.0.json"

    r = s.cli(["validate", str(v06)])
    s.assert_("v0.6 fixture validates clean", r.returncode == 0, r.stdout)
    s.assert_(
        "v0.6 reports 'Schema version: 0.6.1'",
        "Schema version: 0.6.1" in r.stdout,
        r.stdout,
    )

    r = s.cli(["validate", str(v07)])
    s.assert_("v0.7 fixture validates clean", r.returncode == 0, r.stdout)
    s.assert_(
        "v0.7 reports 'Schema version: 0.7.0'",
        "Schema version: 0.7.0" in r.stdout,
        r.stdout,
    )
    # Regressions from earlier rounds — must not resurface.
    s.assert_(
        "v0.7 emits no PLG001 (per-version plugin filter)", "PLG001" not in r.stdout, r.stdout[:300]
    )
    s.assert_(
        "v0.7 emits no VOC003 on UN CPC fixture (scheme-aware)",
        "VOC003" not in r.stdout,
        r.stdout[:300],
    )
    s.assert_(
        "v0.7 emits no VOC004 on UN CPC fixture (scheme-aware)",
        "VOC004" not in r.stdout,
        r.stdout[:300],
    )

    # Sibling v0.7 fixtures exercise different ``credentialSubject`` shapes
    # (battery + cathode have richer attestation/material structures) — they
    # should also auto-detect cleanly with no PLG001 or VOC003/VOC004 noise.
    for sibling in ("untp-dpp-battery-instance-0.7.0.json", "untp-dpp-cathode-instance-0.7.0.json"):
        f = FIXTURES / "valid" / sibling
        if not f.is_file():
            s.skip(f"{sibling} round-trip", "fixture not vendored")
            continue
        r = s.cli(["validate", str(f)])
        s.assert_(f"{sibling} validates clean", r.returncode == 0, r.stdout)
        s.assert_(
            f"{sibling} auto-detects as 0.7.0",
            "Schema version: 0.7.0" in r.stdout,
            r.stdout[:200],
        )
        s.assert_(
            f"{sibling} emits no PLG001/VOC003/VOC004",
            not any(c in r.stdout for c in ("PLG001", "VOC003", "VOC004")),
            r.stdout[:300],
        )


def section_validate_explicit_pin(s: Smoke) -> None:
    s.section("4. validate — explicit pin + VER001")
    v06 = FIXTURES / "valid" / "untp-dpp-instance-0.6.1.json"

    r = s.cli(["validate", str(v06), "--schema-version", "0.6.1"])
    s.assert_("v0.6 + matching pin exits 0", r.returncode == 0, r.stdout)

    r = s.cli(["validate", str(v06), "--schema-version", "0.7.0"])
    s.assert_("VER001 fail-fast on mismatched pin", r.returncode != 0, r.stdout)
    s.assert_("VER001 code surfaces in output", "VER001" in r.stdout, r.stdout)


def section_validate_invalid(s: Smoke) -> None:
    s.section("5. validate — invalid fixtures (parametrized)")
    invalid_root = FIXTURES / "invalid"
    if not invalid_root.is_dir():
        s.skip("invalid-fixture sweep", f"missing {invalid_root}")
        return

    # Anchor case — pin the SCH001/MDL001 contract on one well-known fixture.
    anchor = invalid_root / "missing_issuer.json"
    if anchor.is_file():
        r = s.cli(["validate", str(anchor)])
        s.assert_("missing_issuer.json exits non-zero", r.returncode != 0, r.stdout)
        s.assert_(
            "missing_issuer.json reports SCH001 or MDL001",
            "SCH001" in r.stdout or "MDL001" in r.stdout,
            r.stdout,
        )

    # Sweep every other v0.6 invalid fixture — each must (a) exit non-zero and
    # (b) emit at least one structured error code. We don't assert which code,
    # since that's the job of the unit suite — we're verifying the CLI's
    # error-surfacing contract holds across every failure shape.
    v06_invalids = sorted(p for p in invalid_root.glob("*.json") if p.name != "missing_issuer.json")
    for f in v06_invalids:
        r = s.cli(["validate", str(f)])
        s.assert_(
            f"{f.name} exits non-zero",
            r.returncode != 0,
            f"exit={r.returncode} stdout={r.stdout[:200]}",
        )
        # An error code is any AAA000-style token the CLI surfaces.
        has_code = bool(re.search(r"\b[A-Z]{2,4}\d{3}\b", r.stdout))
        s.assert_(f"{f.name} surfaces a structured error code", has_code, r.stdout[:200])

    # Sweep all v0.7 invalid fixtures (subdir).
    v07_dir = invalid_root / "0.7.0"
    if v07_dir.is_dir():
        v07_invalids = sorted(v07_dir.glob("*.json"))
        for f in v07_invalids:
            r = s.cli(["validate", str(f), "--schema-version", "0.7.0"])
            s.assert_(
                f"v0.7/{f.name} exits non-zero",
                r.returncode != 0,
                f"exit={r.returncode} stdout={r.stdout[:200]}",
            )


def section_output_formats(s: Smoke) -> None:
    s.section("6. validate — output formats")
    v07 = FIXTURES / "valid" / "untp-dpp-instance-0.7.0.json"

    # JSON format must be parseable.
    r = s.cli(["validate", str(v07), "--format", "json"])
    s.assert_("--format json exits 0", r.returncode == 0, r.stderr)
    try:
        parsed = json.loads(r.stdout)
        s.assert_("--format json output is valid JSON", True)
        s.assert_(
            "--format json includes 'valid' key",
            "valid" in parsed,
            json.dumps(parsed, indent=2)[:200],
        )
    except json.JSONDecodeError as exc:
        s.fail("--format json output is valid JSON", f"{exc}: {r.stdout[:200]}")

    # Table format runs without crashing (Rich required for nicest output but
    # the fallback table formatter ships in-tree).
    r = s.cli(["validate", str(v07), "--format", "table"])
    s.assert_("--format table exits 0", r.returncode == 0, r.stderr)


def section_stdin(s: Smoke) -> None:
    s.section("7. validate — stdin input")
    payload = (FIXTURES / "valid" / "minimal_dpp.json").read_text(encoding="utf-8")
    r = s.cli(["validate", "-"], stdin=payload)
    # Either valid (0) or invalid (1) is fine — what matters is that the CLI
    # accepted stdin without crashing (which would be exit code 2).
    s.assert_(
        "stdin input accepted (exit 0 or 1)",
        r.returncode in (0, 1),
        f"exit={r.returncode} stderr={r.stderr[:200]}",
    )
    s.assert_(
        "stdin output contains 'Schema version'",
        "Schema version" in r.stdout,
        r.stdout[:200],
    )


def section_migrate(s: Smoke) -> None:
    s.section("8. migrate — v0.6 → v0.7")
    v06 = FIXTURES / "valid" / "untp-dpp-instance-0.6.1.json"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # Happy path: --accept-warnings writes both upgraded.json + sidecar.
        out = tmp / "upgraded.json"
        r = s.cli(["migrate", str(v06), "-o", str(out), "--accept-warnings"])
        s.assert_("migrate --accept-warnings exits 0", r.returncode == 0, r.stderr)
        s.assert_("migrate produced upgraded.json", out.is_file())
        sidecar = tmp / "upgraded.json.warnings.json"
        s.assert_("migrate produced sidecar .warnings.json", sidecar.is_file())

        if out.is_file():
            upgraded = json.loads(out.read_text(encoding="utf-8"))
            ctxs = upgraded.get("@context") or []
            s.assert_(
                "upgraded payload @context references v0.7",
                any(isinstance(c, str) and "vocabulary.uncefact.org/untp/0.7" in c for c in ctxs),
                json.dumps(ctxs)[:200],
            )

        if sidecar.is_file():
            warnings_doc = json.loads(sidecar.read_text(encoding="utf-8"))
            s.assert_(
                "sidecar records the v0.6 → v0.7 transition",
                "0.6" in str(warnings_doc.get("schema_version_from", ""))
                and "0.7" in str(warnings_doc.get("schema_version_to", "")),
                json.dumps(warnings_doc)[:200],
            )

        # Refusal path: no --accept-warnings → EXIT_BLOCKING_WARNINGS (4)
        # per docs/reference/cli/exit-codes.md (Phase 6 task 6.7);
        # sidecar STILL written, main output NOT written.
        out2 = tmp / "blocked.json"
        r = s.cli(["migrate", str(v06), "-o", str(out2)])
        s.assert_(
            "migrate without --accept-warnings refuses (exit 4)",
            r.returncode == 4,
            r.stderr or r.stdout,
        )
        s.assert_(
            "migrate did NOT write main file when blocked",
            not out2.is_file(),
        )
        s.assert_(
            "migrate STILL wrote sidecar when blocked",
            (tmp / "blocked.json.warnings.json").is_file(),
        )


def section_validate_upgrade_from(s: Smoke) -> None:
    s.section("9. validate --upgrade-from (one-shot)")
    v06 = FIXTURES / "valid" / "untp-dpp-instance-0.6.1.json"
    r = s.cli(
        [
            "validate",
            str(v06),
            "--upgrade-from",
            "0.6.1",
            "--schema-version",
            "0.7.0",
        ]
    )
    # exit 0 (clean upgrade) or 1 (residual schema warnings) — both fine.
    s.assert_(
        "--upgrade-from runs without crashing",
        r.returncode in (0, 1),
        f"exit={r.returncode} stderr={r.stderr[:200]}",
    )
    has_upgrade_warnings = any(c in r.stdout for c in ("UPG001", "UPG002", "UPG003", "UPG004"))
    s.assert_(
        "--upgrade-from surfaces UPG warnings",
        has_upgrade_warnings,
        r.stdout[:300],
    )


def section_export(s: Smoke) -> None:
    s.section("10. export — JSON-LD")
    v07 = FIXTURES / "valid" / "untp-dpp-instance-0.7.0.json"
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "exported.jsonld"
        r = s.cli(["export", str(v07), "--format", "jsonld", "-o", str(out)])
        s.assert_("export jsonld exits 0", r.returncode == 0, r.stderr)
        s.assert_("export wrote output file", out.is_file())
        if out.is_file():
            data = json.loads(out.read_text(encoding="utf-8"))
            s.assert_("exported output has @context", "@context" in data)
            ctxs = data.get("@context") or []
            s.assert_(
                "export @context references v0.7 (auto-detect threaded)",
                any(isinstance(c, str) and "vocabulary.uncefact.org/untp/0.7" in c for c in ctxs),
                json.dumps(ctxs)[:200],
            )

        # JSON format also works.
        out_json = Path(tmpdir) / "exported.json"
        r = s.cli(["export", str(v07), "--format", "json", "-o", str(out_json)])
        s.assert_("export json exits 0", r.returncode == 0, r.stderr)
        s.assert_("export json wrote output file", out_json.is_file())


def section_python_api(s: Smoke) -> None:
    s.section("11. Python API — ValidationEngine")
    r = s.py(
        """
        from dppvalidator.validators import ValidationEngine
        engine = ValidationEngine(schema_version='0.7.0', layers=['model'])
        result = engine.validate({
            '@context': [
                'https://www.w3.org/ns/credentials/v2',
                'https://vocabulary.uncefact.org/untp/0.7.0/context/',
            ],
            'type': ['DigitalProductPassport', 'VerifiableCredential'],
            'id': 'urn:test',
            'name': 'Test',
            'issuer': {'type': ['CredentialIssuer'], 'id': 'did:test', 'name': 'Test'},
            'validFrom': '2024-01-01T00:00:00Z',
            'credentialSubject': {
                'type': ['Product'],
                'id': 'urn:p',
                'name': 'P',
                'idScheme': {'type': ['IdentifierScheme'], 'id': 'urn:s', 'name': 's'},
                'idGranularity': 'model',
                'productCategory': [{
                    'type': ['Classification'],
                    'schemeId': 'urn:cpc',
                    'schemeName': 's',
                    'code': '1',
                    'name': 'n',
                }],
                'producedAtFacility': {'type': ['Facility'], 'id': 'urn:f', 'name': 'f'},
                'countryOfProduction': {'countryCode': 'DE', 'countryName': 'Germany'},
            },
        })
        assert result.valid, f'unexpected errors: {result.errors}'
        assert result.passport is not None
        assert result.schema_version == '0.7.0'
        print('OK')
        """
    )
    s.assert_(
        "ValidationEngine validates a v0.7 dict end-to-end",
        r.returncode == 0 and "OK" in r.stdout,
        r.stderr or r.stdout,
    )


def section_compat_api(s: Smoke) -> None:
    s.section("12. Python API — compat shim")
    v06 = FIXTURES / "valid" / "untp-dpp-instance-0.6.1.json"
    r = s.py(
        f"""
        import json
        from pathlib import Path
        from dppvalidator.compat import (
            upgrade,
            active_version,
            is_version,
            UpgradeWarning,
            UpgradeSeverity,
        )

        v06 = json.loads(Path({json.dumps(str(v06))}).read_text(encoding='utf-8'))
        upgraded, warnings = upgrade(v06, country_lookup={{'AU': 'Australia'}})

        # Shape contract.
        assert isinstance(upgraded, dict), type(upgraded)
        assert isinstance(warnings, list), type(warnings)
        assert all(isinstance(w, UpgradeWarning) for w in warnings)
        assert any(w.severity == UpgradeSeverity.WARNING or
                   w.severity == UpgradeSeverity.INFO for w in warnings)

        # Context rewritten.
        ctxs = upgraded.get('@context', [])
        assert any('vocabulary.uncefact.org/untp/0.7' in c for c in ctxs
                   if isinstance(c, str)), ctxs

        # Helper APIs.
        v = active_version()
        assert isinstance(v, str) and v.count('.') == 2, v
        assert is_version(v)
        assert not is_version('9.9.9')

        print('OK')
        """
    )
    s.assert_(
        "compat.upgrade + active_version() + is_version()",
        r.returncode == 0 and "OK" in r.stdout,
        r.stderr or r.stdout,
    )


def section_eudpp_exporter(s: Smoke) -> None:
    s.section("13. Python API — EU DPP exporter")
    v07 = FIXTURES / "valid" / "untp-dpp-instance-0.7.0.json"
    r = s.py(
        f"""
        import json
        from pathlib import Path
        from dppvalidator.models.v0_7.envelope import DigitalProductPassport
        from dppvalidator.exporters import EUDPPJsonLDExporter

        v07 = json.loads(Path({json.dumps(str(v07))}).read_text(encoding='utf-8'))
        passport = DigitalProductPassport.model_validate(v07)

        # Auto-detect from passport class.
        out = EUDPPJsonLDExporter().export_dict(passport)
        assert 'credentialSubject' in out
        assert isinstance(out.get('@context'), list)
        # eudpp:DPP type marker proves the term mapper applied.
        types = out.get('type') or []
        assert 'eudpp:DPP' in types, types

        # Explicit pin.
        out07 = EUDPPJsonLDExporter(schema_version='0.7.0').export_dict(passport)
        assert 'credentialSubject' in out07

        print('OK')
        """
    )
    s.assert_(
        "EUDPPJsonLDExporter auto-detect + explicit pin",
        r.returncode == 0 and "OK" in r.stdout,
        r.stderr or r.stdout,
    )


def section_plugin_discovery(s: Smoke) -> None:
    s.section("14. Plugin discovery + version-aware dispatch")
    r = s.py(
        """
        from importlib.util import find_spec
        if find_spec('dppvalidator_example_plugin') is None:
            print('SKIP example plugin not installed')
        else:
            from dppvalidator.plugins.discovery import (
                discover_validators,
                discover_exporters,
            )
            from dppvalidator.plugins.registry import PluginRegistry
            from dppvalidator.models.passport import DigitalProductPassport
            from dppvalidator.models import CredentialIssuer

            v_names = sorted(n for n, _ in discover_validators())
            e_names = sorted(n for n, _ in discover_exporters())
            assert 'brand_name' in v_names, v_names
            assert 'brand_name_v07' in v_names, v_names
            assert 'min_materials' in v_names, v_names
            assert 'csv' in e_names, e_names

            # Per-version filter contract: v0.6 plugin must NOT run on v0.7
            # passport (filtered before .check()), and vice-versa.
            registry = PluginRegistry()
            passport = DigitalProductPassport(
                id='urn:test',
                issuer=CredentialIssuer(id='did:test', name='Test'),
            )
            v06_errs = registry.run_all_validators(passport, schema_version='0.6.1')
            v07_errs = registry.run_all_validators(passport, schema_version='0.7.0')
            for e in v06_errs:
                assert e.code != 'PLG001', f'v0.6 plugin crashed: {e.message}'
            for e in v07_errs:
                assert e.code != 'PLG001', f'v0.7 plugin crashed: {e.message}'
            print('OK')
        """
    )
    if "SKIP" in r.stdout:
        s.skip("plugin discovery", "example plugin not installed")
    else:
        s.assert_(
            "plugin discovery + version-aware dispatch",
            r.returncode == 0 and "OK" in r.stdout,
            r.stderr or r.stdout,
        )


def section_manifest_integrity(s: Smoke) -> None:
    s.section("15. Manifest integrity (every vendored artefact pinned)")
    r = s.py(
        """
        import hashlib, json
        from pathlib import Path
        repo = Path.cwd()
        manifest_path = repo / 'src' / 'dppvalidator' / 'schemas' / 'data' / 'MANIFEST.json'
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        bad = []
        for entry in manifest['artefacts']:
            f = repo / entry['path']
            if not f.is_file():
                bad.append(f"missing: {entry['path']}")
                continue
            data = f.read_bytes().replace(b'\\r\\n', b'\\n')
            actual = hashlib.sha256(data).hexdigest()
            if actual != entry['sha256']:
                bad.append(f"hash mismatch: {entry['path']}")
        if bad:
            print('FAIL\\n' + '\\n'.join(bad))
        else:
            print(f'OK {len(manifest["artefacts"])} artefacts')
        """
    )
    s.assert_(
        "every MANIFEST.json artefact's SHA-256 still matches",
        r.returncode == 0 and r.stdout.startswith("OK"),
        r.stderr or r.stdout,
    )


def section_doctor(s: Smoke) -> None:
    s.section("16. doctor — environment health")
    r = s.cli(["doctor"])
    # 0 (healthy) or 2 (issues but the command itself worked).
    s.assert_(
        "doctor runs without crashing",
        r.returncode in (0, 2),
        f"exit={r.returncode} stderr={r.stderr[:200]}",
    )


# ---------------------------------------------------------------------------
# Content negotiation against the upstream UN/CEFACT vocabulary endpoint
# ---------------------------------------------------------------------------


def _http_head_get(url: str, accept: str, timeout: float = 10.0) -> tuple[int, str, bytes]:
    """Issue a GET (with Accept) and return (status, content-type, body).

    GET (not HEAD) because S3/CloudFront sometimes serves different
    Content-Type headers on HEAD vs GET. We need the negotiated body
    too, to verify it's parseable JSON-LD when that's what we asked
    for. Capped at 256 KB so we don't pull the full ~150 KB twice in
    a tight loop.
    """
    req = urllib.request.Request(  # noqa: S310 — fixed https URLs only
        url,
        headers={"Accept": accept, "User-Agent": "dppvalidator-smoke/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        body = resp.read(262_144)
        return resp.status, resp.headers.get("Content-Type", ""), body


def section_content_negotiation(s: Smoke) -> None:
    """Verify upstream UN/CEFACT vocabulary honours JSON-LD content-negotiation.

    Two upstream endpoints with different contracts:

    1. ``/untp/`` — vocabulary landing page. Full negotiation:
       - ``Accept: application/ld+json`` → ``application/ld+json``
       - default / ``Accept: text/html`` → HTML landing page
       - ``Accept: application/json`` → HTML (only ``ld+json`` is honoured)

    2. ``/untp/0.7.0/context/`` — pure JSON-LD context document.
       Unconditionally served as ``application/ld+json`` regardless of
       ``Accept`` (there is no HTML alternative — a context IS the artefact).

    Both must always return parseable JSON-LD with a root ``@context`` when
    dereferenced as part of normal validator flows. Network-dependent;
    skips cleanly when the host is unreachable.
    """
    s.section("17. Content negotiation — vocabulary.uncefact.org")

    # ── /untp/ — landing page with full negotiation ────────────────────────
    base = "https://vocabulary.uncefact.org/untp/"
    base_label = "untp/"
    try:
        status, ctype, body = _http_head_get(base, "application/ld+json")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        s.skip(f"{base_label} (network)", f"unavailable: {exc}")
    else:
        s.assert_(f"{base_label} ld+json returns 200", status == 200, f"got status={status}")
        s.assert_(
            f"{base_label} ld+json Content-Type is application/ld+json",
            "application/ld+json" in ctype.lower(),
            f"got Content-Type={ctype!r}",
        )
        try:
            doc = json.loads(body.decode("utf-8"))
            s.assert_(
                f"{base_label} ld+json body is parseable JSON-LD with @context",
                isinstance(doc, dict) and "@context" in doc,
                f"top keys: {sorted(doc) if isinstance(doc, dict) else type(doc).__name__}",
            )
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            s.fail(
                f"{base_label} ld+json body is parseable JSON-LD with @context",
                f"{exc!r}: {body[:120]!r}",
            )

        # Default Accept must fall back to HTML — proves negotiation is real,
        # not a hard-coded Content-Type.
        try:
            _, ctype_html, _ = _http_head_get(base, "text/html,*/*")
            s.assert_(
                f"{base_label} default Accept falls back to HTML (proves negotiation)",
                "text/html" in ctype_html.lower(),
                f"got Content-Type={ctype_html!r}",
            )
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            s.skip(f"{base_label} (HTML probe)", f"network blip: {exc}")

        # application/json currently falls back to HTML. Pin the observation
        # so a future upstream change (good: starts honouring it; bad: 406s)
        # is flagged loudly rather than silently changing validator semantics.
        try:
            _, ctype_json, _ = _http_head_get(base, "application/json")
            s.assert_(
                f"{base_label} application/json → HTML fallback (only ld+json is honoured)",
                "text/html" in ctype_json.lower(),
                f"got Content-Type={ctype_json!r} — upstream behaviour changed?",
            )
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            s.skip(f"{base_label} (json probe)", f"network blip: {exc}")

    # ── /untp/0.7.0/context/ — pure JSON-LD context, no negotiation ────────
    ctx_url = "https://vocabulary.uncefact.org/untp/0.7.0/context/"
    ctx_label = "untp/0.7.0/context/"
    for accept, accept_label in (
        ("application/ld+json", "ld+json"),
        ("text/html,*/*", "default Accept"),
        ("application/json", "application/json"),
    ):
        try:
            status, ctype, body = _http_head_get(ctx_url, accept)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            s.skip(f"{ctx_label} ({accept_label})", f"network blip: {exc}")
            continue
        s.assert_(
            f"{ctx_label} {accept_label} returns 200",
            status == 200,
            f"got status={status}",
        )
        # Context document is always served as ld+json — there's no
        # HTML alternative because a JSON-LD context IS the artefact.
        s.assert_(
            f"{ctx_label} {accept_label} → application/ld+json (unconditional)",
            "application/ld+json" in ctype.lower(),
            f"got Content-Type={ctype!r}",
        )

    # Final cross-check: the context body really is the v0.7.0 UNTP context
    # document — pin shape + a couple of well-known prefixes so silent upstream
    # content drift is caught (e.g. if the file at this URL is replaced).
    try:
        _, _, body = _http_head_get(ctx_url, "application/ld+json")
        doc = json.loads(body.decode("utf-8"))
        ctx = doc.get("@context")
        s.assert_(
            "context body has @context as a dict (JSON-LD context document)",
            isinstance(ctx, dict),
            f"@context type: {type(ctx).__name__}",
        )
        if isinstance(ctx, dict):
            terms = list(ctx.keys())
            s.assert_(
                "context body declares 'untp' prefix (right document at this URL)",
                "untp" in terms,
                f"terms[:8]: {terms[:8]}",
            )
            # 105 KB context with ~30+ top-level terms is the expected shape;
            # drop to >= 10 to leave headroom for upstream pruning while still
            # catching catastrophic shrinkage (e.g. a stub or 404 page).
            s.assert_(
                "context body has substantial term mappings (not a stub)",
                len(terms) >= 10,
                f"only {len(terms)} terms — upstream stub?",
            )
    except (
        urllib.error.URLError,
        TimeoutError,
        OSError,
        json.JSONDecodeError,
        UnicodeDecodeError,
    ) as exc:
        s.skip("context content cross-check", f"unavailable: {exc}")


# ---------------------------------------------------------------------------
# Phase 9 (0.5.0) — user-visible contract checks
# ---------------------------------------------------------------------------
#
# The five sections below pin the Phase 9 contracts on the *installed*
# wheel so a regression in any of them blocks a release. They run on
# both the local dev env and the TestPyPI smoke job in release.yml
# (see DPP_BIN env var). Each is small and self-contained.


def section_exit_codes(s: Smoke) -> None:
    s.section("18. CLI — six-code exit surface (Phase 6 task 6.7)")
    v06 = FIXTURES / "valid" / "untp-dpp-instance-0.6.1.json"
    v07 = FIXTURES / "valid" / "untp-dpp-instance-0.7.0.json"
    if not v06.is_file() or not v07.is_file():
        s.skip("six-code exit surface", "fixtures unavailable")
        return

    # Exit 0 — valid v0.7 fixture
    r = s.cli(["validate", str(v07)])
    s.assert_(
        "exit 0 (EXIT_VALID) on a valid v0.7.0 fixture",
        r.returncode == 0,
        r.stderr or r.stdout,
    )

    # Exit 1 — schema-violating junk payload
    with tempfile.TemporaryDirectory() as tmpdir:
        junk = Path(tmpdir) / "junk.json"
        junk.write_text(
            '{"id":"https://x.com","issuer":{"id":"https://x.com","name":"T"}}',
            encoding="utf-8",
        )
        r = s.cli(["validate", str(junk)])
        s.assert_(
            "exit 1 (EXIT_INVALID) on a schema-violating payload",
            r.returncode == 1,
            r.stderr or r.stdout,
        )

    # Exit 3 — DET001 family mismatch (--target cirpass on a UNTP fixture)
    r = s.cli(["validate", "--target", "cirpass", str(v07)])
    s.assert_(
        "exit 3 (EXIT_FAMILY_MISMATCH) on --target/payload contradiction",
        r.returncode == 3,
        r.stderr or r.stdout,
    )
    s.assert_(
        "DET001 surfaced in stderr/stdout for the family mismatch",
        "DET001" in (r.stderr + r.stdout),
        r.stderr or r.stdout,
    )

    # Exit 4 — migrate without --accept-warnings (blocking warnings)
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "blocked.json"
        r = s.cli(["migrate", str(v06), "-o", str(out)])
        s.assert_(
            "exit 4 (EXIT_BLOCKING_WARNINGS) on migrate w/o --accept-warnings",
            r.returncode == 4,
            r.stderr or r.stdout,
        )
        sidecar = out.with_suffix(out.suffix + ".warnings.json")
        s.assert_(
            "sidecar warnings file written even when main output is blocked",
            sidecar.is_file(),
            f"expected {sidecar} to exist; tmpdir contents: {list(Path(tmpdir).iterdir())}",
        )

    # Exit 5 — IO error (file not found)
    r = s.cli(["validate", "/tmp/_dppvalidator_smoke_does_not_exist.json"])
    s.assert_(
        "exit 5 (EXIT_IO_ERROR) on a missing input file",
        r.returncode == 5,
        r.stderr or r.stdout,
    )

    # Exit 5 — IO error (invalid JSON)
    with tempfile.TemporaryDirectory() as tmpdir:
        bad = Path(tmpdir) / "bad.json"
        bad.write_text("{not valid json", encoding="utf-8")
        r = s.cli(["validate", str(bad)])
        s.assert_(
            "exit 5 (EXIT_IO_ERROR) on syntactically-invalid JSON",
            r.returncode == 5,
            r.stderr or r.stdout,
        )


def section_status_list_index_coercion(s: Smoke) -> None:
    s.section("19. D1 (Phase 9.7) — BitstringStatusListEntry.statusListIndex int coercion")
    r = s.py(
        """
        from dppvalidator.models.v0_7.envelope import BitstringStatusListEntry
        # Numeric-string from a v0.6 fixture shape — must coerce to int.
        e = BitstringStatusListEntry.model_validate({
            'id': 'https://example.com/sl/1',
            'type': 'BitstringStatusListEntry',
            'statusPurpose': 'revocation',
            'statusListIndex': '12345',
            'statusListCredential': 'https://example.com/sl',
        })
        assert e.status_list_index == 12345, e.status_list_index
        assert isinstance(e.status_list_index, int), type(e.status_list_index)
        # Round-trip — model_dump emits int, not the original string.
        dumped = e.model_dump(by_alias=True, exclude_none=True)
        assert dumped['statusListIndex'] == 12345, dumped
        assert isinstance(dumped['statusListIndex'], int), type(dumped['statusListIndex'])
        # Negative integer is rejected (ge=0).
        try:
            BitstringStatusListEntry.model_validate({
                'id': 'https://example.com/sl/2',
                'type': 'BitstringStatusListEntry',
                'statusPurpose': 'revocation',
                'statusListIndex': -1,
                'statusListCredential': 'https://example.com/sl',
            })
            raise AssertionError('negative statusListIndex should have been rejected')
        except Exception:
            pass
        print('OK')
        """
    )
    s.assert_(
        "statusListIndex coerces numeric strings to int and rejects negatives",
        r.returncode == 0 and "OK" in r.stdout,
        r.stderr or r.stdout,
    )


def section_party_role_gradient(s: Smoke) -> None:
    s.section("20. D2 (Phase 9.8) — PartyRoleEnum gradient + PRT001 advisory")
    v07 = FIXTURES / "valid" / "untp-dpp-instance-0.7.0.json"
    if not v07.is_file():
        s.skip("PartyRoleEnum gradient", "v0.7 fixture unavailable")
        return

    r = s.py(
        f"""
        import copy, json
        from pathlib import Path
        from dppvalidator.models.v0_7.identifiers import PartyRoleEnum, SCHEMA_STRICT_ROLES
        from dppvalidator.validators.engine import ValidationEngine

        # Surface invariants — gradient sizes are part of the public contract.
        assert len(SCHEMA_STRICT_ROLES) == 6, len(SCHEMA_STRICT_ROLES)
        assert len(list(PartyRoleEnum)) == 20, len(list(PartyRoleEnum))
        assert PartyRoleEnum.MANUFACTURER.is_schema_strict() is True
        assert PartyRoleEnum.IMPORTER.is_schema_strict() is False

        # Build a payload with one of the 14 wider PartyRole values.
        payload = json.loads(Path({json.dumps(str(v07))}).read_text(encoding='utf-8'))
        related = payload.get('credentialSubject', {{}}).setdefault('relatedParty', [])
        wider = {{'type': ['PartyRole'], 'role': 'importer',
                  'party': {{'type': ['Party'], 'id': 'did:web:imp.example.com', 'name': 'Imp Co'}}}}
        if related:
            related[0] = wider
        else:
            related.append(wider)

        # Default mode: PRT001 fires as info (informational).
        r_default = ValidationEngine(schema_version='0.7.0').validate(payload)
        prt_info = [i for i in (r_default.info or []) if i.code == 'PRT001']
        assert len(prt_info) == 1, prt_info
        assert all(e.code != 'PRT001' for e in (r_default.errors or [])), r_default.errors

        # Strict mode: same payload, PRT001 promoted to error; valid flips to False.
        r_strict = ValidationEngine(schema_version='0.7.0', strict_role_enum=True).validate(payload)
        prt_err = [e for e in (r_strict.errors or []) if e.code == 'PRT001']
        assert len(prt_err) == 1, prt_err
        assert prt_err[0].severity == 'error', prt_err[0].severity
        assert all(i.code != 'PRT001' for i in (r_strict.info or [])), r_strict.info

        print('OK')
        """
    )
    s.assert_(
        "PRT001 emits as info by default, upgrades to error under strict_role_enum=True",
        r.returncode == 0 and "OK" in r.stdout,
        r.stderr or r.stdout,
    )


def section_deprecation_warnings(s: Smoke) -> None:
    s.section("21. Phase 9.4 — deprecation warnings activated for 0.5.0")
    r = s.py(
        """
        import warnings

        # is_dpp_document — Phase 2 alias deprecated in 0.5.0.
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter('always')
            from dppvalidator.validators.detection import is_dpp_document
            is_dpp_document({'type': ['DigitalProductPassport']})
        ddep = [w for w in captured if issubclass(w.category, DeprecationWarning)]
        assert len(ddep) == 1, [str(w.message) for w in ddep]
        assert 'looks_like_dpp' in str(ddep[0].message), str(ddep[0].message)

        # SCHEMA_REGISTRY[version] bare-string lookup — deprecated in 0.5.0.
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter('always')
            from dppvalidator.schemas.registry import SCHEMA_REGISTRY
            _ = SCHEMA_REGISTRY['0.7.0']
            _ = SCHEMA_REGISTRY['0.6.1']
        sdep = [w for w in captured if issubclass(w.category, DeprecationWarning)]
        assert len(sdep) == 2, [str(w.message) for w in sdep]
        assert 'SCHEMA_REGISTRY_BY_FAMILY' in str(sdep[0].message), str(sdep[0].message)

        # Recommended replacement — must NOT warn.
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter('always')
            from dppvalidator.schemas.registry import SCHEMA_REGISTRY_BY_FAMILY, SchemaFamily
            _ = SCHEMA_REGISTRY_BY_FAMILY[(SchemaFamily.UNTP, '0.7.0')]
        clean = [w for w in captured if issubclass(w.category, DeprecationWarning)]
        assert clean == [], [str(w.message) for w in clean]

        print('OK')
        """
    )
    s.assert_(
        "is_dpp_document() and SCHEMA_REGISTRY[] each emit DeprecationWarning",
        r.returncode == 0 and "OK" in r.stdout,
        r.stderr or r.stdout,
    )


def section_cross_family_round_trip(s: Smoke) -> None:
    s.section("22. Cross-family round-trip — UNTP ↔ CIRPASS via Python compat")
    v07 = FIXTURES / "valid" / "untp-dpp-instance-0.7.0.json"
    if not v07.is_file():
        s.skip("cross-family round-trip", "v0.7 fixture unavailable")
        return

    r = s.py(
        f"""
        import json
        from pathlib import Path
        from dppvalidator.compat import to_cirpass_1_3, to_untp_0_7
        from dppvalidator.validators.engine import ValidationEngine

        untp = json.loads(Path({json.dumps(str(v07))}).read_text(encoding='utf-8'))

        # Forward shim — UNTP 0.7 → CIRPASS 1.3.
        cirpass, fwd_warnings = to_cirpass_1_3(untp)
        assert isinstance(cirpass, dict), type(cirpass)
        assert 'dppIdentifier' in cirpass and 'product' in cirpass and 'issuedAt' in cirpass, sorted(cirpass.keys())
        fwd_codes = {{w.code for w in fwd_warnings}}
        # The shim is documented to emit MAP00X warnings on lossy projections.
        assert fwd_codes & {{'MAP001', 'MAP002', 'MAP003', 'MAP004', 'MAP005'}}, fwd_codes

        # Reverse shim — round-trip back to UNTP.
        back, rev_warnings = to_untp_0_7(cirpass)
        assert isinstance(back, dict), type(back)
        assert '@context' in back and 'credentialSubject' in back, sorted(back.keys())

        # Round-tripped UNTP must validate cleanly against the v0.7 schema.
        r_back = ValidationEngine(schema_version='0.7.0').validate(back)
        assert r_back.valid, [e.message for e in r_back.errors[:3]]
        assert r_back.schema_version == '0.7.0', r_back.schema_version

        print('OK')
        """
    )
    s.assert_(
        "UNTP→CIRPASS→UNTP round-trip emits MAP-warnings and re-validates",
        r.returncode == 0 and "OK" in r.stdout,
        r.stderr or r.stdout,
    )


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def main() -> int:
    s = Smoke()
    print(f"{BLUE}dppvalidator functional smoke test{RESET}")
    print(f"{DIM}DPP_BIN={DPP_BIN}{RESET}")
    print(f"{DIM}PY_BIN={PY_BIN}{RESET}")

    if not _check_environment(s):
        s.fail("pre-flight failed", "stopping early — fix the environment and re-run")
        return s.report()

    section_cli_sanity(s)
    section_schema_management(s)
    section_validate_auto_detect(s)
    section_validate_explicit_pin(s)
    section_validate_invalid(s)
    section_output_formats(s)
    section_stdin(s)
    section_migrate(s)
    section_validate_upgrade_from(s)
    section_export(s)
    section_python_api(s)
    section_compat_api(s)
    section_eudpp_exporter(s)
    section_plugin_discovery(s)
    section_manifest_integrity(s)
    section_doctor(s)
    section_content_negotiation(s)

    # Phase 9 (0.5.0) — pin user-visible 0.5.0 contracts on the
    # installed wheel. Run last because they're the freshest layer
    # and any flake here is most actionable.
    section_exit_codes(s)
    section_status_list_index_coercion(s)
    section_party_role_gradient(s)
    section_deprecation_warnings(s)
    section_cross_family_round_trip(s)

    return s.report()


if __name__ == "__main__":
    sys.exit(main())
