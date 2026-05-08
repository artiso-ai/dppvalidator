"""Extended tests for signature verification - covering ECDSA and edge cases."""

import base64
from typing import Any

from cryptography.hazmat.primitives.asymmetric import ec, ed25519

from dppvalidator.verifier.did import VerificationMethod
from dppvalidator.verifier.signatures import (
    SignatureInfo,
    SignatureVerifier,
    verify_jws,
    verify_signature,
)


class TestSignatureInfo:
    """Tests for SignatureInfo dataclass."""

    def test_default_key_id_is_none(self) -> None:
        """key_id defaults to None."""
        info = SignatureInfo(
            algorithm="Ed25519",
            signature_bytes=b"sig",
            message_bytes=b"msg",
        )
        assert info.key_id is None

    def test_key_id_can_be_set(self) -> None:
        """key_id can be explicitly set."""
        info = SignatureInfo(
            algorithm="ES256",
            signature_bytes=b"sig",
            message_bytes=b"msg",
            key_id="key-1",
        )
        assert info.key_id == "key-1"


class TestSignatureVerifierECDSA:
    """Tests for ECDSA signature verification."""

    def test_verify_es256_with_jwk(self) -> None:
        """ES256 verification works with JWK public key."""
        # Generate P-256 key pair
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()

        # Create JWK
        numbers = public_key.public_numbers()
        x_bytes = numbers.x.to_bytes(32, "big")
        y_bytes = numbers.y.to_bytes(32, "big")
        jwk = {
            "kty": "EC",
            "crv": "P-256",
            "x": base64.urlsafe_b64encode(x_bytes).rstrip(b"=").decode(),
            "y": base64.urlsafe_b64encode(y_bytes).rstrip(b"=").decode(),
        }

        # Sign a message
        from cryptography.hazmat.primitives import hashes

        message = b"test message"
        signature = private_key.sign(message, ec.ECDSA(hashes.SHA256()))

        verifier = SignatureVerifier()
        result = verifier.verify(signature, message, jwk, "ES256")
        assert result is True

    def test_verify_es384_with_jwk(self) -> None:
        """ES384 verification works with JWK public key."""
        # Generate P-384 key pair
        private_key = ec.generate_private_key(ec.SECP384R1())
        public_key = private_key.public_key()

        # Create JWK
        numbers = public_key.public_numbers()
        x_bytes = numbers.x.to_bytes(48, "big")
        y_bytes = numbers.y.to_bytes(48, "big")
        jwk = {
            "kty": "EC",
            "crv": "P-384",
            "x": base64.urlsafe_b64encode(x_bytes).rstrip(b"=").decode(),
            "y": base64.urlsafe_b64encode(y_bytes).rstrip(b"=").decode(),
        }

        # Sign a message
        from cryptography.hazmat.primitives import hashes

        message = b"test message for P-384"
        signature = private_key.sign(message, ec.ECDSA(hashes.SHA384()))

        verifier = SignatureVerifier()
        result = verifier.verify(signature, message, jwk, "ES384")
        assert result is True

    def test_verify_p256_alias_works(self) -> None:
        """P-256 alias works for ES256."""
        verifier = SignatureVerifier()
        # Invalid signature should return False, not crash
        result = verifier.verify(b"invalid", b"message", b"\x04" + b"\x00" * 64, "P-256")
        assert result is False

    def test_verify_p384_alias_works(self) -> None:
        """P-384 alias works for ES384."""
        verifier = SignatureVerifier()
        # Invalid signature should return False, not crash
        result = verifier.verify(b"invalid", b"message", b"\x04" + b"\x00" * 96, "P-384")
        assert result is False

    def test_verify_invalid_ecdsa_signature_returns_false(self) -> None:
        """Invalid ECDSA signature returns False."""
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()

        numbers = public_key.public_numbers()
        x_bytes = numbers.x.to_bytes(32, "big")
        y_bytes = numbers.y.to_bytes(32, "big")
        jwk = {
            "kty": "EC",
            "crv": "P-256",
            "x": base64.urlsafe_b64encode(x_bytes).rstrip(b"=").decode(),
            "y": base64.urlsafe_b64encode(y_bytes).rstrip(b"=").decode(),
        }

        verifier = SignatureVerifier()
        result = verifier.verify(b"invalid signature", b"message", jwk, "ES256")
        assert result is False

    def test_unsupported_algorithm_returns_false(self) -> None:
        """Unsupported algorithm returns False."""
        verifier = SignatureVerifier()
        result = verifier.verify(b"sig", b"msg", b"key", "RS256")
        assert result is False


