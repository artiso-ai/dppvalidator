"""Verifiable Credential verification module."""

from dppvalidator.verifier.did import DIDDocument, DIDResolver, resolve_did
from dppvalidator.verifier.signatures import (
    SignatureVerifier,
    verify_signature,
)
from dppvalidator.verifier.verifier import (
    CredentialVerifier,
    VerificationResult,
    verify_credential,
)

__all__ = [
    # DID Resolution
    "DIDResolver",
    "DIDDocument",
    "resolve_did",
    # Signature Verification
    "SignatureVerifier",
    "verify_signature",
    # Credential Verification
    "CredentialVerifier",
    "VerificationResult",
    "verify_credential",
]
