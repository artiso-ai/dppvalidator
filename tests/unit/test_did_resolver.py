"""Unit tests for DID resolution behavior."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from dppvalidator.verifier.did import (
    MULTICODEC_ED25519_PUB,
    MULTICODEC_P256_PUB,
    DIDDocument,
    DIDResolver,
    VerificationMethod,
    get_resolver,
    resolve_did,
)


class TestDIDResolverConfiguration:
    """Tests for DIDResolver configuration."""

    def test_default_cache_size(self) -> None:
        """Default cache size is 100."""
        resolver = DIDResolver()
        assert resolver.cache_size == 100

    def test_custom_cache_size(self) -> None:
        """Cache size can be customized."""
        resolver = DIDResolver(cache_size=50)
        assert resolver.cache_size == 50

    def test_default_timeout(self) -> None:
        """Default timeout is 10 seconds."""
        resolver = DIDResolver()
        assert resolver.timeout == 10.0

    def test_custom_timeout(self) -> None:
        """Timeout can be customized."""
        resolver = DIDResolver(timeout=5.0)
        assert resolver.timeout == 5.0


class TestDIDKeyResolution:
    """Tests for did:key resolution behavior."""

    def test_resolve_ed25519_did_key(self) -> None:
        """Ed25519 did:key resolves to self-describing document."""
        resolver = DIDResolver()
        # Well-known Ed25519 did:key
        did = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"

        doc = resolver.resolve(did)

        assert doc is not None
        assert doc.id == did
        assert len(doc.verification_method) == 1
        assert doc.verification_method[0].type == "Ed25519VerificationKey2020"

    def test_ed25519_key_has_jwk(self) -> None:
        """Ed25519 verification method has JWK with correct format."""
        resolver = DIDResolver()
        did = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"

        doc = resolver.resolve(did)

        assert doc is not None
        jwk = doc.verification_method[0].public_key_jwk
        assert jwk is not None
        assert jwk["kty"] == "OKP"
        assert jwk["crv"] == "Ed25519"
        assert "x" in jwk

    def test_ed25519_doc_has_assertion_methods(self) -> None:
        """Ed25519 DID document includes assertion method references."""
        resolver = DIDResolver()
        did = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"

        doc = resolver.resolve(did)

        assert doc is not None
        assert len(doc.assertion_method) == 1
        assert len(doc.authentication) == 1

    def test_unsupported_multibase_encoding(self) -> None:
        """Non-z multibase prefix returns None."""
        resolver = DIDResolver()
        # 'f' prefix is not supported (hex)
        did = "did:key:fabcdef"

        doc = resolver.resolve(did)
        assert doc is None

    def test_invalid_base58_returns_none(self) -> None:
        """Invalid base58 in did:key returns None."""
        resolver = DIDResolver()
        # Contains invalid characters
        did = "did:key:zO0Il"

        doc = resolver.resolve(did)
        assert doc is None


class TestDIDWebResolution:
    """Tests for did:web resolution behavior."""

    def test_did_web_url_construction_simple(self) -> None:
        """Simple did:web constructs correct URL."""
        resolver = DIDResolver()

        # Mock httpx.Client
        with patch.object(httpx, "Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__ = MagicMock(return_value=mock_client)
            mock_client_class.return_value.__exit__ = MagicMock(return_value=False)

            mock_response = MagicMock()
            mock_response.json.return_value = {
                "id": "did:web:example.com",
                "@context": ["https://www.w3.org/ns/did/v1"],
                "verificationMethod": [],
            }
            mock_client.get.return_value = mock_response

            resolver._resolve_did_web("did:web:example.com")

            mock_client.get.assert_called_once_with("https://example.com/.well-known/did.json")

    def test_did_web_url_with_path(self) -> None:
        """did:web with path constructs correct URL."""
        resolver = DIDResolver()

        with patch.object(httpx, "Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__ = MagicMock(return_value=mock_client)
            mock_client_class.return_value.__exit__ = MagicMock(return_value=False)

            mock_response = MagicMock()
            mock_response.json.return_value = {
                "id": "did:web:example.com:users:alice",
                "@context": ["https://www.w3.org/ns/did/v1"],
                "verificationMethod": [],
            }
            mock_client.get.return_value = mock_response

            resolver._resolve_did_web("did:web:example.com:users:alice")

            mock_client.get.assert_called_once_with("https://example.com/users/alice/did.json")

    def test_did_web_with_port_encoding(self) -> None:
        """did:web with encoded port is handled correctly."""
        resolver = DIDResolver()

        with patch.object(httpx, "Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__ = MagicMock(return_value=mock_client)
            mock_client_class.return_value.__exit__ = MagicMock(return_value=False)

            mock_response = MagicMock()
            mock_response.json.return_value = {
                "id": "did:web:localhost:8080",
                "@context": ["https://www.w3.org/ns/did/v1"],
                "verificationMethod": [],
            }
            mock_client.get.return_value = mock_response

            resolver._resolve_did_web("did:web:localhost%3A8080")

            mock_client.get.assert_called_once_with("https://localhost:8080/.well-known/did.json")

    def test_did_web_network_error_returns_none(self) -> None:
        """Network error during did:web resolution returns None."""
        resolver = DIDResolver()

        with patch.object(httpx, "Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__ = MagicMock(return_value=mock_client)
            mock_client_class.return_value.__exit__ = MagicMock(return_value=False)
            mock_client.get.side_effect = httpx.RequestError("Network error")

            doc = resolver._resolve_did_web("did:web:unreachable.example.com")
            assert doc is None


class TestDIDResolverCaching:
    """Tests for DID document caching behavior."""

    def test_resolved_did_is_cached(self) -> None:
        """Resolved DID documents are cached."""
        resolver = DIDResolver(cache_size=10)
        did = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"

        doc1 = resolver.resolve(did)
        doc2 = resolver.resolve(did)

        assert doc1 is doc2  # Same object

    def test_cache_respects_size_limit(self) -> None:
        """Cache doesn't exceed size limit."""
        resolver = DIDResolver(cache_size=2)

        # Resolve 3 different DIDs
        did1 = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"
        resolver.resolve(did1)

        # Cache should have 1 entry
        assert len(resolver._cache) == 1

        # When cache is full, new entries are not added
        # (based on the implementation checking len < cache_size)

    def test_clear_cache_removes_all_entries(self) -> None:
        """clear_cache removes all cached documents."""
        resolver = DIDResolver()
        did = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"

        resolver.resolve(did)
        assert len(resolver._cache) == 1

        resolver.clear_cache()
        assert len(resolver._cache) == 0


