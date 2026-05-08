# EU DPP Ontology Alignment

dppvalidator aligns UNTP Digital Product Passport data with EU Digital Product
Passport ontologies defined by the CIRPASS-2 project and TalTech research.

## Overview

The EU Ecodesign for Sustainable Products Regulation (ESPR) mandates Digital
Product Passports with specific semantic requirements. dppvalidator provides
vocabulary modules that map UNTP data structures to EU DPP ontology terms.

## Supported Ontologies

| Ontology              | Namespace                      | Description               |
| --------------------- | ------------------------------ | ------------------------- |
| EU DPP Core           | `http://dpp.taltech.ee/EUDPP#` | Product lifecycle classes |
| Actors & Roles        | `http://dpp.taltech.ee/EUDPP#` | Supply chain participants |
| Substances of Concern | `http://dpp.taltech.ee/EUDPP#` | REACH/SVHC compliance     |
| LCA Module            | `http://dpp.cea.fr/EUDPP/LCA#` | PEF/OEF impact categories |

## Vocabulary Modules

### Actor Roles (`eudpp_actors.py`)

Defines 24 actor and role classes per ESPR Art 2(37-55):

```python
from dppvalidator.vocabularies.eudpp_actors import (
    EUDPPActorClass,
    EUDPPRoleClass,
    Actor,
)

# Economic operator roles
print(EUDPPRoleClass.MANUFACTURER.value)  # eudpp:ManufacturerRole
print(EUDPPRoleClass.IMPORTER.value)  # eudpp:ImporterRole
print(EUDPPRoleClass.DISTRIBUTOR.value)  # eudpp:DistributorRole
```

### LCA Impact Categories (`eudpp_lca.py`)

Provides 16 PEF 3.1 impact categories per ESPR Annex I:

```python
from dppvalidator.vocabularies.eudpp_lca import (
    ImpactCategory,
    LCAClass,
)

# Climate change impact
print(ImpactCategory.CLIMATE_CHANGE.value)
print(ImpactCategory.OZONE_DEPLETION.value)
print(ImpactCategory.WATER_USE.value)
```

### Substances of Concern (`eudpp_substances.py`)

REACH/SVHC substance vocabulary for chemical compliance:

```python
from dppvalidator.vocabularies.eudpp_substances import (
    Substance,
    SubstanceIdentifierType,
)

# Validate CAS/EINECS identifiers
substance = Substance(
    cas_number="50-00-0",
    name="Formaldehyde",
)
```

### Core Classes (`eudpp_classes.py`)

EU DPP Core Ontology class definitions:

```python
from dppvalidator.vocabularies.eudpp_classes import (
    EUDPPClass,
    EUDPPProperty,
)

# Product passport class
print(EUDPPClass.DIGITAL_PRODUCT_PASSPORT.value)
print(EUDPPClass.PRODUCT.value)
```

### Relation Mapping (`eudpp_relations.py`)

UNTP to EU DPP property mappings:

```python
from dppvalidator.vocabularies.eudpp_relations import ProductRelationMapper

mapper = ProductRelationMapper()
eudpp_property = mapper.map_untp_property("manufacturer")
```

## EU DPP Export

Convert validated UNTP DPPs to EU DPP JSON-LD format:

```python
from dppvalidator.exporters import EUDPPJsonLDExporter
from dppvalidator.validators import ValidationEngine

# Validate first
engine = ValidationEngine()
result = engine.validate(dpp_data)

if result.valid and result.passport:
    # Export to EU DPP format (auto-detects UNTP version from the
    # passport's class — works for both v0.6 and v0.7 inputs).
    exporter = EUDPPJsonLDExporter()
    eudpp_jsonld = exporter.export(result.passport)
```

### Per-version mapping (Phase 3c)

The exporter is **version-aware**. UNTP v0.6 and v0.7 use different
source-side spellings (`serialNumber` vs `itemNumber`,
`producedByParty` vs `relatedParty`, …) but most map to the same EU
DPP target URI. The mapping table in
[`vocabularies/ontology.py:TermMapping`](https://github.com/artiso-ai/dppvalidator/blob/main/src/dppvalidator/vocabularies/ontology.py)
carries `untp_v0_6` / `untp_v0_7` columns; the exporter reads the
right one per call.

- **`schema_version=None` (default)** — auto-detect from the passport
  class's module path (`dppvalidator.models.v0_X.*`).
- **`schema_version="0.6.1"` or `"0.7.0"`** — pin explicitly. Useful
  for downstream-compat scenarios (e.g. forcing v0.6 mapping on a
  v0.7 passport).

Terms removed in a given version (the `TERM_REMOVED` sentinel —
currently `gtin` for v0.7) drop out of that version's mapper index.
The full mapping table and per-version usage examples are in the
[EU DPP export guide](../guides/eudpp-export.md).

## Ontology Data Files

Bundled Turtle files for offline validation:

```
vocabularies/data/ontologies/
├── eudpp_core.ttl          # Core ontology
├── product_dpp.ttl         # Product DPP classes
├── actors_roles.ttl        # Actor and role hierarchy
├── soc.ttl                 # Substances of Concern
└── lca.ttl                 # LCA impact categories
```

## References

- [EU DPP Core Ontology](https://doi.org/10.5281/zenodo.15270342) (TalTech)
- [CIRPASS-2 Vocabulary Hub](https://dpp.vocabulary-hub.eu/)
- [ESPR Regulation](https://eur-lex.europa.eu/eli/reg/2024/1781)
- [PEF 3.1 Methodology](https://eplca.jrc.ec.europa.eu/LCDN/developerEF.xhtml)

## See Also

- [CIRPASS-2 Implementation](cirpass-implementation.md)
- [Seven-Layer Validation](validation-layers.md)
- [JSON-LD Export Guide](../guides/jsonld.md)
