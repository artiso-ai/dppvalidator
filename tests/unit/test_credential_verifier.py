"""Unit tests for credential verification behavior."""

import base64
from typing import Any
from unittest.mock import MagicMock

from cryptography.hazmat.primitives.asymmetric import ed25519

from dppvalidator.verifier.did import DIDDocument, DIDResolver, VerificationMethod
from dppvalidator.verifier.verifier import (
    CredentialVerifier,
    VerificationResult,
    has_vc_support,
    verify_credential,
)


class TestVerificationResultBehavior:
    """Tests for VerificationResult dataclass behavior."""

    def test_verified_requires_both_valid_and_signature(self) -> None:
        """verified property requires both valid=True and signature_valid=True."""
        # Both True
        result = VerificationResult(valid=True, signature_valid=True)
        assert result.verified is True

        # Valid but no signature check
        result = VerificationResult(valid=True, signature_valid=None)
        assert result.verified is False

        # Signature valid but overall invalid
        result = VerificationResult(valid=False, signature_valid=True)
        assert result.verified is False

    def test_errors_and_warnings_default_empty(self) -> None:
        """Errors and warnings default to empty lists."""
        result = VerificationResult(valid=True)
        assert result.errors == []
        assert result.warnings == []

    def test_can_add_errors_and_warnings(self) -> None:
        """Errors and warnings can be added."""
        result = VerificationResult(valid=False)
        result.errors.append("Error 1")
        result.warnings.append("Warning 1")

        assert len(result.errors) == 1
        assert len(result.warnings) == 1


class TestCredentialVerifierIssuerExtraction:
    """Tests for issuer extraction from credentials."""

    def test_extract_issuer_from_string(self) -> None:
        """Issuer extracted from string format."""
        verifier = CredentialVerifier()
        credential = {"issuer": "did:web:example.com"}

        result = verifier.verify(credential)
        assert result.issuer_did == "did:web:example.com"

    def test_extract_issuer_from_object(self) -> None:
        """Issuer extracted from object with id field."""
        verifier = CredentialVerifier()
        credential = {"issuer": {"id": "did:key:z6Mk...", "name": "Test Issuer"}}

        result = verifier.verify(credential)
        assert result.issuer_did == "did:key:z6Mk..."

    def test_missing_issuer_returns_none(self) -> None:
        """Missing issuer returns None for issuer_did."""
        verifier = CredentialVerifier()
        credential = {"credentialSubject": {"id": "urn:uuid:123"}}

        result = verifier.verify(credential)
        assert result.issuer_did is None


class TestCredentialVerifierProofHandling:
    """Tests for proof verification in credentials."""

    def test_no_proof_returns_warning(self) -> None:
        """Credential without proof returns warning."""
        verifier = CredentialVerifier()
        credential = {"issuer": "did:web:example.com"}

        result = verifier.verify(credential)
        assert "No proof found in credential" in result.warnings
        assert result.valid is True

    def test_proof_with_unresolvable_did_fails(self) -> None:
        """Proof with unresolvable DID returns error."""
        verifier = CredentialVerifier()
        credential = {
            "issuer": "did:web:nonexistent.example.com",
            "proof": {
                "type": "Ed25519Signature2020",
                "verificationMethod": "did:web:nonexistent.example.com#key-1",
                "proofValue": "z...",
            },
        }

        result = verifier.verify(credential)
        assert result.valid is False
        assert any("Could not resolve DID" in e for e in result.errors)

    def test_proof_with_invalid_verification_method_format(self) -> None:
        """Proof with invalid verification method format fails."""
        verifier = CredentialVerifier()
        credential = {
            "issuer": "did:web:example.com",
            "proof": {
                "type": "Ed25519Signature2020",
                "verificationMethod": "not-a-did",
                "proofValue": "z...",
            },
        }

        result = verifier.verify(credential)
        assert result.valid is False
        assert any("Could not extract DID" in e for e in result.errors)

    def test_multiple_proofs_verified(self) -> None:
        """Multiple proofs in array are all checked."""
        mock_resolver = MagicMock(spec=DIDResolver)
        mock_resolver.resolve.return_value = None

        verifier = CredentialVerifier(did_resolver=mock_resolver)
        credential = {
            "issuer": "did:web:example.com",
            "proof": [
                {
                    "type": "Ed25519Signature2020",
                    "verificationMethod": "did:web:example.com#key-1",
                    "proofValue": "z...",
                },
                {
                    "type": "Ed25519Signature2020",
                    "verificationMethod": "did:web:example.com#key-2",
                    "proofValue": "z...",
                },
            ],
        }

        verifier.verify(credential)
        # Both proofs should be attempted
        assert mock_resolver.resolve.call_count == 2

    def test_unsupported_proof_type_warning(self) -> None:
        """Unsupported proof type returns warning."""
        # Create a mock DID document with verification method
        vm = VerificationMethod(
            id="did:key:z6Mk...#key-1",
            type="Ed25519VerificationKey2020",
            controller="did:key:z6Mk...",
            public_key_jwk={"kty": "OKP", "crv": "Ed25519", "x": "abc"},
        )
        doc = DIDDocument(
            id="did:key:z6Mk...",
            verification_method=[vm],
        )

        mock_resolver = MagicMock(spec=DIDResolver)
        mock_resolver.resolve.return_value = doc

        verifier = CredentialVerifier(did_resolver=mock_resolver)
        credential = {
            "issuer": "did:key:z6Mk...",
            "proof": {
                "type": "UnknownProofType2025",
                "verificationMethod": "did:key:z6Mk...#key-1",
                "proofValue": "zbase58signature",
            },
        }

        result = verifier.verify(credential)
        assert any("Unsupported proof type" in w for w in result.warnings)


