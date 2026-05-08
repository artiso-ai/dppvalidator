______________________________________________________________________

paths:

- "src/\*\*/\*.py"
- "tests/\*\*/\*.py"

______________________________________________________________________

# DPP Domain Guidelines

## Domain knowledge

- DPP = Digital Product Passport (EU ESPR regulation).
- Use CIRPASS and UNECE ontologies as reference.
- Material codes follow ISO 2076 (e.g. `CO`=Cotton, `EL`=Elastane).
- Country codes use ISO 3166-1 alpha-2.
- Product IDs use GTIN-13 or equivalent.

## Validation rules

- Material percentages must sum to 100%.
- All mandatory ESPR fields must be present.
- URIs must be valid and follow semantic web standards.
- Supply chain nodes must have valid roles: `Manufacturer`, `Supplier`, `Recycler`.

## Pydantic v2 patterns (do not regress to v1)

- Use `Field()` with `description=` for documentation.
- Use `@field_validator` decorator with `@classmethod` (NOT v1 `@validator`).
- Use `@model_validator(mode="after")` for cross-field validation (NOT v1 `@root_validator`).
- Use `model_dump()` instead of v1 `.dict()`.
- Use `model_dump_json()` instead of v1 `.json()`.
- Use `model_validate()` instead of v1 `.parse_obj()`.
- Use `X | None` type syntax instead of `Optional[X]`.
- Use `ConfigDict` class attribute instead of inner `Config` class.
- Export to JSON-LD with `@context` and `@type`.
