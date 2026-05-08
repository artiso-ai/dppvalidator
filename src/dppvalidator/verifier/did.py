"""DID (Decentralized Identifier) resolution for did:web and did:key methods."""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from typing import Any

import base58
import httpx

from dppvalidator.logging import get_logger

logger = get_logger(__name__)

# Multicodec prefixes for did:key
MULTICODEC_ED25519_PUB = b"\xed\x01"  # 0xed01
MULTICODEC_P256_PUB = b"\x80\x24"  # 0x8024 (secp256r1/P-256)
MULTICODEC_P384_PUB = b"\x81\x24"  # 0x8124 (secp384r1/P-384)


@dataclass
class VerificationMethod:
    """A verification method from a DID document."""

    id: str
    type: str
    controller: str
    public_key_jwk: dict[str, Any] | None = None
    public_key_multibase: str | None = None
    public_key_base58: str | None = None

    @property
    def key_type(self) -> str | None:
        """Determine the key type (Ed25519, P-256, etc.)."""
        if self.public_key_jwk:
            crv = self.public_key_jwk.get("crv")
            kty = self.public_key_jwk.get("kty")
            if kty == "OKP" and crv == "Ed25519":
                return "Ed25519"
            if kty == "EC" and crv == "P-256":
                return "P-256"
            if kty == "EC" and crv == "P-384":
                return "P-384"
        if self.type == "Ed25519VerificationKey2020":
            return "Ed25519"
        if self.type == "JsonWebKey2020" and self.public_key_jwk:
            return self.key_type  # Recurse with JWK
        return None


@dataclass
class DIDDocument:
    """Parsed DID Document."""

    id: str
    context: list[str] = field(default_factory=list)
    verification_method: list[VerificationMethod] = field(default_factory=list)
    authentication: list[str] = field(default_factory=list)
    assertion_method: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def get_verification_method(self, method_id: str) -> VerificationMethod | None:
        """Get a verification method by ID."""
        # Handle fragment references
        if method_id.startswith("#"):
            method_id = f"{self.id}{method_id}"

        for vm in self.verification_method:
            if vm.id == method_id:
                return vm
            # Also check fragment-only match
            if vm.id.endswith(method_id) or method_id.endswith(vm.id.split("#")[-1]):
                return vm
        return None

    def get_assertion_methods(self) -> list[VerificationMethod]:
        """Get all verification methods valid for assertions."""
        methods = []
        for ref in self.assertion_method:
            vm = self.get_verification_method(ref)
            if vm:
                methods.append(vm)
        return methods