class TestBase58Decoding:
    """Tests for base58btc decoding in verifier."""

    def test_decode_valid_base58(self) -> None:
        """Valid base58btc string decodes correctly."""
        verifier = CredentialVerifier()
        # "1" in base58 = 0x00
        # "2" in base58 = 0x01
        result = verifier._decode_base58btc("2")
        assert result == b"\x01"

    def test_decode_base58_with_leading_ones(self) -> None:
        """Leading '1' characters decode to leading zero bytes."""
        verifier = CredentialVerifier()
        # "111" = three leading zeros
        result = verifier._decode_base58btc("1112")
        assert result is not None
        assert result.startswith(b"\x00\x00\x00")

    def test_decode_invalid_base58_returns_none(self) -> None:
        """Invalid base58 characters return None."""
        verifier = CredentialVerifier()
        # 'O', 'I', 'l', '0' are not in base58 alphabet
        result = verifier._decode_base58btc("O0Il")
        assert result is None


class TestVerifyData:
    """Tests for creating verification data."""

    def test_create_verify_data_removes_proof(self) -> None:
        """Verification data excludes proof object."""
        verifier = CredentialVerifier()
        credential = {
            "@context": ["https://www.w3.org/2018/credentials/v1"],
            "id": "urn:uuid:123",
            "type": ["VerifiableCredential"],
            "proof": {
                "type": "Ed25519Signature2020",
                "proofValue": "zsig...",
            },
        }
        proof: dict[str, Any] = credential["proof"]  # type: ignore[assignment]

        data = verifier._create_verify_data(credential, proof)

        assert data is not None
        # URDNA2015 produces N-Quads format, not JSON
        # The proof object should be excluded from the credential canonicalization
        assert b"proofValue" not in data
        # Data should contain the credential ID in some form
        assert b"urn:uuid:123" in data or len(data) > 0

    def test_create_verify_data_removes_proof_value(self) -> None:
        """Proof options exclude proofValue."""
        verifier = CredentialVerifier()
        # Use a credential with @context for proper URDNA2015 canonicalization
        credential = {
            "@context": ["https://www.w3.org/2018/credentials/v1"],
            "id": "urn:uuid:123",
            "type": ["VerifiableCredential"],
        }
        proof = {
            "type": "Ed25519Signature2020",
            "proofValue": "zsig...",
            "created": "2024-01-01",
        }

        data = verifier._create_verify_data(credential, proof)

        assert data is not None
        # proofValue should always be excluded from verification data
        assert b"proofValue" not in data
        # Data should be non-empty (URDNA2015 produces N-Quads)
        assert len(data) > 0


