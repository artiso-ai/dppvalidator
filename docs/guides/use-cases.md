# Use Cases

Real-world examples of how to use dppvalidator across different scenarios
and industries.

______________________________________________________________________

## Fashion & Textiles Compliance

### Pre-Production Validation

Validate DPP data before generating QR codes for garment labels.

```python
from dppvalidator import ValidationEngine
from dppvalidator.vocabularies import validate_gtin, is_valid_material_code

engine = ValidationEngine(strict_mode=True)


def validate_garment_dpp(dpp_data: dict) -> dict:
    """Validate garment DPP before QR code generation."""
    result = engine.validate(dpp_data)

    if not result.valid:
        return {
            "status": "rejected",
            "errors": [
                {"code": e.code, "path": e.path, "message": e.message}
                for e in result.errors
            ],
        }

    return {
        "status": "approved",
        "passport_id": dpp_data.get("id"),
        "ready_for_qr": True,
    }


# Example garment DPP
garment_dpp = {
    "type": ["DigitalProductPassport", "VerifiableCredential"],
    "@context": [
        "https://www.w3.org/ns/credentials/v2",
        "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
    ],
    "id": "https://brand.com/dpp/organic-dress-2024-001",
    "issuer": {
        "id": "did:web:brand.com",
        "name": "Sustainable Fashion Brand",
    },
    "validFrom": "2024-06-01T00:00:00Z",
    "validUntil": "2034-06-01T00:00:00Z",
    "credentialSubject": {
        "type": ["Product"],
        "id": "https://brand.com/products/organic-dress-001",
        "name": "Organic Cotton Summer Dress",
        "granularityLevel": "model",
        "materialsProvenance": [
            {
                "type": ["Material"],
                "name": "GOTS Organic Cotton",
                "massFraction": 0.95,
                "recycled": False,
                "hazardous": False,
            },
            {
                "type": ["Material"],
                "name": "Elastane",
                "massFraction": 0.05,
                "recycled": False,
                "hazardous": False,
            },
        ],
        "circularityScorecard": {
            "type": ["CircularityScorecard"],
            "recycledContent": 0.0,
            "recyclableContent": 0.92,
        },
    },
}

result = validate_garment_dpp(garment_dpp)
print(result)
```

### Material Composition Validation

Ensure fiber compositions are accurate and sum correctly.

```python
from dppvalidator import ValidationEngine

engine = ValidationEngine()


def check_fiber_composition(dpp_data: dict) -> dict:
    """Check fiber composition adds up to 100%."""
    result = engine.validate(dpp_data)

    materials = dpp_data.get("credentialSubject", {}).get("materialsProvenance", [])

    total_fraction = sum(m.get("massFraction", 0) for m in materials)

    return {
        "valid": result.valid,
        "total_composition": f"{total_fraction * 100:.1f}%",
        "materials": [
            {
                "name": m.get("name"),
                "percentage": f"{m.get('massFraction', 0) * 100:.1f}%",
            }
            for m in materials
        ],
        "composition_complete": abs(total_fraction - 1.0) < 0.01,
    }
```

______________________________________________________________________

## Supplier Onboarding

### Supplier DPP Validation API

Validate DPP submissions from suppliers before accepting them.

```python
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from dppvalidator import ValidationEngine

app = FastAPI(title="Supplier DPP Validation API")
engine = ValidationEngine(strict_mode=True)


class SubmissionResponse(BaseModel):
    accepted: bool
    submission_id: str | None = None
    errors: list[dict] | None = None


@app.post("/api/v1/supplier/submit-dpp", response_model=SubmissionResponse)
async def submit_dpp(dpp: dict, supplier_id: str):
    """Validate and accept supplier DPP submission."""

    # Validate the DPP
    result = engine.validate(dpp)

    if not result.valid:
        return SubmissionResponse(
            accepted=False,
            errors=[
                {
                    "code": e.code,
                    "field": e.path,
                    "message": e.message,
                    "suggestion": e.suggestion,
                }
                for e in result.errors
            ],
        )

    # DPP is valid - store it
    submission_id = f"SUB-{supplier_id}-{dpp.get('id', '').split('/')[-1]}"

    return SubmissionResponse(
        accepted=True,
        submission_id=submission_id,
    )


@app.post("/api/v1/supplier/batch-validate")
async def batch_validate(dpps: list[dict]):
    """Validate multiple DPPs in one request."""
    results = await engine.validate_batch(dpps, concurrency=10)

    return {
        "total": len(dpps),
        "valid": sum(1 for r in results if r.valid),
        "invalid": sum(1 for r in results if not r.valid),
        "results": [
            {
                "index": i,
                "valid": r.valid,
                "error_count": r.error_count,
            }
            for i, r in enumerate(results)
        ],
    }
```