class DIDResolver:
    """Resolver for DID documents supporting did:web and did:key methods."""

    def __init__(self, cache_size: int = 100, timeout: float = 10.0) -> None:
        """Initialize the DID resolver.

        Args:
            cache_size: Maximum number of DID documents to cache
            timeout: HTTP request timeout in seconds

        """
        self.cache_size = cache_size
        self.timeout = timeout
        self._cache: dict[str, DIDDocument] = {}

    def resolve(self, did: str) -> DIDDocument | None:
        """Resolve a DID to its DID document.

        Args:
            did: The DID to resolve (e.g., "did:web:example.com" or "did:key:z...")

        Returns:
            DIDDocument or None if resolution fails

        """
        if did in self._cache:
            return self._cache[did]

        if did.startswith("did:web:"):
            doc = self._resolve_did_web(did)
        elif did.startswith("did:key:"):
            doc = self._resolve_did_key(did)
        else:
            logger.warning(
                "Unsupported DID method: %s", did.split(":")[1] if ":" in did else "unknown"
            )
            return None

        if doc and len(self._cache) < self.cache_size:
            self._cache[did] = doc

        return doc

    def _resolve_did_web(self, did: str) -> DIDDocument | None:
        """Resolve a did:web identifier.

        did:web:example.com -> https://example.com/.well-known/did.json
        did:web:example.com:path:to:doc -> https://example.com/path/to/doc/did.json
        """
        try:
            # Parse did:web format
            parts = did[8:].split(":")  # Remove "did:web:" prefix
            domain = parts[0].replace("%3A", ":")  # Handle port encoding

            if len(parts) > 1:
                path = "/".join(parts[1:])
                url = f"https://{domain}/{path}/did.json"
            else:
                url = f"https://{domain}/.well-known/did.json"

            # Fetch the DID document
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()

            return self._parse_did_document(data)

        except Exception as e:
            logger.warning("Failed to resolve did:web %s: %s", did, e)
            return None

    def _resolve_did_key(self, did: str) -> DIDDocument | None:
        """Resolve a did:key identifier.

        did:key is self-describing - the public key is encoded in the identifier.
        """
        try:
            # Extract the multibase-encoded key
            key_id = did[8:]  # Remove "did:key:" prefix

            if not key_id.startswith("z"):
                logger.warning("Unsupported multibase encoding for did:key: %s", key_id[0])
                return None

            # Decode base58btc (multibase 'z' prefix)
            key_bytes = self._decode_base58btc(key_id[1:])
            if not key_bytes:
                return None

            # Determine key type from multicodec prefix
            vm = self._parse_multicodec_key(did, key_bytes)
            if not vm:
                return None

            # Build self-describing DID document
            doc = DIDDocument(
                id=did,
                context=["https://www.w3.org/ns/did/v1"],
                verification_method=[vm],
                authentication=[vm.id],
                assertion_method=[vm.id],
                raw={
                    "@context": ["https://www.w3.org/ns/did/v1"],
                    "id": did,
                    "verificationMethod": [
                        {
                            "id": vm.id,
                            "type": vm.type,
                            "controller": vm.controller,
                            "publicKeyJwk": vm.public_key_jwk,
                        }
                    ],
                    "authentication": [vm.id],
                    "assertionMethod": [vm.id],
                },
            )

            return doc

        except Exception as e:
            logger.warning("Failed to resolve did:key %s: %s", did, e)
            return None

    def _parse_multicodec_key(self, did: str, key_bytes: bytes) -> VerificationMethod | None:
        """Parse a multicodec-prefixed public key."""
        if key_bytes[:2] == MULTICODEC_ED25519_PUB:
            # Ed25519 public key (32 bytes after prefix)
            pub_key = key_bytes[2:]
            if len(pub_key) != 32:
                return None

            return VerificationMethod(
                id=f"{did}#{did[8:]}",
                type="Ed25519VerificationKey2020",
                controller=did,
                public_key_jwk={
                    "kty": "OKP",
                    "crv": "Ed25519",
                    "x": base64.urlsafe_b64encode(pub_key).rstrip(b"=").decode(),
                },
            )

        if key_bytes[:2] == MULTICODEC_P256_PUB:
            # P-256 public key (compressed or uncompressed)
            pub_key = key_bytes[2:]
            # For compressed keys, we'd need to decompress
            # For now, store as-is in multibase format
            return VerificationMethod(
                id=f"{did}#{did[8:]}",
                type="JsonWebKey2020",
                controller=did,
                public_key_jwk={
                    "kty": "EC",
                    "crv": "P-256",
                    # Note: Would need proper decompression for x, y coordinates
                },
                public_key_multibase=f"z{self._encode_base58btc(key_bytes)}",
            )

        logger.warning("Unsupported multicodec prefix: %s", key_bytes[:2].hex())
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
        except (ValueError, Exception):
            return None

    def _encode_base58btc(self, data: bytes) -> str:
        """Encode bytes as base58btc using the base58 library.

        Args:
            data: Bytes to encode

        Returns:
            Base58-encoded string
        """
        return base58.b58encode(data).decode("ascii")

    def _parse_did_document(self, data: dict[str, Any]) -> DIDDocument:
        """Parse a DID document from JSON."""
        verification_methods = []

        for vm_data in data.get("verificationMethod", []):
            vm = VerificationMethod(
                id=vm_data.get("id", ""),
                type=vm_data.get("type", ""),
                controller=vm_data.get("controller", ""),
                public_key_jwk=vm_data.get("publicKeyJwk"),
                public_key_multibase=vm_data.get("publicKeyMultibase"),
                public_key_base58=vm_data.get("publicKeyBase58"),
            )
            verification_methods.append(vm)

        # Handle @context as string or list
        context = data.get("@context", [])
        if isinstance(context, str):
            context = [context]

        return DIDDocument(
            id=data.get("id", ""),
            context=context,
            verification_method=verification_methods,
            authentication=data.get("authentication", []),
            assertion_method=data.get("assertionMethod", []),
            raw=data,
        )

    def clear_cache(self) -> None:
        """Clear the DID document cache."""
        self._cache.clear()

    async def resolve_async(self, did: str) -> DIDDocument | None:
        """Resolve a DID asynchronously.

        Async variant of resolve() that uses httpx.AsyncClient for network
        operations. Useful when called from async contexts to avoid blocking.

        Args:
            did: The DID to resolve (e.g., "did:web:example.com" or "did:key:z...")

        Returns:
            DIDDocument or None if resolution fails
        """
        if did in self._cache:
            return self._cache[did]

        if did.startswith("did:web:"):
            doc = await self._resolve_did_web_async(did)
        elif did.startswith("did:key:"):
            # did:key is self-describing, no network needed
            doc = self._resolve_did_key(did)
        else:
            logger.warning(
                "Unsupported DID method: %s", did.split(":")[1] if ":" in did else "unknown"
            )
            return None

        if doc and len(self._cache) < self.cache_size:
            self._cache[did] = doc

        return doc

    async def _resolve_did_web_async(self, did: str) -> DIDDocument | None:
        """Resolve a did:web identifier asynchronously.

        did:web:example.com -> https://example.com/.well-known/did.json
        did:web:example.com:path:to:doc -> https://example.com/path/to/doc/did.json
        """
        try:
            parts = did[8:].split(":")
            domain = parts[0].replace("%3A", ":")

            if len(parts) > 1:
                path = "/".join(parts[1:])
                url = f"https://{domain}/{path}/did.json"
            else:
                url = f"https://{domain}/.well-known/did.json"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

            return self._parse_did_document(data)

        except Exception as e:
            logger.warning("Failed to resolve did:web async %s: %s", did, e)
            return None


# Module-level resolver instance
_default_resolver: DIDResolver | None = None


def get_resolver() -> DIDResolver:
    """Get the default DID resolver instance."""
    global _default_resolver
    if _default_resolver is None:
        _default_resolver = DIDResolver()
    return _default_resolver


def resolve_did(did: str) -> DIDDocument | None:
    """Resolve a DID using the default resolver.

    Args:
        did: The DID to resolve

    Returns:
        DIDDocument or None if resolution fails

    """
    return get_resolver().resolve(did)
