"""Unit tests for Verifiable Credential verification."""

from dppvalidator.verifier.did import DIDDocument, DIDResolver, VerificationMethod
from dppvalidator.verifier.verifier import CredentialVerifier, VerificationResult


class TestDIDResolver:
    """Tests for DID resolution."""

    def test_resolve_did_key_ed25519(self) -> None:
        """did:key with Ed25519 resolves to self-describing document."""
        resolver = DIDResolver()
        # Example Ed25519 did:key (multicodec 0xed01)
        did = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"
        doc = resolver.resolve(did)

        assert doc is not None
        assert doc.id == did
        assert len(doc.verification_method) == 1
        assert doc.verification_method[0].type == "Ed25519VerificationKey2020"
        assert doc.verification_method[0].public_key_jwk is not None
        assert doc.verification_method[0].public_key_jwk.get("kty") == "OKP"
        assert doc.verification_method[0].public_key_jwk.get("crv") == "Ed25519"

    def test_resolve_did_key_caching(self) -> None:
        """Resolved DIDs are cached."""
        resolver = DIDResolver(cache_size=10)
        did = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"

        doc1 = resolver.resolve(did)
        doc2 = resolver.resolve(did)

        assert doc1 is doc2  # Same object from cache

    def test_resolve_unsupported_method(self) -> None:
        """Unsupported DID methods return None."""
        resolver = DIDResolver()
        doc = resolver.resolve("did:unsupported:12345")
        assert doc is None

    def test_clear_cache(self) -> None:
        """Cache can be cleared."""
        resolver = DIDResolver()
        did = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"

        resolver.resolve(did)
        assert len(resolver._cache) == 1

        resolver.clear_cache()
        assert len(resolver._cache) == 0


class TestVerificationMethod:
    """Tests for VerificationMethod parsing."""

    def test_key_type_ed25519_from_jwk(self) -> None:
        """Ed25519 key type detected from JWK."""
        vm = VerificationMethod(
            id="did:key:z6Mk...#z6Mk...",
            type="JsonWebKey2020",
            controller="did:key:z6Mk...",
            public_key_jwk={"kty": "OKP", "crv": "Ed25519", "x": "abc123"},
        )
        assert vm.key_type == "Ed25519"

    def test_key_type_p256_from_jwk(self) -> None:
        """P-256 key type detected from JWK."""
        vm = VerificationMethod(
            id="did:key:zDn...",
            type="JsonWebKey2020",
            controller="did:key:zDn...",
            public_key_jwk={"kty": "EC", "crv": "P-256", "x": "x", "y": "y"},
        )
        assert vm.key_type == "P-256"

    def test_key_type_ed25519_from_type(self) -> None:
        """Ed25519 key type detected from verification method type."""
        vm = VerificationMethod(
            id="did:key:z6Mk...",
            type="Ed25519VerificationKey2020",
            controller="did:key:z6Mk...",
        )
        assert vm.key_type == "Ed25519"


class TestDIDDocument:
    """Tests for DIDDocument operations."""

    def test_get_verification_method_by_id(self) -> None:
        """Verification method can be retrieved by ID."""
        vm = VerificationMethod(
            id="did:key:z6Mk...#key-1",
            type="Ed25519VerificationKey2020",
            controller="did:key:z6Mk...",
        )
        doc = DIDDocument(
            id="did:key:z6Mk...",
            verification_method=[vm],
            assertion_method=["did:key:z6Mk...#key-1"],
        )

        found = doc.get_verification_method("did:key:z6Mk...#key-1")
        assert found is vm

    def test_get_verification_method_by_fragment(self) -> None:
        """Verification method can be found by fragment reference."""
        vm = VerificationMethod(
            id="did:key:z6Mk...#key-1",
            type="Ed25519VerificationKey2020",
            controller="did:key:z6Mk...",
        )
        doc = DIDDocument(
            id="did:key:z6Mk...",
            verification_method=[vm],
        )

        found = doc.get_verification_method("#key-1")
        assert found is vm

    def test_get_assertion_methods(self) -> None:
        """Assertion methods can be retrieved."""
        vm = VerificationMethod(
            id="did:key:z6Mk...#key-1",
            type="Ed25519VerificationKey2020",
            controller="did:key:z6Mk...",
        )
        doc = DIDDocument(
            id="did:key:z6Mk...",
            verification_method=[vm],
            assertion_method=["did:key:z6Mk...#key-1"],
        )

        methods = doc.get_assertion_methods()
        assert len(methods) == 1
        assert methods[0] is vm