### Supplier Quality Dashboard

Aggregate validation results for supplier quality scoring.

```python
from collections import Counter
from dataclasses import dataclass
from dppvalidator import ValidationEngine


@dataclass
class SupplierQualityReport:
    supplier_id: str
    total_submissions: int
    valid_count: int
    invalid_count: int
    pass_rate: float
    common_errors: list[tuple[str, int]]


def analyze_supplier_submissions(
    supplier_id: str,
    submissions: list[dict],
) -> SupplierQualityReport:
    """Analyze a supplier's DPP submission quality."""
    engine = ValidationEngine()

    error_codes = []
    valid_count = 0

    for dpp in submissions:
        result = engine.validate(dpp)
        if result.valid:
            valid_count += 1
        else:
            error_codes.extend(e.code for e in result.errors)

    return SupplierQualityReport(
        supplier_id=supplier_id,
        total_submissions=len(submissions),
        valid_count=valid_count,
        invalid_count=len(submissions) - valid_count,
        pass_rate=valid_count / len(submissions) if submissions else 0,
        common_errors=Counter(error_codes).most_common(5),
    )
```

______________________________________________________________________

## CI/CD Pipeline Integration

### GitHub Actions Workflow

Add DPP validation as a CI/CD gate.

```yaml
# .github/workflows/validate-dpps.yml
name: Validate Digital Product Passports

on:
  push:
    paths:
      - 'data/passports/**/*.json'
  pull_request:
    paths:
      - 'data/passports/**/*.json'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dppvalidator
        run: pip install dppvalidator

      - name: Validate all DPP files
        run: |
          find data/passports -name "*.json" -exec \
            dppvalidator validate {} --strict --format json \;

      - name: Generate validation report
        if: always()
        run: |
          echo "## DPP Validation Report" >> $GITHUB_STEP_SUMMARY
          for f in data/passports/*.json; do
            result=$(dppvalidator validate "$f" --format json 2>&1 || true)
            valid=$(echo "$result" | jq -r '.valid')
            if [ "$valid" = "true" ]; then
              echo "✅ $(basename $f)" >> $GITHUB_STEP_SUMMARY
            else
              echo "❌ $(basename $f)" >> $GITHUB_STEP_SUMMARY
            fi
          done
```

### Pre-Commit Hook

Validate DPP files before committing.

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: validate-dpps
        name: Validate DPP files
        entry: dppvalidator validate
        language: python
        types: [json]
        files: ^data/passports/.*\.json$
        additional_dependencies: [dppvalidator]
```

### Python CI Script

Programmatic validation for complex pipelines.

```python
#!/usr/bin/env python3
"""CI script for DPP validation with detailed reporting."""

import json
import sys
from pathlib import Path
from dppvalidator import ValidationEngine


def validate_directory(directory: Path) -> int:
    """Validate all DPP files in a directory."""
    engine = ValidationEngine(strict_mode=True)

    files = list(directory.glob("**/*.json"))
    if not files:
        print(f"No JSON files found in {directory}")
        return 0

    failed = 0
    for path in files:
        try:
            data = json.loads(path.read_text())
            result = engine.validate(data)

            if result.valid:
                print(f"✅ {path.name}")
            else:
                print(f"❌ {path.name}")
                for error in result.errors:
                    print(f"   [{error.code}] {error.path}: {error.message}")
                failed += 1

        except json.JSONDecodeError as e:
            print(f"❌ {path.name}: Invalid JSON - {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Total: {len(files)} | Passed: {len(files) - failed} | Failed: {failed}")

    return failed


if __name__ == "__main__":
    directory = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/passports")
    sys.exit(validate_directory(directory))
```

______________________________________________________________________

## Data Migration

### Legacy System Migration

Convert and validate legacy product data to DPP format.

```python
from datetime import datetime, timezone
from dppvalidator import ValidationEngine
from dppvalidator.models import DigitalProductPassport, CredentialIssuer