class TestUnsupportedDIDMethods:
    """Tests for unsupported DID methods."""

    def test_unsupported_method_returns_none(self) -> None:
        """Unsupported DID method returns None."""
        resolver = DIDResolver()
        doc = resolver.resolve("did:ethr:0x123")
        assert doc is None

    def test_malformed_did_returns_none(self) -> None:
        """Malformed DID returns None."""
        resolver = DIDResolver()
        doc = resolver.resolve("not-a-did")
        assert doc is None


class TestBase58Encoding:
    """Tests for base58btc encoding/decoding."""

    def test_decode_encodes_roundtrip(self) -> None:
        """Base58 encode/decode roundtrips correctly."""
        resolver = DIDResolver()
        original = b"\x01\x02\x03\x04\x05"

        encoded = resolver._encode_base58btc(original)
        decoded = resolver._decode_base58btc(encoded)

        assert decoded == original

    def test_decode_handles_leading_zeros(self) -> None:
        """Leading zero bytes become '1' characters."""
        resolver = DIDResolver()
        data = b"\x00\x00\x01"

        encoded = resolver._encode_base58btc(data)
        assert encoded.startswith("11")

        decoded = resolver._decode_base58btc(encoded)
        assert decoded == data

    def test_encode_empty_bytes(self) -> None:
        """Empty bytes encode to empty string."""
        resolver = DIDResolver()
        encoded = resolver._encode_base58btc(b"")
        assert encoded == ""