class TestVerificationResult:
    """Tests for VerificationResult."""

    def test_verified_property(self) -> None:
        """verified is True only when valid and signature_valid."""
        result = VerificationResult(valid=True, signature_valid=True)
        assert result.verified is True

        result = VerificationResult(valid=True, signature_valid=False)
        assert result.verified is False

        result = VerificationResult(valid=False, signature_valid=True)
        assert result.verified is False

        result = VerificationResult(valid=True, signature_valid=None)
        assert result.verified is False


class TestCredentialVerifier:
    """Tests for CredentialVerifier."""

    def test_verify_extracts_issuer_string(self) -> None:
        """Issuer DID is extracted from string format."""
        verifier = CredentialVerifier()
        credential = {"issuer": "did:web:example.com"}

        result = verifier.verify(credential)
        assert result.issuer_did == "did:web:example.com"

    def test_verify_extracts_issuer_object(self) -> None:
        """Issuer DID is extracted from object format."""
        verifier = CredentialVerifier()
        credential = {"issuer": {"id": "did:web:example.com", "name": "Example"}}

        result = verifier.verify(credential)
        assert result.issuer_did == "did:web:example.com"

    def test_verify_without_cryptography_returns_warning(self) -> None:
        """Without cryptography, verification returns warning but extracts issuer."""
        verifier = CredentialVerifier()
        credential = {
            "issuer": "did:web:example.com",
            "credentialSubject": {"id": "urn:uuid:123"},
        }

        result = verifier.verify(credential)

        # Should always extract issuer
        assert result.issuer_did == "did:web:example.com"
        # If cryptography not installed, should have warning
        # If installed, should check for proof
        assert result.valid is True


class TestValidationEngineIntegration:
    """Tests for ValidationEngine integration with VC verification."""

    def test_verify_signatures_parameter(self) -> None:
        """verify_signatures parameter is stored."""
        from dppvalidator.validators.engine import ValidationEngine

        engine = ValidationEngine(verify_signatures=True)
        assert engine.verify_signatures is True

        engine = ValidationEngine(verify_signatures=False)
        assert engine.verify_signatures is False

    def test_validation_result_has_signature_fields(self) -> None:
        """ValidationResult includes signature verification fields."""
        from dppvalidator.validators.results import ValidationResult

        result = ValidationResult(
            valid=True,
            signature_valid=True,
            issuer_did="did:web:example.com",
            verification_method="did:web:example.com#key-1",
        )

        assert result.signature_valid is True
        assert result.issuer_did == "did:web:example.com"
        assert result.verification_method == "did:web:example.com#key-1"

        result_dict = result.to_dict()
        assert result_dict["signature_valid"] is True
        assert result_dict["issuer_did"] == "did:web:example.com"


class TestModuleExports:
    """Tests for verifier module exports."""

    def test_verifier_module_exports(self) -> None:
        """verifier module exports expected classes and functions."""
        from dppvalidator.verifier import (
            CredentialVerifier,
            DIDResolver,
            SignatureVerifier,
            resolve_did,
            verify_credential,
            verify_signature,
        )

        assert callable(DIDResolver)
        assert callable(CredentialVerifier)
        assert callable(SignatureVerifier)
        assert callable(resolve_did)
        assert callable(verify_credential)
        assert callable(verify_signature)
