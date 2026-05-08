"""Signature verification for Verifiable Credentials."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

import jwt
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, ed25519

from dppvalidator.logging import get_logger
from dppvalidator.verifier.did import VerificationMethod

logger = get_logger(__name__)


@dataclass
class SignatureInfo:
    """Information about a signature."""

    algorithm: str
    signature_bytes: bytes
    message_bytes: bytes
    key_id: str | None = None


class SignatureVerifier:
    """Verify cryptographic signatures using various algorithms."""

    SUPPORTED_ALGORITHMS = ["Ed25519", "ES256", "ES384"]

    def __init__(self) -> None:
        """Initialize the signature verifier."""
        pass

    def verify(
        self,
        signature: bytes,
        message: bytes,
        public_key: bytes | dict[str, Any],
        algorithm: str,
    ) -> bool:
        """Verify a signature.

        Args:
            signature: The signature bytes
            message: The message that was signed
            public_key: Public key as bytes or JWK dict
            algorithm: Signature algorithm (Ed25519, ES256, ES384)

        Returns:
            True if signature is valid, False otherwise

        """
        try:
            if algorithm == "Ed25519":
                return self._verify_ed25519(signature, message, public_key)
            elif algorithm in ("ES256", "P-256"):
                return self._verify_ecdsa(signature, message, public_key, "P-256")
            elif algorithm in ("ES384", "P-384"):
                return self._verify_ecdsa(signature, message, public_key, "P-384")
            else:
                logger.warning("Unsupported signature algorithm: %s", algorithm)
                return False
        except Exception as e:
            logger.warning("Signature verification failed: %s", e)
            return False

    def _verify_ed25519(
        self,
        signature: bytes,
        message: bytes,
        public_key: bytes | dict[str, Any],
    ) -> bool:
        """Verify an Ed25519 signature."""
        try:
            # Convert JWK to bytes if needed
            if isinstance(public_key, dict):
                public_key = self._jwk_to_ed25519_public_key(public_key)

            key = ed25519.Ed25519PublicKey.from_public_bytes(public_key)
            key.verify(signature, message)
            return True
        except InvalidSignature:
            return False
        except Exception as e:
            logger.warning("Ed25519 verification error: %s", e)
            return False

    def _verify_ecdsa(
        self,
        signature: bytes,
        message: bytes,
        public_key: bytes | dict[str, Any],
        curve: str,
    ) -> bool:
        """Verify an ECDSA signature (P-256 or P-384)."""
        try:
            # Convert JWK to key object if needed
            if isinstance(public_key, dict):
                key = self._jwk_to_ec_public_key(public_key)
            else:
                # Assume raw bytes
                if curve == "P-256":
                    key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), public_key)
                else:
                    key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP384R1(), public_key)

            # Determine hash algorithm
            hash_alg = hashes.SHA256() if curve == "P-256" else hashes.SHA384()

            # Verify signature
            key.verify(signature, message, ec.ECDSA(hash_alg))
            return True
        except InvalidSignature:
            return False
        except Exception as e:
            logger.warning("ECDSA verification error: %s", e)
            return False

    def _jwk_to_ed25519_public_key(self, jwk: dict[str, Any]) -> bytes:
        """Convert a JWK to Ed25519 public key bytes."""
        if jwk.get("kty") != "OKP" or jwk.get("crv") != "Ed25519":
            raise ValueError("Invalid JWK for Ed25519")

        x = jwk.get("x", "")
        # Add padding if needed
        x += "=" * (4 - len(x) % 4) if len(x) % 4 else ""
        return base64.urlsafe_b64decode(x)

    def _jwk_to_ec_public_key(self, jwk: dict[str, Any]) -> Any:
        """Convert a JWK to EC public key object."""
        if jwk.get("kty") != "EC":
            raise ValueError("Invalid JWK for EC key")

        crv = jwk.get("crv")
        x = jwk.get("x", "")
        y = jwk.get("y", "")

        # Add padding if needed
        x += "=" * (4 - len(x) % 4) if len(x) % 4 else ""
        y += "=" * (4 - len(y) % 4) if len(y) % 4 else ""

        x_bytes = base64.urlsafe_b64decode(x)
        y_bytes = base64.urlsafe_b64decode(y)

        # Create uncompressed point
        point = b"\x04" + x_bytes + y_bytes

        if crv == "P-256":
            return ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), point)
        elif crv == "P-384":
            return ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP384R1(), point)
        else:
            raise ValueError(f"Unsupported curve: {crv}")

    def verify_from_method(
        self,
        signature: bytes,
        message: bytes,
        verification_method: VerificationMethod,
    ) -> bool:
        """Verify a signature using a DID verification method.

        Args:
            signature: The signature bytes
            message: The message that was signed
            verification_method: DID verification method with public key

        Returns:
            True if signature is valid, False otherwise

        """
        if not verification_method.public_key_jwk:
            logger.warning("No JWK in verification method")
            return False

        key_type = verification_method.key_type
        if not key_type:
            logger.warning("Could not determine key type from verification method")
            return False

        return self.verify(
            signature,
            message,
            verification_method.public_key_jwk,
            key_type,
        )


def verify_jws(jws_token: str, public_key: dict[str, Any]) -> tuple[bool, dict | None]:
    """Verify a JWS (JSON Web Signature) token.

    Args:
        jws_token: The JWS token (compact serialization)
        public_key: Public key as JWK dict

    Returns:
        Tuple of (is_valid, payload_dict or None)

    """
    try:
        # Determine algorithm from JWK
        kty = public_key.get("kty")
        crv = public_key.get("crv")

        if kty == "OKP" and crv == "Ed25519":
            algorithm = "EdDSA"
        elif kty == "EC" and crv == "P-256":
            algorithm = "ES256"
        elif kty == "EC" and crv == "P-384":
            algorithm = "ES384"
        else:
            logger.warning("Unsupported key type for JWS: kty=%s, crv=%s", kty, crv)
            return False, None

        # Convert JWK to PEM for PyJWT
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

        if kty == "OKP":
            key_bytes = SignatureVerifier()._jwk_to_ed25519_public_key(public_key)
            key = ed25519.Ed25519PublicKey.from_public_bytes(key_bytes)
        else:
            key = SignatureVerifier()._jwk_to_ec_public_key(public_key)

        pem = key.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)

        # Verify and decode
        payload = jwt.decode(jws_token, pem, algorithms=[algorithm])
        return True, payload

    except jwt.InvalidSignatureError:
        return False, None
    except Exception as e:
        logger.warning("JWS verification failed: %s", e)
        return False, None


def verify_signature(
    signature: bytes,
    message: bytes,
    public_key: bytes | dict[str, Any],
    algorithm: str,
) -> bool:
    """Verify a signature using the default verifier.

    Args:
        signature: The signature bytes
        message: The message that was signed
        public_key: Public key as bytes or JWK dict
        algorithm: Signature algorithm (Ed25519, ES256, ES384)

    Returns:
        True if signature is valid, False otherwise

    """
    verifier = SignatureVerifier()
    return verifier.verify(signature, message, public_key, algorithm)