class TestJWSProofVerification:
    """Tests for JWS proof verification."""

    def test_jws_proof_without_jws_returns_none(self) -> None:
        """JWS proof without jws field returns None."""
        vm = VerificationMethod(
            id="did:key:z6Mk...#key-1",
            type="JsonWebKey2020",
            controller="did:key:z6Mk...",
            public_key_jwk={"kty": "OKP", "crv": "Ed25519", "x": "abc"},
        )

        verifier = CredentialVerifier()
        result = verifier._verify_jws_proof({}, {"type": "JsonWebSignature2020"}, vm)
        assert result is None

    def test_jws_proof_without_jwk_returns_none(self) -> None:
        """JWS proof without JWK in verification method returns None."""
        vm = VerificationMethod(
            id="did:key:z6Mk...#key-1",
            type="JsonWebKey2020",
            controller="did:key:z6Mk...",
            public_key_jwk=None,
        )

        verifier = CredentialVerifier()
        result = verifier._verify_jws_proof({}, {"jws": "eyJ..."}, vm)
        assert result is None


class TestEd25519ProofVerification:
    """Tests for Ed25519 proof verification."""

    def test_ed25519_proof_without_value_returns_none(self) -> None:
        """Ed25519 proof without proofValue returns None."""
        vm = VerificationMethod(
            id="did:key:z6Mk...#key-1",
            type="Ed25519VerificationKey2020",
            controller="did:key:z6Mk...",
            public_key_jwk={"kty": "OKP", "crv": "Ed25519", "x": "abc"},
        )

        verifier = CredentialVerifier()
        result = verifier._verify_ed25519_proof({}, {"type": "Ed25519Signature2020"}, vm)
        assert result is None

    def test_ed25519_proof_with_base64_signature(self) -> None:
        """Ed25519 proof with base64 signature round-trips through the verifier.

        Round-trips the verifier's own canonicalisation: we ask the
        verifier to produce ``verify-data`` for a (credential, proof
        options) pair, sign **those** bytes with a fresh Ed25519 key,
        attach the signature as the ``proofValue``, and then call the
        verifier — which must recompute the same canonical bytes and
        report a valid signature.

        The credential carries an ``@context`` so URDNA2015
        canonicalisation produces non-empty n-quads (the verifier's
        primary path since 0.3.2). This avoids the historical flake:
        signing JSON-canonical bytes while the verifier compares
        against URDNA2015-canonicalised bytes.
        """
        verifier = CredentialVerifier()

        # Generate the signing key.
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        vm = VerificationMethod(
            id="did:key:z6Mk...#key-1",
            type="Ed25519VerificationKey2020",
            controller="did:key:z6Mk...",
            public_key_jwk={
                "kty": "OKP",
                "crv": "Ed25519",
                "x": base64.urlsafe_b64encode(public_key.public_bytes_raw()).rstrip(b"=").decode(),
            },
        )

        # A credential with @context so URDNA2015 produces non-empty
        # canonical bytes — otherwise the verifier and the signer would
        # operate on different message bytes.
        credential = {
            "@context": ["https://www.w3.org/ns/credentials/v2"],
            "id": "urn:uuid:test",
            "type": ["VerifiableCredential"],
        }
        proof_options = {
            "type": "Ed25519Signature2020",
            "created": "2024-01-01T00:00:00Z",
            "verificationMethod": vm.id,
            "proofPurpose": "assertionMethod",
        }

        # Sign exactly what the verifier will verify.
        message = verifier._create_verify_data(credential, proof_options)
        assert message, "verify-data must be non-empty for a credential with @context"

        signature = private_key.sign(message)
        proof = {**proof_options, "proofValue": base64.b64encode(signature).decode()}

        result = verifier._verify_ed25519_proof(credential, proof, vm)
        assert result is True


class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_verify_credential_creates_verifier(self) -> None:
        """verify_credential function creates CredentialVerifier."""
        credential = {"issuer": "did:web:test.com"}
        result = verify_credential(credential)

        assert isinstance(result, VerificationResult)
        assert result.issuer_did == "did:web:test.com"

    def test_has_vc_support_returns_true(self) -> None:
        """has_vc_support returns True when cryptography is installed."""
        assert has_vc_support() is True


class TestDIDExtraction:
    """Tests for DID extraction from verification methods."""

    def test_extract_did_from_full_method_id(self) -> None:
        """DID extracted from full verification method ID."""
        verifier = CredentialVerifier()
        did = verifier._extract_did_from_method("did:web:example.com#key-1")
        assert did == "did:web:example.com"

    def test_extract_did_from_method_without_fragment(self) -> None:
        """DID extracted when no fragment present."""
        verifier = CredentialVerifier()
        did = verifier._extract_did_from_method("did:key:z6Mk...")
        assert did == "did:key:z6Mk..."

    def test_extract_did_from_non_did_returns_none(self) -> None:
        """Non-DID string returns None."""
        verifier = CredentialVerifier()
        did = verifier._extract_did_from_method("https://example.com/keys/1")
        assert did is None