class TestSignatureVerifierEd25519:
    """Tests for Ed25519 signature verification."""

    def test_verify_ed25519_with_jwk(self) -> None:
        """Ed25519 verification works with JWK public key."""
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        jwk = {
            "kty": "OKP",
            "crv": "Ed25519",
            "x": base64.urlsafe_b64encode(public_key.public_bytes_raw()).rstrip(b"=").decode(),
        }

        message = b"test message"
        signature = private_key.sign(message)

        verifier = SignatureVerifier()
        result = verifier.verify(signature, message, jwk, "Ed25519")
        assert result is True

    def test_verify_ed25519_with_raw_bytes(self) -> None:
        """Ed25519 verification works with raw public key bytes."""
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        message = b"test message"
        signature = private_key.sign(message)

        verifier = SignatureVerifier()
        result = verifier.verify(signature, message, public_key.public_bytes_raw(), "Ed25519")
        assert result is True

    def test_verify_ed25519_invalid_signature_returns_false(self) -> None:
        """Invalid Ed25519 signature returns False."""
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        verifier = SignatureVerifier()
        result = verifier.verify(
            b"invalid" * 8, b"message", public_key.public_bytes_raw(), "Ed25519"
        )
        assert result is False


class TestJWKConversion:
    """Tests for JWK to key conversion."""

    def test_invalid_ed25519_jwk_raises(self) -> None:
        """Invalid Ed25519 JWK raises ValueError."""
        verifier = SignatureVerifier()
        jwk: dict[str, Any] = {"kty": "RSA", "n": "abc", "e": "AQAB"}

        try:
            verifier._jwk_to_ed25519_public_key(jwk)
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "Invalid JWK for Ed25519" in str(e)

    def test_invalid_ec_jwk_raises(self) -> None:
        """Invalid EC JWK raises ValueError."""
        verifier = SignatureVerifier()
        jwk: dict[str, Any] = {"kty": "OKP", "crv": "Ed25519", "x": "abc"}

        try:
            verifier._jwk_to_ec_public_key(jwk)
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "Invalid JWK for EC key" in str(e)

    def test_unsupported_ec_curve_raises(self) -> None:
        """Unsupported EC curve raises ValueError."""
        verifier = SignatureVerifier()
        jwk = {
            "kty": "EC",
            "crv": "P-521",  # Not supported
            "x": base64.urlsafe_b64encode(b"\x00" * 66).decode(),
            "y": base64.urlsafe_b64encode(b"\x00" * 66).decode(),
        }

        try:
            verifier._jwk_to_ec_public_key(jwk)
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "Unsupported curve" in str(e)


class TestVerifyFromMethod:
    """Tests for verify_from_method."""

    def test_no_jwk_returns_false(self) -> None:
        """Missing JWK in verification method returns False."""
        vm = VerificationMethod(
            id="did:key:z6Mk...#key-1",
            type="Ed25519VerificationKey2020",
            controller="did:key:z6Mk...",
            public_key_jwk=None,
        )

        verifier = SignatureVerifier()
        result = verifier.verify_from_method(b"sig", b"msg", vm)
        assert result is False

    def test_no_key_type_returns_false(self) -> None:
        """Unknown key type returns False."""
        vm = VerificationMethod(
            id="did:key:z6Mk...#key-1",
            type="UnknownKeyType",
            controller="did:key:z6Mk...",
            public_key_jwk={"kty": "unknown"},
        )

        verifier = SignatureVerifier()
        result = verifier.verify_from_method(b"sig", b"msg", vm)
        assert result is False


class TestVerifyJWS:
    """Tests for JWS verification."""

    def test_unsupported_key_type_returns_false(self) -> None:
        """Unsupported key type returns (False, None)."""
        jwk = {"kty": "RSA", "n": "abc", "e": "AQAB"}
        valid, payload = verify_jws("eyJ...", jwk)
        assert valid is False
        assert payload is None

    def test_invalid_jws_returns_false(self) -> None:
        """Invalid JWS token returns (False, None)."""
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        jwk = {
            "kty": "OKP",
            "crv": "Ed25519",
            "x": base64.urlsafe_b64encode(public_key.public_bytes_raw()).rstrip(b"=").decode(),
        }

        valid, payload = verify_jws("not.a.valid.jws", jwk)
        assert valid is False
        assert payload is None


class TestModuleFunctions:
    """Tests for module-level convenience functions."""

    def test_verify_signature_uses_default_verifier(self) -> None:
        """verify_signature creates SignatureVerifier internally."""
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        message = b"test"
        signature = private_key.sign(message)

        result = verify_signature(signature, message, public_key.public_bytes_raw(), "Ed25519")
        assert result is True
