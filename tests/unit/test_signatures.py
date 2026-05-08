"""Unit tests for signature verification behavior."""

import base64

import pytest
from cryptography.hazmat.primitives.asymmetric import ec, ed25519

from dppvalidator.verifier.did import VerificationMethod
from dppvalidator.verifier.signatures import (
    SignatureInfo,
    SignatureVerifier,
    verify_jws,
    verify_signature,
)


class TestSignatureVerifier:
    """Tests for SignatureVerifier class."""

    def test_supported_algorithms(self) -> None:
        """Verifier lists supported algorithms."""
        verifier = SignatureVerifier()
        assert "Ed25519" in verifier.SUPPORTED_ALGORITHMS
        assert "ES256" in verifier.SUPPORTED_ALGORITHMS
        assert "ES384" in verifier.SUPPORTED_ALGORITHMS

    def test_verify_ed25519_valid_signature(self) -> None:
        """Valid Ed25519 signature verifies successfully."""
        verifier = SignatureVerifier()

        # Generate a real key pair
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Sign a message
        message = b"test message"
        signature = private_key.sign(message)

        # Verify with raw bytes
        public_bytes = public_key.public_bytes_raw()
        result = verifier.verify(signature, message, public_bytes, "Ed25519")

        assert result is True

    def test_verify_ed25519_invalid_signature(self) -> None:
        """Invalid Ed25519 signature fails verification."""
        verifier = SignatureVerifier()

        # Generate a key pair
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Sign a message
        message = b"test message"
        signature = private_key.sign(message)

        # Verify with wrong message
        public_bytes = public_key.public_bytes_raw()
        result = verifier.verify(signature, b"wrong message", public_bytes, "Ed25519")

        assert result is False

    def test_verify_ed25519_with_jwk(self) -> None:
        """Ed25519 signature verifies with JWK public key."""
        verifier = SignatureVerifier()

        # Generate a real key pair
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Sign a message
        message = b"test message for jwk"
        signature = private_key.sign(message)

        # Create JWK from public key
        public_bytes = public_key.public_bytes_raw()
        jwk = {
            "kty": "OKP",
            "crv": "Ed25519",
            "x": base64.urlsafe_b64encode(public_bytes).rstrip(b"=").decode(),
        }

        result = verifier.verify(signature, message, jwk, "Ed25519")
        assert result is True

    def test_verify_es256_valid_signature(self) -> None:
        """Valid ES256 (P-256) signature verifies successfully."""
        verifier = SignatureVerifier()

        # Generate a P-256 key pair
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()

        # Sign a message (DER format)
        from cryptography.hazmat.primitives import hashes

        message = b"test message for P-256"
        der_signature = private_key.sign(message, ec.ECDSA(hashes.SHA256()))

        # Get public key numbers for JWK
        numbers = public_key.public_numbers()
        x_bytes = numbers.x.to_bytes(32, "big")
        y_bytes = numbers.y.to_bytes(32, "big")

        jwk = {
            "kty": "EC",
            "crv": "P-256",
            "x": base64.urlsafe_b64encode(x_bytes).rstrip(b"=").decode(),
            "y": base64.urlsafe_b64encode(y_bytes).rstrip(b"=").decode(),
        }

        result = verifier.verify(der_signature, message, jwk, "ES256")
        assert result is True

    def test_verify_es384_valid_signature(self) -> None:
        """Valid ES384 (P-384) signature verifies successfully."""
        verifier = SignatureVerifier()

        # Generate a P-384 key pair
        private_key = ec.generate_private_key(ec.SECP384R1())
        public_key = private_key.public_key()

        # Sign a message
        from cryptography.hazmat.primitives import hashes

        message = b"test message for P-384"
        der_signature = private_key.sign(message, ec.ECDSA(hashes.SHA384()))

        # Get public key numbers for JWK
        numbers = public_key.public_numbers()
        x_bytes = numbers.x.to_bytes(48, "big")
        y_bytes = numbers.y.to_bytes(48, "big")

        jwk = {
            "kty": "EC",
            "crv": "P-384",
            "x": base64.urlsafe_b64encode(x_bytes).rstrip(b"=").decode(),
            "y": base64.urlsafe_b64encode(y_bytes).rstrip(b"=").decode(),
        }

        result = verifier.verify(der_signature, message, jwk, "ES384")
        assert result is True

    def test_verify_unsupported_algorithm(self) -> None:
        """Unsupported algorithm returns False."""
        verifier = SignatureVerifier()
        result = verifier.verify(b"sig", b"msg", b"key", "RS256")
        assert result is False

    def test_verify_with_invalid_key_returns_false(self) -> None:
        """Invalid public key returns False without raising."""
        verifier = SignatureVerifier()
        result = verifier.verify(b"signature", b"message", b"invalid", "Ed25519")
        assert result is False

    def test_verify_p256_alias(self) -> None:
        """P-256 alias maps to ES256."""
        verifier = SignatureVerifier()

        # Generate a P-256 key pair
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()

        from cryptography.hazmat.primitives import hashes

        message = b"test p256 alias"
        signature = private_key.sign(message, ec.ECDSA(hashes.SHA256()))

        numbers = public_key.public_numbers()
        jwk = {
            "kty": "EC",
            "crv": "P-256",
            "x": base64.urlsafe_b64encode(numbers.x.to_bytes(32, "big")).rstrip(b"=").decode(),
            "y": base64.urlsafe_b64encode(numbers.y.to_bytes(32, "big")).rstrip(b"=").decode(),
        }

        result = verifier.verify(signature, message, jwk, "P-256")
        assert result is True

    def test_verify_p384_alias(self) -> None:
        """P-384 alias maps to ES384."""
        verifier = SignatureVerifier()

        # Generate a P-384 key pair
        private_key = ec.generate_private_key(ec.SECP384R1())
        public_key = private_key.public_key()

        from cryptography.hazmat.primitives import hashes

        message = b"test p384 alias"
        signature = private_key.sign(message, ec.ECDSA(hashes.SHA384()))

        numbers = public_key.public_numbers()
        jwk = {
            "kty": "EC",
            "crv": "P-384",
            "x": base64.urlsafe_b64encode(numbers.x.to_bytes(48, "big")).rstrip(b"=").decode(),
            "y": base64.urlsafe_b64encode(numbers.y.to_bytes(48, "big")).rstrip(b"=").decode(),
        }

        result = verifier.verify(signature, message, jwk, "P-384")
        assert result is True