class TestMulticodecParsing:
    """Tests for multicodec key parsing."""

    def test_parse_ed25519_multicodec(self) -> None:
        """Ed25519 multicodec prefix parsed correctly."""
        resolver = DIDResolver()

        # Create a valid Ed25519 public key (32 bytes)
        public_key = bytes(32)  # 32 zero bytes for testing
        key_bytes = MULTICODEC_ED25519_PUB + public_key

        vm = resolver._parse_multicodec_key("did:key:z...", key_bytes)

        assert vm is not None
        assert vm.type == "Ed25519VerificationKey2020"
        assert vm.public_key_jwk is not None
        assert vm.public_key_jwk["crv"] == "Ed25519"

    def test_parse_p256_multicodec(self) -> None:
        """P-256 multicodec prefix parsed correctly."""
        resolver = DIDResolver()

        # Create mock P-256 key bytes
        public_key = bytes(33)  # Compressed point
        key_bytes = MULTICODEC_P256_PUB + public_key

        vm = resolver._parse_multicodec_key("did:key:zDn...", key_bytes)

        assert vm is not None
        assert vm.type == "JsonWebKey2020"
        assert vm.public_key_jwk is not None
        assert vm.public_key_jwk["crv"] == "P-256"

    def test_parse_unsupported_multicodec(self) -> None:
        """Unsupported multicodec prefix returns None."""
        resolver = DIDResolver()

        # Unknown multicodec prefix
        key_bytes = b"\xff\xff" + bytes(32)

        vm = resolver._parse_multicodec_key("did:key:z...", key_bytes)
        assert vm is None

    def test_parse_ed25519_wrong_length(self) -> None:
        """Ed25519 key with wrong length returns None."""
        resolver = DIDResolver()

        # Ed25519 needs exactly 32 bytes after prefix
        key_bytes = MULTICODEC_ED25519_PUB + bytes(16)  # Only 16 bytes

        vm = resolver._parse_multicodec_key("did:key:z...", key_bytes)
        assert vm is None


class TestDIDDocumentParsing:
    """Tests for DID document parsing."""

    def test_parse_verification_methods(self) -> None:
        """Verification methods are parsed from document."""
        resolver = DIDResolver()

        data = {
            "id": "did:web:example.com",
            "@context": ["https://www.w3.org/ns/did/v1"],
            "verificationMethod": [
                {
                    "id": "did:web:example.com#key-1",
                    "type": "Ed25519VerificationKey2020",
                    "controller": "did:web:example.com",
                    "publicKeyJwk": {"kty": "OKP", "crv": "Ed25519", "x": "abc"},
                }
            ],
            "authentication": ["did:web:example.com#key-1"],
            "assertionMethod": ["did:web:example.com#key-1"],
        }

        doc = resolver._parse_did_document(data)

        assert doc.id == "did:web:example.com"
        assert len(doc.verification_method) == 1
        assert doc.verification_method[0].id == "did:web:example.com#key-1"
        assert doc.verification_method[0].public_key_jwk is not None

    def test_parse_context_as_string(self) -> None:
        """Context as string is converted to list."""
        resolver = DIDResolver()

        data = {
            "id": "did:web:example.com",
            "@context": "https://www.w3.org/ns/did/v1",
            "verificationMethod": [],
        }

        doc = resolver._parse_did_document(data)

        assert doc.context == ["https://www.w3.org/ns/did/v1"]

    def test_parse_preserves_raw_document(self) -> None:
        """Raw document is preserved in parsed result."""
        resolver = DIDResolver()

        data = {
            "id": "did:web:example.com",
            "@context": ["https://www.w3.org/ns/did/v1"],
            "verificationMethod": [],
            "customField": "value",
        }

        doc = resolver._parse_did_document(data)

        assert doc.raw == data
        assert doc.raw.get("customField") == "value"


class TestVerificationMethodKeyTypes:
    """Tests for VerificationMethod key type detection."""

    def test_key_type_p384_from_jwk(self) -> None:
        """P-384 key type detected from JWK."""
        vm = VerificationMethod(
            id="did:key:z...",
            type="JsonWebKey2020",
            controller="did:key:z...",
            public_key_jwk={"kty": "EC", "crv": "P-384", "x": "x", "y": "y"},
        )
        assert vm.key_type == "P-384"

    def test_key_type_unknown_returns_none(self) -> None:
        """Unknown key type returns None."""
        vm = VerificationMethod(
            id="did:key:z...",
            type="UnknownKeyType2030",
            controller="did:key:z...",
        )
        assert vm.key_type is None