class TestJWTCredentialVerification:
    """Tests for JWT credential verification behavior."""

    def test_jwt_credential_without_token_returns_error(self) -> None:
        """JWT credential without jwt field returns error."""
        verifier = CredentialVerifier()
        credential: dict[str, Any] = {
            "issuer": "did:web:example.com",
        }
        # Force JWT path by setting internal flag
        verifier._is_jwt_credential = lambda _: True  # type: ignore[method-assign]

        result = verifier._verify_jwt_credential(credential, VerificationResult(valid=True))

        assert result.signature_valid is False
        assert any("No JWT token" in e for e in result.errors)

    def test_jwt_credential_with_proof_jwt_field(self) -> None:
        """JWT token extracted from proof.jwt field."""
        mock_resolver = MagicMock(spec=DIDResolver)
        mock_resolver.resolve.return_value = None

        verifier = CredentialVerifier(did_resolver=mock_resolver)
        credential: dict[str, Any] = {
            "issuer": "did:web:example.com",
            "proof": {"jwt": "eyJhbGciOiJFZERTQSJ9.eyJpc3MiOiJkaWQ6d2ViOmV4YW1wbGUuY29tIn0.sig"},
        }

        result = verifier._verify_jwt_credential(credential, VerificationResult(valid=True))

        # Should attempt to resolve issuer DID
        assert result.issuer_did == "did:web:example.com"
        assert any("Failed to resolve issuer DID" in e for e in result.errors)

    def test_jwt_credential_invalid_format_returns_error(self) -> None:
        """Invalid JWT format returns decode error."""
        verifier = CredentialVerifier()
        credential: dict[str, Any] = {
            "issuer": "did:web:example.com",
            "jwt": "not-a-valid-jwt",
        }

        result = verifier._verify_jwt_credential(credential, VerificationResult(valid=True))

        assert result.signature_valid is False
        assert any("Invalid JWT format" in e for e in result.errors)

    def test_jwt_credential_extracts_issuer_from_payload(self) -> None:
        """Issuer extracted from JWT payload when not in credential."""
        mock_resolver = MagicMock(spec=DIDResolver)
        mock_resolver.resolve.return_value = None

        verifier = CredentialVerifier(did_resolver=mock_resolver)
        # JWT with iss claim in payload (base64url encoded: {"alg":"ES256"}.{"iss":"did:web:jwt-issuer.com"})
        credential: dict[str, Any] = {
            "jwt": "eyJhbGciOiJFUzI1NiJ9.eyJpc3MiOiJkaWQ6d2ViOmp3dC1pc3N1ZXIuY29tIn0.sig",
        }

        result = verifier._verify_jwt_credential(credential, VerificationResult(valid=True))

        # Should extract issuer from JWT payload
        assert result.issuer_did == "did:web:jwt-issuer.com"

    def test_jwt_credential_no_issuer_returns_error(self) -> None:
        """JWT without issuer anywhere returns error."""
        verifier = CredentialVerifier()
        # JWT without iss claim
        credential: dict[str, Any] = {
            "jwt": "eyJhbGciOiJFUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.sig",
        }

        result = verifier._verify_jwt_credential(credential, VerificationResult(valid=True))

        assert result.signature_valid is False
        assert any("Cannot extract issuer DID" in e for e in result.errors)

    def test_jwt_credential_with_kid_uses_specific_key(self) -> None:
        """JWT with kid header uses specific verification method."""
        vm = VerificationMethod(
            id="did:web:example.com#key-specific",
            type="JsonWebKey2020",
            controller="did:web:example.com",
            public_key_jwk={"kty": "EC", "crv": "P-256", "x": "test", "y": "test"},
        )
        doc = DIDDocument(
            id="did:web:example.com",
            verification_method=[vm],
        )

        mock_resolver = MagicMock(spec=DIDResolver)
        mock_resolver.resolve.return_value = doc

        verifier = CredentialVerifier(did_resolver=mock_resolver)
        # JWT with kid in header
        credential: dict[str, Any] = {
            "issuer": "did:web:example.com",
            "jwt": "eyJhbGciOiJFUzI1NiIsImtpZCI6ImRpZDp3ZWI6ZXhhbXBsZS5jb20ja2V5LXNwZWNpZmljIn0.eyJpc3MiOiJkaWQ6d2ViOmV4YW1wbGUuY29tIn0.sig",
        }

        result = verifier._verify_jwt_credential(credential, VerificationResult(valid=True))

        # Should use the specific key from kid
        assert result.verification_method == "did:web:example.com#key-specific"

    def test_jwt_credential_fallback_to_assertion_method(self) -> None:
        """JWT without kid falls back to assertionMethod."""
        vm = VerificationMethod(
            id="did:web:example.com#assertion-key",
            type="JsonWebKey2020",
            controller="did:web:example.com",
            public_key_jwk={"kty": "EC", "crv": "P-256", "x": "test", "y": "test"},
        )
        doc = DIDDocument(
            id="did:web:example.com",
            verification_method=[vm],
            assertion_method=["did:web:example.com#assertion-key"],
        )

        mock_resolver = MagicMock(spec=DIDResolver)
        mock_resolver.resolve.return_value = doc

        verifier = CredentialVerifier(did_resolver=mock_resolver)
        credential: dict[str, Any] = {
            "issuer": "did:web:example.com",
            "jwt": "eyJhbGciOiJFUzI1NiJ9.eyJpc3MiOiJkaWQ6d2ViOmV4YW1wbGUuY29tIn0.sig",
        }

        result = verifier._verify_jwt_credential(credential, VerificationResult(valid=True))

        # Should use assertion method key
        assert result.verification_method == "did:web:example.com#assertion-key"

    def test_jwt_credential_no_suitable_key_returns_error(self) -> None:
        """JWT without suitable verification method returns error."""
        vm = VerificationMethod(
            id="did:web:example.com#key-no-jwk",
            type="Ed25519VerificationKey2020",
            controller="did:web:example.com",
            public_key_jwk=None,  # No JWK
        )
        doc = DIDDocument(
            id="did:web:example.com",
            verification_method=[vm],
        )

        mock_resolver = MagicMock(spec=DIDResolver)
        mock_resolver.resolve.return_value = doc

        verifier = CredentialVerifier(did_resolver=mock_resolver)
        credential: dict[str, Any] = {
            "issuer": "did:web:example.com",
            "jwt": "eyJhbGciOiJFUzI1NiJ9.eyJpc3MiOiJkaWQ6d2ViOmV4YW1wbGUuY29tIn0.sig",
        }

        result = verifier._verify_jwt_credential(credential, VerificationResult(valid=True))

        assert result.signature_valid is False
        assert any("No suitable verification method" in e for e in result.errors)

    def test_jwt_credential_verification_exception_handled(self) -> None:
        """Exception during JWT verification is handled gracefully."""
        vm = VerificationMethod(
            id="did:web:example.com#key-1",
            type="JsonWebKey2020",
            controller="did:web:example.com",
            public_key_jwk={"kty": "EC", "crv": "P-256", "x": "invalid", "y": "invalid"},
        )
        doc = DIDDocument(
            id="did:web:example.com",
            verification_method=[vm],
        )

        mock_resolver = MagicMock(spec=DIDResolver)
        mock_resolver.resolve.return_value = doc

        verifier = CredentialVerifier(did_resolver=mock_resolver)
        credential: dict[str, Any] = {
            "issuer": "did:web:example.com",
            "jwt": "eyJhbGciOiJFUzI1NiJ9.eyJpc3MiOiJkaWQ6d2ViOmV4YW1wbGUuY29tIn0.invalidsig",
        }

        result = verifier._verify_jwt_credential(credential, VerificationResult(valid=True))

        # Should handle exception and return error
        assert result.signature_valid is False
        assert len(result.errors) > 0