class TestVerifyFromMethod:
    """Tests for verify_from_method using VerificationMethod."""

    def test_verify_from_method_with_ed25519(self) -> None:
        """Verification works with VerificationMethod object."""
        verifier = SignatureVerifier()

        # Generate key pair
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        message = b"message from method"
        signature = private_key.sign(message)

        # Create VerificationMethod with JWK
        public_bytes = public_key.public_bytes_raw()
        vm = VerificationMethod(
            id="did:key:z6Mk...#key-1",
            type="Ed25519VerificationKey2020",
            controller="did:key:z6Mk...",
            public_key_jwk={
                "kty": "OKP",
                "crv": "Ed25519",
                "x": base64.urlsafe_b64encode(public_bytes).rstrip(b"=").decode(),
            },
        )

        result = verifier.verify_from_method(signature, message, vm)
        assert result is True

    def test_verify_from_method_no_jwk(self) -> None:
        """Returns False when VerificationMethod has no JWK."""
        verifier = SignatureVerifier()

        vm = VerificationMethod(
            id="did:key:z6Mk...",
            type="Ed25519VerificationKey2020",
            controller="did:key:z6Mk...",
            public_key_jwk=None,
        )

        result = verifier.verify_from_method(b"sig", b"msg", vm)
        assert result is False


class TestJWKConversion:
    """Tests for JWK to key conversion."""

    def test_jwk_to_ed25519_invalid_kty(self) -> None:
        """Invalid kty in JWK raises ValueError."""
        verifier = SignatureVerifier()

        with pytest.raises(ValueError, match="Invalid JWK for Ed25519"):
            verifier._jwk_to_ed25519_public_key({"kty": "EC", "crv": "Ed25519"})

    def test_jwk_to_ed25519_invalid_crv(self) -> None:
        """Invalid crv in JWK raises ValueError."""
        verifier = SignatureVerifier()

        with pytest.raises(ValueError, match="Invalid JWK for Ed25519"):
            verifier._jwk_to_ed25519_public_key({"kty": "OKP", "crv": "X25519"})

    def test_jwk_to_ec_invalid_kty(self) -> None:
        """Invalid kty in EC JWK raises ValueError."""
        verifier = SignatureVerifier()

        with pytest.raises(ValueError, match="Invalid JWK for EC key"):
            verifier._jwk_to_ec_public_key({"kty": "OKP", "crv": "P-256"})

    def test_jwk_to_ec_unsupported_curve(self) -> None:
        """Unsupported EC curve raises ValueError."""
        verifier = SignatureVerifier()

        # Use valid base64 values so the curve check is reached
        with pytest.raises(ValueError, match="Unsupported curve"):
            verifier._jwk_to_ec_public_key(
                {
                    "kty": "EC",
                    "crv": "secp256k1",
                    "x": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                    "y": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                }
            )