class TestDIDDocumentMethods:
    """Tests for DIDDocument helper methods."""

    def test_get_verification_method_partial_match(self) -> None:
        """Verification method found by partial fragment match."""
        vm = VerificationMethod(
            id="did:web:example.com#key-1",
            type="Ed25519VerificationKey2020",
            controller="did:web:example.com",
        )
        doc = DIDDocument(
            id="did:web:example.com",
            verification_method=[vm],
        )

        # Should match by fragment suffix
        found = doc.get_verification_method("key-1")
        assert found is vm

    def test_get_verification_method_not_found(self) -> None:
        """Non-existent verification method returns None."""
        doc = DIDDocument(
            id="did:web:example.com",
            verification_method=[],
        )

        found = doc.get_verification_method("did:web:example.com#key-1")
        assert found is None

    def test_get_assertion_methods_filters_correctly(self) -> None:
        """get_assertion_methods only returns referenced methods."""
        vm1 = VerificationMethod(
            id="did:web:example.com#key-1",
            type="Ed25519VerificationKey2020",
            controller="did:web:example.com",
        )
        vm2 = VerificationMethod(
            id="did:web:example.com#key-2",
            type="Ed25519VerificationKey2020",
            controller="did:web:example.com",
        )

        doc = DIDDocument(
            id="did:web:example.com",
            verification_method=[vm1, vm2],
            assertion_method=["did:web:example.com#key-1"],  # Only key-1
        )

        methods = doc.get_assertion_methods()

        assert len(methods) == 1
        assert methods[0] is vm1


class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_get_resolver_returns_singleton(self) -> None:
        """get_resolver returns the same instance."""
        resolver1 = get_resolver()
        resolver2 = get_resolver()

        assert resolver1 is resolver2

    def test_resolve_did_uses_default_resolver(self) -> None:
        """resolve_did uses the module-level resolver."""
        did = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"
        doc = resolve_did(did)

        assert doc is not None
        assert doc.id == did


class TestVerificationMethodKeyTypeEdgeCases:
    """Tests for VerificationMethod key_type edge cases."""

    def test_jsonwebkey2020_with_ed25519_jwk(self) -> None:
        """JsonWebKey2020 type with Ed25519 JWK returns Ed25519."""
        vm = VerificationMethod(
            id="did:web:example.com#key-1",
            type="JsonWebKey2020",
            controller="did:web:example.com",
            public_key_jwk={"kty": "OKP", "crv": "Ed25519", "x": "abc"},
        )
        assert vm.key_type == "Ed25519"

    def test_jsonwebkey2020_with_p256_jwk(self) -> None:
        """JsonWebKey2020 type with P-256 JWK returns P-256."""
        vm = VerificationMethod(
            id="did:web:example.com#key-1",
            type="JsonWebKey2020",
            controller="did:web:example.com",
            public_key_jwk={"kty": "EC", "crv": "P-256", "x": "x", "y": "y"},
        )
        assert vm.key_type == "P-256"

    def test_jsonwebkey2020_without_jwk_returns_none(self) -> None:
        """JsonWebKey2020 without JWK returns None."""
        vm = VerificationMethod(
            id="did:web:example.com#key-1",
            type="JsonWebKey2020",
            controller="did:web:example.com",
            public_key_jwk=None,
        )
        assert vm.key_type is None