class TestVerificationMethodNotFound:
    """Tests for verification method resolution edge cases."""

    def test_verification_method_not_in_did_document(self) -> None:
        """Verification method ID not found in DID document returns error."""
        vm = VerificationMethod(
            id="did:web:example.com#different-key",
            type="Ed25519VerificationKey2020",
            controller="did:web:example.com",
            public_key_jwk={"kty": "OKP", "crv": "Ed25519", "x": "abc"},
        )
        doc = DIDDocument(
            id="did:web:example.com",
            verification_method=[vm],
        )

        mock_resolver = MagicMock(spec=DIDResolver)
        mock_resolver.resolve.return_value = doc

        verifier = CredentialVerifier(did_resolver=mock_resolver)
        credential = {
            "issuer": "did:web:example.com",
            "proof": {
                "type": "Ed25519Signature2020",
                "verificationMethod": "did:web:example.com#nonexistent-key",
                "proofValue": "z...",
            },
        }

        result = verifier.verify(credential)

        assert result.valid is False
        assert any("Verification method not found" in e for e in result.errors)


class TestEd25519ProofEdgeCases:
    """Tests for Ed25519 proof verification edge cases."""

    def test_ed25519_proof_with_base64_non_multibase(self) -> None:
        """Ed25519 proof with standard base64 (not multibase) is decoded."""
        vm = VerificationMethod(
            id="did:key:z6Mk...#key-1",
            type="Ed25519VerificationKey2020",
            controller="did:key:z6Mk...",
            public_key_jwk={"kty": "OKP", "crv": "Ed25519", "x": "abc"},
        )

        verifier = CredentialVerifier()
        # Non-multibase (no 'z' prefix) - should decode as base64
        proof = {
            "type": "Ed25519Signature2020",
            "proofValue": base64.b64encode(b"signature-bytes").decode(),
        }

        # This will fail signature verification but should decode the signature
        result = verifier._verify_ed25519_proof({"id": "test"}, proof, vm)

        # Returns None or False (verification fails but decoding works)
        assert result in (None, False)

    def test_ed25519_proof_create_verify_data_failure(self) -> None:
        """Ed25519 proof handles verify data creation failure."""
        vm = VerificationMethod(
            id="did:key:z6Mk...#key-1",
            type="Ed25519VerificationKey2020",
            controller="did:key:z6Mk...",
            public_key_jwk={"kty": "OKP", "crv": "Ed25519", "x": "abc"},
        )

        verifier = CredentialVerifier()
        # Mock _create_verify_data to return None
        verifier._create_verify_data = lambda _c, _p: None  # type: ignore[method-assign]

        proof = {
            "type": "Ed25519Signature2020",
            "proofValue": "zbase58sig",
        }

        result = verifier._verify_ed25519_proof({"id": "test"}, proof, vm)
        assert result is None

    def test_ed25519_proof_invalid_signature_bytes(self) -> None:
        """Ed25519 proof with invalid signature bytes returns None."""
        vm = VerificationMethod(
            id="did:key:z6Mk...#key-1",
            type="Ed25519VerificationKey2020",
            controller="did:key:z6Mk...",
            public_key_jwk={"kty": "OKP", "crv": "Ed25519", "x": "abc"},
        )

        verifier = CredentialVerifier()
        # Mock _decode_base58btc to return None
        verifier._decode_base58btc = lambda _: None  # type: ignore[method-assign]

        proof = {
            "type": "Ed25519Signature2020",
            "proofValue": "zInvalidBase58",
        }

        result = verifier._verify_ed25519_proof({"id": "test"}, proof, vm)
        assert result is None


