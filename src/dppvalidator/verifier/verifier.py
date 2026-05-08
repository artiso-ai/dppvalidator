"""Verifiable Credential verification for Digital Product Passports.

This module provides verification of W3C Verifiable Credentials embedded
in Digital Product Passports.

Supported Features:
    - Data Integrity Proofs (Ed25519Signature2020, DataIntegrityProof)
    - JWS Proofs (JsonWebSignature2020)
    - JWT Credentials (ES256, ES384, Ed25519)
    - DID Resolution (did:web, did:key)
    - URDNA2015 RDF Canonicalization
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from typing import Any

import base58
import jwt
from pyld import jsonld
from pyld.jsonld import JsonLdError

from dppvalidator.logging import get_logger
from dppvalidator.verifier.did import DIDResolver
from dppvalidator.verifier.signatures import SignatureVerifier, verify_jws

logger = get_logger(__name__)


@dataclass
class VerificationResult:
    """Result of credential verification."""

    valid: bool
    signature_valid: bool | None = None
    issuer_did: str | None = None
    verification_method: str | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def verified(self) -> bool:
        """Check if the credential is fully verified."""
        return self.valid and self.signature_valid is True


class CredentialVerifier:
    """Verify Verifiable Credentials in Digital Product Passports.

    Supports verification of:
        - Data Integrity Proofs (embedded proofs)
        - Enveloped Proofs (JWS/JWT format)
        - did:web and did:key issuer resolution

    Note:
        JWT credential verification is experimental. For production use,
        prefer Data Integrity Proofs (Ed25519Signature2020).

        Canonicalization uses simplified JSON sorting. For credentials
        requiring strict W3C compliance, implement URDNA2015.
    """

    def __init__(
        self,
        did_resolver: DIDResolver | None = None,
        signature_verifier: SignatureVerifier | None = None,
    ) -> None:
        """Initialize the credential verifier.

        Args:
            did_resolver: Custom DID resolver, or None to use default
            signature_verifier: Custom signature verifier, or None to use default

        """
        self._did_resolver = did_resolver or DIDResolver()
        self._signature_verifier = signature_verifier or SignatureVerifier()

    def verify(self, credential: dict[str, Any]) -> VerificationResult:
        """Verify a Verifiable Credential.

        Args:
            credential: The credential as a dict (parsed JSON)

        Returns:
            VerificationResult with verification status

        """
        result = VerificationResult(valid=True)

        # Extract issuer first (always available)
        issuer = self._extract_issuer(credential)
        if issuer:
            result.issuer_did = issuer

        # Determine proof type and verify
        proof = credential.get("proof")
        if proof:
            # Data Integrity Proof (embedded)
            return self._verify_data_integrity_proof(credential, proof, result)

        # Check for JWT/JWS format (enveloped proof)
        if self._is_jwt_credential(credential):
            return self._verify_jwt_credential(credential, result)

        # No proof found
        result.warnings.append("No proof found in credential")
        return result

    def _extract_issuer(self, credential: dict[str, Any]) -> str | None:
        """Extract the issuer DID from a credential."""
        issuer = credential.get("issuer")
        if isinstance(issuer, str):
            return issuer
        if isinstance(issuer, dict):
            return issuer.get("id")
        return None

    def _is_jwt_credential(self, _credential: dict[str, Any]) -> bool:
        """Check if the credential is in JWT format."""
        # JWT credentials have a specific structure or are passed as strings
        return False  # We expect parsed credentials, not JWT strings

    def _verify_data_integrity_proof(
        self,
        credential: dict[str, Any],
        proof: dict[str, Any] | list[dict[str, Any]],
        result: VerificationResult,
    ) -> VerificationResult:
        """Verify a Data Integrity Proof."""
        # Handle proof as list or single object
        proofs = proof if isinstance(proof, list) else [proof]

        for p in proofs:
            proof_type = p.get("type", "")
            verification_method = p.get("verificationMethod", "")
            result.verification_method = verification_method

            # Resolve the verification method
            did = self._extract_did_from_method(verification_method)
            if not did:
                result.errors.append(f"Could not extract DID from: {verification_method}")
                result.valid = False
                continue

            did_doc = self._did_resolver.resolve(did)
            if not did_doc:
                result.errors.append(f"Could not resolve DID: {did}")
                result.valid = False
                continue

            vm = did_doc.get_verification_method(verification_method)
            if not vm:
                result.errors.append(f"Verification method not found: {verification_method}")
                result.valid = False
                continue

            # Verify based on proof type
            if proof_type in ("Ed25519Signature2020", "DataIntegrityProof"):
                sig_valid = self._verify_ed25519_proof(credential, p, vm)
            elif proof_type == "JsonWebSignature2020":
                sig_valid = self._verify_jws_proof(credential, p, vm)
            else:
                result.warnings.append(f"Unsupported proof type: {proof_type}")
                sig_valid = None

            result.signature_valid = sig_valid
            if sig_valid is False:
                result.valid = False
                result.errors.append("Signature verification failed")

        return result

    def _extract_did_from_method(self, verification_method: str) -> str | None:
        """Extract the DID from a verification method ID."""
        if verification_method.startswith("did:"):
            # Format: did:method:identifier#fragment
            parts = verification_method.split("#")
            return parts[0]
        return None

    def _verify_ed25519_proof(
        self,
        credential: dict[str, Any],
        proof: dict[str, Any],
        vm: Any,
    ) -> bool | None:
        """Verify an Ed25519 signature proof."""
        try:
            # Get proof value
            proof_value = proof.get("proofValue", "")
            if not proof_value:
                return None

            # Decode multibase-encoded signature (z prefix = base58btc)
            if proof_value.startswith("z"):
                signature = self._decode_base58btc(proof_value[1:])
            else:
                signature = base64.b64decode(proof_value)

            if not signature:
                return None

            # Create the message to verify (canonicalized credential minus proof)
            message = self._create_verify_data(credential, proof)
            if not message:
                return None

            # Verify using the verification method
            return self._signature_verifier.verify_from_method(signature, message, vm)

        except Exception as e:
            logger.warning("Ed25519 proof verification error: %s", e)
            return None

    def _verify_jws_proof(
        self,
        _credential: dict[str, Any],
        proof: dict[str, Any],
        vm: Any,
    ) -> bool | None:
        """Verify a JWS proof."""
        try:
            jws = proof.get("jws", "")
            if not jws:
                return None

            if not vm.public_key_jwk:
                return None

            valid, _ = verify_jws(jws, vm.public_key_jwk)
            return valid

        except Exception as e:
            logger.warning("JWS proof verification error: %s", e)
            return None

    def _create_verify_data(
        self,
        credential: dict[str, Any],
        proof: dict[str, Any],
    ) -> bytes | None:
        """Create the data to be verified using URDNA2015 RDF canonicalization.

        Uses pyld's normalize() with URDNA2015 algorithm for W3C Data Integrity
        compliant canonicalization. Falls back to simplified JSON canonicalization
        if URDNA2015 fails (e.g., missing @context).

        Args:
            credential: The credential document (without proof for verification)
            proof: The proof object (without proofValue)

        Returns:
            Canonicalized bytes for signature verification, or None on failure
        """
        try:
            # Remove proof from credential for verification
            cred_copy = {k: v for k, v in credential.items() if k != "proof"}

            # Create proof options (proof without proofValue)
            proof_options = {k: v for k, v in proof.items() if k != "proofValue"}

            # Use URDNA2015 RDF canonicalization via pyld
            try:
                cred_normalized = jsonld.normalize(
                    cred_copy,
                    {"algorithm": "URDNA2015", "format": "application/n-quads"},
                )
                proof_normalized = jsonld.normalize(
                    proof_options,
                    {"algorithm": "URDNA2015", "format": "application/n-quads"},
                )
                return (proof_normalized + cred_normalized).encode("utf-8")

            except JsonLdError as e:
                # Fallback to simplified canonicalization for non-JSON-LD documents
                logger.debug("URDNA2015 failed, using JSON fallback: %s", e)
                cred_json = json.dumps(cred_copy, sort_keys=True, separators=(",", ":"))
                proof_json = json.dumps(proof_options, sort_keys=True, separators=(",", ":"))
                return (proof_json + cred_json).encode("utf-8")

        except Exception as e:
            logger.warning("Failed to create verify data: %s", e)
            return None

    def _decode_base58btc(self, encoded: str) -> bytes | None:
        """Decode a base58btc string using the base58 library.

        Args:
            encoded: Base58-encoded string

        Returns:
            Decoded bytes, or None if decoding fails
        """
        try:
            return base58.b58decode(encoded)
        except Exception:
            return None

    def _verify_jwt_credential(
        self,
        credential: dict[str, Any],
        result: VerificationResult,
    ) -> VerificationResult:
        """Verify a JWT-encoded credential.

        Supports ES256, ES384, and EdDSA (Ed25519) algorithms.
        Resolves the issuer DID to obtain the public key for verification.

        Args:
            credential: The JWT credential containing a 'jwt' field or proof.jwt
            result: The verification result to update

        Returns:
            VerificationResult with verification status
        """
        try:
            # Extract JWT token from credential
            jwt_token = credential.get("jwt")
            if not jwt_token:
                proof = credential.get("proof", {})
                jwt_token = proof.get("jwt") if isinstance(proof, dict) else None

            if not jwt_token:
                result.errors.append("No JWT token found in credential")
                result.signature_valid = False
                return result

            # Decode header to get algorithm and key ID
            try:
                header = jwt.get_unverified_header(jwt_token)
            except jwt.exceptions.DecodeError as e:
                result.errors.append(f"Invalid JWT format: {e}")
                result.signature_valid = False
                return result

            kid = header.get("kid")

            # Extract issuer DID using existing method
            issuer_did = self._extract_issuer(credential)
            if not issuer_did:
                # Try to get issuer from JWT payload
                try:
                    unverified = jwt.decode(jwt_token, options={"verify_signature": False})
                    issuer_did = unverified.get("iss")
                except Exception:
                    pass

            if not issuer_did:
                result.errors.append("Cannot extract issuer DID for JWT verification")
                result.signature_valid = False
                return result

            result.issuer_did = issuer_did

            # Resolve DID document
            doc = self._did_resolver.resolve(issuer_did)
            if not doc:
                result.errors.append(f"Failed to resolve issuer DID: {issuer_did}")
                result.signature_valid = False
                return result

            # Find verification method
            vm = None
            if kid:
                vm = doc.get_verification_method(kid)
            if not vm:
                assertion_methods = doc.get_assertion_methods()
                vm = assertion_methods[0] if assertion_methods else None
            if not vm:
                vm = doc.verification_method[0] if doc.verification_method else None

            if not vm or not vm.public_key_jwk:
                result.errors.append("No suitable verification method with JWK found")
                result.signature_valid = False
                return result

            result.verification_method = vm.id

            # Use verify_jws which handles JWK conversion internally
            try:
                valid, _ = verify_jws(jwt_token, vm.public_key_jwk)
                result.signature_valid = valid
                if not valid:
                    result.errors.append("JWT signature verification failed")
            except Exception as e:
                result.errors.append(f"JWT signature verification failed: {e}")
                result.signature_valid = False

            return result

        except Exception as e:
            logger.warning("JWT credential verification error: %s", e)
            result.errors.append(f"JWT verification error: {e}")
            result.signature_valid = False
            return result


def verify_credential(credential: dict[str, Any]) -> VerificationResult:
    """Verify a Verifiable Credential using the default verifier.

    Args:
        credential: The credential as a dict

    Returns:
        VerificationResult with verification status

    """
    verifier = CredentialVerifier()
    return verifier.verify(credential)


def has_vc_support() -> bool:
    """Check if VC verification dependencies are installed."""
    return True