class TestVerifyJWS:
    """Tests for JWS token verification."""

    def test_verify_jws_ed25519(self) -> None:
        """JWS with EdDSA algorithm verifies correctly."""
        import jwt

        # Generate Ed25519 key
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Create JWT/JWS
        from cryptography.hazmat.primitives.serialization import (
            Encoding,
            NoEncryption,
            PrivateFormat,
        )

        private_pem = private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
        payload = {"sub": "test", "iat": 1234567890}
        token = jwt.encode(payload, private_pem, algorithm="EdDSA")

        # Create JWK for verification
        public_bytes = public_key.public_bytes_raw()
        jwk = {
            "kty": "OKP",
            "crv": "Ed25519",
            "x": base64.urlsafe_b64encode(public_bytes).rstrip(b"=").decode(),
        }

        valid, decoded = verify_jws(token, jwk)
        assert valid is True
        assert decoded is not None
        assert decoded["sub"] == "test"

    def test_verify_jws_es256(self) -> None:
        """JWS with ES256 algorithm verifies correctly."""
        import jwt

        # Generate P-256 key
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()

        # Create JWT/JWS
        from cryptography.hazmat.primitives.serialization import (
            Encoding,
            NoEncryption,
            PrivateFormat,
        )

        private_pem = private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
        payload = {"sub": "es256-test"}
        token = jwt.encode(payload, private_pem, algorithm="ES256")

        # Create JWK for verification
        numbers = public_key.public_numbers()
        jwk = {
            "kty": "EC",
            "crv": "P-256",
            "x": base64.urlsafe_b64encode(numbers.x.to_bytes(32, "big")).rstrip(b"=").decode(),
            "y": base64.urlsafe_b64encode(numbers.y.to_bytes(32, "big")).rstrip(b"=").decode(),
        }

        valid, decoded = verify_jws(token, jwk)
        assert valid is True
        assert decoded is not None
        assert decoded["sub"] == "es256-test"

    def test_verify_jws_invalid_signature(self) -> None:
        """Invalid JWS signature returns False."""
        # Tampered token
        jwk = {"kty": "OKP", "crv": "Ed25519", "x": "abcd1234"}
        valid, decoded = verify_jws("invalid.token.here", jwk)
        assert valid is False
        assert decoded is None

    def test_verify_jws_unsupported_key_type(self) -> None:
        """Unsupported key type returns False."""
        jwk = {"kty": "RSA", "n": "abc", "e": "AQAB"}
        valid, decoded = verify_jws("some.jwt.token", jwk)
        assert valid is False
        assert decoded is None


class TestVerifySignatureFunction:
    """Tests for module-level verify_signature function."""

    def test_verify_signature_creates_verifier(self) -> None:
        """Module function creates SignatureVerifier internally."""
        # Generate key
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        message = b"module level test"
        signature = private_key.sign(message)

        result = verify_signature(
            signature,
            message,
            public_key.public_bytes_raw(),
            "Ed25519",
        )
        assert result is True


class TestSignatureInfo:
    """Tests for SignatureInfo dataclass."""

    def test_signature_info_fields(self) -> None:
        """SignatureInfo stores all fields."""
        info = SignatureInfo(
            algorithm="Ed25519",
            signature_bytes=b"signature",
            message_bytes=b"message",
            key_id="did:key:z6Mk...#key-1",
        )

        assert info.algorithm == "Ed25519"
        assert info.signature_bytes == b"signature"
        assert info.message_bytes == b"message"
        assert info.key_id == "did:key:z6Mk...#key-1"

    def test_signature_info_optional_key_id(self) -> None:
        """key_id is optional."""
        info = SignatureInfo(
            algorithm="ES256",
            signature_bytes=b"sig",
            message_bytes=b"msg",
        )
        assert info.key_id is None