def migrate_legacy_product(legacy: dict, issuer_id: str) -> dict:
    """Convert legacy product data to DPP format."""
    return {
        "type": ["DigitalProductPassport", "VerifiableCredential"],
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
            "https://test.uncefact.org/vocabulary/untp/dpp/0.6.1/",
        ],
        "id": f"https://company.com/dpp/{legacy['sku']}",
        "issuer": {
            "id": issuer_id,
            "name": legacy.get("brand", "Unknown"),
        },
        "validFrom": datetime.now(timezone.utc).isoformat(),
        "validUntil": "2035-01-01T00:00:00Z",
        "credentialSubject": {
            "type": ["Product"],
            "id": f"https://company.com/products/{legacy['sku']}",
            "name": legacy["name"],
            "description": legacy.get("description", ""),
            "granularityLevel": "model",
        },
    }


def migrate_and_validate(
    legacy_products: list[dict],
    issuer_id: str,
) -> dict:
    """Migrate legacy products and validate the results."""
    engine = ValidationEngine()

    results = {
        "migrated": [],
        "failed": [],
    }

    for legacy in legacy_products:
        dpp = migrate_legacy_product(legacy, issuer_id)
        result = engine.validate(dpp)

        if result.valid:
            results["migrated"].append(
                {
                    "sku": legacy["sku"],
                    "dpp_id": dpp["id"],
                    "status": "success",
                }
            )
        else:
            results["failed"].append(
                {
                    "sku": legacy["sku"],
                    "errors": [e.message for e in result.errors],
                }
            )

    return results


# Example usage
legacy_data = [
    {"sku": "SHIRT-001", "name": "Cotton T-Shirt", "brand": "EcoBrand"},
    {"sku": "DRESS-002", "name": "Summer Dress", "brand": "EcoBrand"},
]

migration_results = migrate_and_validate(
    legacy_data,
    issuer_id="did:web:ecobrand.com",
)
print(f"Migrated: {len(migration_results['migrated'])}")
print(f"Failed: {len(migration_results['failed'])}")
```

______________________________________________________________________

## Supply Chain Traceability

### Deep Validation of Supply Chain

Validate entire supply chains by following linked documents.

```python
import asyncio
from dppvalidator import ValidationEngine


async def validate_supply_chain(root_dpp: dict) -> dict:
    """Validate a product's entire supply chain."""
    engine = ValidationEngine(
        validate_jsonld=True,
        verify_signatures=True,
    )

    result = await engine.validate_deep(
        root_dpp,
        max_depth=5,
        follow_links=[
            "credentialSubject.traceabilityEvents",
            "credentialSubject.conformityClaim",
            "credentialSubject.materialsProvenance",
        ],
        timeout=60.0,
    )

    return {
        "root_valid": result.root_result.valid,
        "total_documents": result.total_documents,
        "all_valid": result.valid,
        "max_depth_reached": result.max_depth_reached,
        "cycle_detected": result.cycle_detected,
        "failed_urls": list(result.failed_urls.keys()),
        "validation_time_ms": result.elapsed_time_ms,
    }


# Run the validation
supply_chain_report = asyncio.run(validate_supply_chain(garment_dpp))
print(f"Supply chain documents: {supply_chain_report['total_documents']}")
print(f"All valid: {supply_chain_report['all_valid']}")
```

______________________________________________________________________

## Consumer Applications

### Mobile App DPP Scanner

Parse and display DPP data in a consumer app.

```python
from dppvalidator import ValidationEngine

engine = ValidationEngine()


def scan_dpp_qrcode(qr_data: str | dict) -> dict:
    """Process scanned DPP QR code data for mobile app display."""
    result = engine.validate(qr_data)

    if not result.valid:
        return {
            "success": False,
            "error": "Invalid product passport",
        }

    passport = result.passport
    subject = passport.credential_subject if passport else None

    return {
        "success": True,
        "product": {
            "name": getattr(subject, "name", "Unknown"),
            "description": getattr(subject, "description", ""),
        },
        "issuer": {
            "name": passport.issuer.name if passport else "Unknown",
            "verified": result.signature_valid or False,
        },
        "sustainability": extract_sustainability_info(subject),
        "valid_until": (
            passport.valid_until.isoformat()
            if passport and passport.valid_until
            else None
        ),
    }


def extract_sustainability_info(subject) -> dict:
    """Extract sustainability information for display."""
    if not subject:
        return {}

    scorecard = getattr(subject, "circularity_scorecard", None)
    materials = getattr(subject, "materials_provenance", []) or []

    return {
        "recycled_content": (
            f"{scorecard.recycled_content * 100:.0f}%"
            if scorecard and scorecard.recycled_content
            else "N/A"
        ),
        "recyclable": (
            f"{scorecard.recyclable_content * 100:.0f}%"
            if scorecard and scorecard.recyclable_content
            else "N/A"
        ),
        "materials": [
            {
                "name": m.name,
                "percentage": f"{(m.mass_fraction or 0) * 100:.0f}%",
                "recycled": m.recycled or False,
            }
            for m in materials
        ],
    }