class TestCreateVerifyDataFallback:
    """Tests for URDNA2015 to JSON fallback in verify data creation."""

    def test_create_verify_data_json_fallback(self) -> None:
        """Verify data falls back to JSON when URDNA2015 fails."""
        verifier = CredentialVerifier()
        # Credential with invalid @context that will fail URDNA2015 normalization
        credential = {
            "@context": "not-a-valid-url",
            "id": "urn:uuid:test",
            "type": ["VerifiableCredential"],
        }
        proof = {
            "type": "Ed25519Signature2020",
            "created": "2024-01-01",
            "proofValue": "zsig...",  # This should be excluded
        }

        data = verifier._create_verify_data(credential, proof)

        assert data is not None
        # Data should contain credential content
        assert len(data) > 0
        # proofValue should always be excluded from verification data
        assert b"zsig" not in data

    def test_create_verify_data_urdna2015_success(self) -> None:
        """Verify data uses URDNA2015 when @context present."""
        verifier = CredentialVerifier()
        credential = {
            "@context": ["https://www.w3.org/2018/credentials/v1"],
            "id": "urn:uuid:test",
            "type": ["VerifiableCredential"],
        }
        proof = {
            "type": "Ed25519Signature2020",
            "created": "2024-01-01",
        }

        data = verifier._create_verify_data(credential, proof)

        assert data is not None
        # URDNA2015 produces N-Quads format
        assert len(data) > 0