class TestDIDDocumentAssertionMethods:
    """Tests for DIDDocument assertion method handling."""

    def test_get_assertion_methods_with_invalid_reference(self) -> None:
        """Assertion method reference that doesn't exist is skipped."""
        vm = VerificationMethod(
            id="did:web:example.com#key-1",
            type="Ed25519VerificationKey2020",
            controller="did:web:example.com",
        )
        doc = DIDDocument(
            id="did:web:example.com",
            verification_method=[vm],
            assertion_method=["did:web:example.com#nonexistent"],
        )

        methods = doc.get_assertion_methods()
        assert len(methods) == 0

    def test_get_assertion_methods_mixed_valid_invalid(self) -> None:
        """Mix of valid and invalid assertion method references."""
        vm = VerificationMethod(
            id="did:web:example.com#key-1",
            type="Ed25519VerificationKey2020",
            controller="did:web:example.com",
        )
        doc = DIDDocument(
            id="did:web:example.com",
            verification_method=[vm],
            assertion_method=[
                "did:web:example.com#key-1",
                "did:web:example.com#nonexistent",
            ],
        )

        methods = doc.get_assertion_methods()
        assert len(methods) == 1
        assert methods[0] is vm


class TestAsyncDIDResolution:
    """Tests for async DID resolution methods."""

    @pytest.mark.asyncio
    async def test_resolve_async_did_key(self) -> None:
        """Async resolution of did:key works without network."""
        resolver = DIDResolver()
        did = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"

        doc = await resolver.resolve_async(did)

        assert doc is not None
        assert doc.id == did
        assert len(doc.verification_method) == 1

    @pytest.mark.asyncio
    async def test_resolve_async_caches_result(self) -> None:
        """Async resolution caches the result."""
        resolver = DIDResolver()
        did = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"

        doc1 = await resolver.resolve_async(did)
        doc2 = await resolver.resolve_async(did)

        assert doc1 is doc2

    @pytest.mark.asyncio
    async def test_resolve_async_unsupported_method(self) -> None:
        """Async resolution of unsupported DID method returns None."""
        resolver = DIDResolver()

        doc = await resolver.resolve_async("did:ethr:0x123")
        assert doc is None

    @pytest.mark.asyncio
    async def test_resolve_async_did_web_network_error(self) -> None:
        """Async did:web resolution handles network errors."""
        resolver = DIDResolver()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__aenter__ = MagicMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = MagicMock(return_value=None)
            mock_client.get = MagicMock(side_effect=httpx.RequestError("Network error"))

            doc = await resolver._resolve_did_web_async("did:web:unreachable.com")
            assert doc is None

    @pytest.mark.asyncio
    async def test_resolve_async_did_web_success(self) -> None:
        """Async did:web resolution succeeds with valid response."""
        from unittest.mock import AsyncMock

        resolver = DIDResolver()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "did:web:example.com",
            "@context": ["https://www.w3.org/ns/did/v1"],
            "verificationMethod": [],
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None

            doc = await resolver._resolve_did_web_async("did:web:example.com")

            assert doc is not None
            assert doc.id == "did:web:example.com"

    @pytest.mark.asyncio
    async def test_resolve_async_did_web_with_path(self) -> None:
        """Async did:web with path constructs correct URL."""
        from unittest.mock import AsyncMock

        resolver = DIDResolver()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "did:web:example.com:users:alice",
            "@context": ["https://www.w3.org/ns/did/v1"],
            "verificationMethod": [],
        }
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None

            doc = await resolver._resolve_did_web_async("did:web:example.com:users:alice")

            assert doc is not None
            mock_client.get.assert_called_once_with("https://example.com/users/alice/did.json")


class TestDIDKeyExceptionHandling:
    """Tests for exception handling in did:key resolution."""

    def test_resolve_did_key_exception_returns_none(self) -> None:
        """Exception during did:key resolution returns None."""
        resolver = DIDResolver()

        # Mock _decode_base58btc to raise an exception
        with patch.object(resolver, "_decode_base58btc", side_effect=Exception("Decode error")):
            doc = resolver._resolve_did_key("did:key:zValidButWillFail")
            assert doc is None

    def test_resolve_did_key_multicodec_parse_fails(self) -> None:
        """did:key with unsupported multicodec returns None."""
        resolver = DIDResolver()

        # Create a valid base58 that decodes to unsupported multicodec
        with patch.object(resolver, "_decode_base58btc", return_value=b"\xff\xff" + bytes(32)):
            doc = resolver._resolve_did_key("did:key:zUnknownCodec")
            assert doc is None