```

______________________________________________________________________

## Recycling & Waste Management

### Material Identification for Sorting

Help recycling facilities identify materials from DPP data.

```python
from dppvalidator import ValidationEngine

engine = ValidationEngine()

RECYCLABLE_MATERIALS = {
    "cotton",
    "wool",
    "silk",
    "linen",
    "hemp",
    "polyester",
    "nylon",
    "pet",
}

HAZARDOUS_INDICATORS = {"lead", "mercury", "cadmium", "pvc"}


def analyze_for_recycling(dpp_data: dict) -> dict:
    """Analyze DPP for recycling facility sorting."""
    result = engine.validate(dpp_data)

    if not result.valid:
        return {"error": "Invalid passport", "sortable": False}

    materials = dpp_data.get("credentialSubject", {}).get("materialsProvenance", [])

    analysis = {
        "sortable": True,
        "materials": [],
        "recyclable": True,
        "hazardous": False,
        "recommended_stream": "textile",
    }

    for mat in materials:
        name = mat.get("name", "").lower()
        fraction = mat.get("massFraction", 0)
        hazardous = mat.get("hazardous", False)

        analysis["materials"].append(
            {
                "name": mat.get("name"),
                "fraction": f"{fraction * 100:.1f}%",
                "recyclable": any(r in name for r in RECYCLABLE_MATERIALS),
                "hazardous": hazardous,
            }
        )

        if hazardous or any(h in name for h in HAZARDOUS_INDICATORS):
            analysis["hazardous"] = True
            analysis["recommended_stream"] = "special_handling"

    return analysis
```

______________________________________________________________________

## Customs & Border Control

### Import Compliance Verification

Verify DPP compliance for imports.

```python
from dppvalidator import ValidationEngine
from dppvalidator.vocabularies import is_valid_hs_code, is_textile_hs_code

engine = ValidationEngine(
    strict_mode=True,
    verify_signatures=True,
)


def verify_import_compliance(dpp_data: dict, declared_hs_code: str) -> dict:
    """Verify DPP compliance for customs import."""
    result = engine.validate(dpp_data)

    checks = {
        "dpp_valid": result.valid,
        "signature_verified": result.signature_valid or False,
        "issuer": result.issuer_did,
        "hs_code_valid": is_valid_hs_code(declared_hs_code),
        "is_textile": is_textile_hs_code(declared_hs_code),
        "requires_dpp": False,
        "compliance_status": "pending",
    }

    # Textiles require DPP from 2027
    if checks["is_textile"]:
        checks["requires_dpp"] = True
        checks["compliance_status"] = "compliant" if result.valid else "non_compliant"
    else:
        checks["compliance_status"] = "exempt"

    return checks
```

______________________________________________________________________

## Resale & Recommerce

### Product Authentication

Authenticate products for resale platforms.

```python
from dppvalidator import ValidationEngine

engine = ValidationEngine(verify_signatures=True)


def authenticate_for_resale(dpp_data: dict) -> dict:
    """Authenticate product for resale platform."""
    result = engine.validate(dpp_data)

    authentication = {
        "authentic": False,
        "confidence": "low",
        "details": {},
    }

    if not result.valid:
        authentication["reason"] = "Invalid passport structure"
        return authentication

    # Check signature
    if result.signature_valid:
        authentication["authentic"] = True
        authentication["confidence"] = "high"
        authentication["details"]["signature"] = {
            "verified": True,
            "issuer": result.issuer_did,
            "method": result.verification_method,
        }
    else:
        authentication["confidence"] = "medium"
        authentication["details"]["signature"] = {"verified": False}

    # Extract provenance for display
    passport = result.passport
    if passport:
        authentication["details"]["product"] = {
            "id": str(passport.id),
            "issuer": passport.issuer.name,
            "valid_from": (
                passport.valid_from.isoformat() if passport.valid_from else None
            ),
        }

    return authentication
```

______________________________________________________________________

## Next Steps

- [Validation Guide](validation.md) — Detailed validation options
- [Plugin Development](plugins.md) — Create custom validators
- [API Reference](../reference/api/validators.md) — Full API documentation
