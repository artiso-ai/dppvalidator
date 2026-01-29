# Models API

Pydantic models for Digital Product Passport entities.

## DigitalProductPassport

The main passport model representing a W3C Verifiable Credential.

::: dppvalidator.models.DigitalProductPassport
options:
show_source: false
members:
\- id
\- type
\- issuer
\- valid_from
\- valid_until
\- credential_subject

## CredentialIssuer

The issuer of a Digital Product Passport.

::: dppvalidator.models.CredentialIssuer
options:
show_source: false

## Product

Product information within a passport.

::: dppvalidator.models.Product
options:
show_source: false

## ProductPassport

The credential subject containing product passport data.

::: dppvalidator.models.ProductPassport
options:
show_source: false

## Measure

A measurement with value and unit.

::: dppvalidator.models.Measure
options:
show_source: false

## Usage Example

```python
from dppvalidator.models import (
    DigitalProductPassport,
    CredentialIssuer,
    Product,
    Measure,
)

# Create a passport
passport = DigitalProductPassport(
    id="https://example.com/dpp/001",
    issuer=CredentialIssuer(id="https://example.com/issuer", name="Acme Corp"),
)

# Access fields
print(passport.id)
print(passport.issuer.name)

# Serialize to dict
data = passport.model_dump(by_alias=True)

# Serialize to JSON
json_str = passport.model_dump_json(by_alias=True)
```