class TestDataIntegrityProofSignatureFailure:
    """Tests for signature verification failure handling."""

    def test_signature_verification_returns_false_when_verify_fails(self) -> None:
        """Signature verification returning False is captured in result."""
        vm = VerificationMethod(
            id="did:web:example.com#key-1",
            type="Ed25519VerificationKey2020",
            controller="did:web:example.com",
            public_key_jwk={"kty": "OKP", "crv": "Ed25519", "x": "abc"},
        )

        verifier = CredentialVerifier()

        # Test _verify_ed25519_proof directly with invalid signature
        credential = {"id": "test"}
        proof = {
            "type": "Ed25519Signature2020",
            "proofValue": "zInvalidSignature",
        }

        # This should return False or None (verification fails)
        result = verifier._verify_ed25519_proof(credential, proof, vm)

        # Returns None or False when verification fails
        assert result in (None, False)


class TestJWSProofVerificationPaths:
    """Tests for JWS proof verification paths."""

    def test_jws_proof_type_handled(self) -> None:
        """JsonWebSignature2020 proof type is recognized."""
        vm = VerificationMethod(
            id="did:web:example.com#key-1",
            type="JsonWebKey2020",
            controller="did:web:example.com",
            public_key_jwk={"kty": "EC", "crv": "P-256", "x": "test", "y": "test"},
        )
        doc = DIDDocument(
            id="did:web:example.com",
            verification_method=[vm],
        )

        mock_resolver = MagicMock(spec=DIDResolver)
        mock_resolver.resolve.return_value = doc

        verifier = CredentialVerifier(did_resolver=mock_resolver)
        credential = {
            "issuer": "did:web:example.com",
            "proof": {
                "type": "JsonWebSignature2020",
                "verificationMethod": "did:web:example.com#key-1",
                "jws": "eyJhbGciOiJFUzI1NiJ9..invalid",
            },
        }

        result = verifier.verify(credential)

        # Should process the JWS proof type
        assert result.verification_method == "did:web:example.com#key-1"

    def test_jws_proof_exception_handling(self) -> None:
        """JWS proof verification handles exceptions gracefully."""
        vm = VerificationMethod(
            id="did:web:example.com#key-1",
            type="JsonWebKey2020",
            controller="did:web:example.com",
            public_key_jwk={"kty": "EC", "crv": "P-256", "x": "invalid", "y": "invalid"},
        )

        verifier = CredentialVerifier()

        # Test _verify_jws_proof with invalid JWS
        proof = {"jws": "completely-invalid-jws"}
        result = verifier._verify_jws_proof({}, proof, vm)

        # Should return None or False on exception/verification failure
        assert result in (None, False)


class TestCreateVerifyDataExceptionHandling:
    """Tests for exception handling in verify data creation."""

    def test_create_verify_data_handles_general_exception(self) -> None:
        """Create verify data handles general exceptions."""
        verifier = CredentialVerifier()

        # Create a credential that will cause an exception during processing
        # Use an object that can't be JSON serialized in the fallback
        class NonSerializable:
            pass

        credential = {
            "@context": "invalid",
            "bad_field": NonSerializable(),
        }
        proof = {"type": "test"}

        result = verifier._create_verify_data(credential, proof)

        # Should return None on exception
        assert result is None


class TestDataIntegrityProofVerification:
    """Tests for DataIntegrityProof type handling."""

    def test_data_integrity_proof_type_handled(self) -> None:
        """DataIntegrityProof type is recognized as Ed25519."""
        vm = VerificationMethod(
            id="did:web:example.com#key-1",
            type="Ed25519VerificationKey2020",
            controller="did:web:example.com",
            public_key_jwk={"kty": "OKP", "crv": "Ed25519", "x": "abc"},
        )
        doc = DIDDocument(
            id="did:web:example.com",
            verification_method=[vm],
        )

        mock_resolver = MagicMock(spec=DIDResolver)
        mock_resolver.resolve.return_value = doc

        verifier = CredentialVerifier(did_resolver=mock_resolver)
        credential = {
            "issuer": "did:web:example.com",
            "proof": {
                "type": "DataIntegrityProof",
                "verificationMethod": "did:web:example.com#key-1",
                "proofValue": "zInvalidSig",
            },
        }

        result = verifier.verify(credential)

        # Should process the DataIntegrityProof type
        assert result.verification_method == "did:web:example.com#key-1"
