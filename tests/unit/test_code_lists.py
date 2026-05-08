"""Unit tests for extended code list validation."""

from dppvalidator.vocabularies.code_lists import (
    extract_gtin_from_gs1_digital_link,
    get_hs_chapter_description,
    get_hs_codes,
    get_material_codes,
    is_textile_hs_code,
    is_valid_gs1_digital_link,
    is_valid_hs_code,
    is_valid_material_code,
    validate_gtin,
)


class TestMaterialCodes:
    """Tests for UNECE Rec 46 material code validation."""

    def test_valid_material_codes(self) -> None:
        """Valid material codes are accepted."""
        assert is_valid_material_code("COTTON") is True
        assert is_valid_material_code("POLYESTER") is True
        assert is_valid_material_code("WOOL") is True
        assert is_valid_material_code("SILK") is True

    def test_case_insensitive(self) -> None:
        """Material codes are case-insensitive."""
        assert is_valid_material_code("cotton") is True
        assert is_valid_material_code("Cotton") is True
        assert is_valid_material_code("COTTON") is True

    def test_normalized_codes(self) -> None:
        """Material codes with spaces/hyphens are normalized."""
        assert is_valid_material_code("RECYCLED COTTON") is True
        assert is_valid_material_code("RECYCLED-COTTON") is True
        assert is_valid_material_code("recycled_cotton") is True

    def test_invalid_material_codes(self) -> None:
        """Invalid material codes are rejected."""
        assert is_valid_material_code("UNKNOWN_MATERIAL") is False
        assert is_valid_material_code("XYZ123") is False
        assert is_valid_material_code("") is False

    def test_get_material_codes_returns_frozenset(self) -> None:
        """get_material_codes returns a frozenset."""
        codes = get_material_codes()
        assert isinstance(codes, frozenset)
        assert len(codes) > 0
        assert "COTTON" in codes


class TestHSCodes:
    """Tests for HS (Harmonized System) code validation."""

    def test_valid_hs_codes(self) -> None:
        """Valid textile HS codes are accepted."""
        assert is_valid_hs_code("5201") is True  # Cotton
        assert is_valid_hs_code("5208") is True  # Cotton woven
        assert is_valid_hs_code("6101") is True  # Apparel knitted

    def test_hs_code_with_dots(self) -> None:
        """HS codes with dots are normalized."""
        assert is_valid_hs_code("52.01") is True
        assert is_valid_hs_code("52.08") is True

    def test_invalid_hs_codes(self) -> None:
        """Invalid HS codes are rejected."""
        assert is_valid_hs_code("9999") is False
        assert is_valid_hs_code("1234") is False
        assert is_valid_hs_code("") is False

    def test_is_textile_hs_code(self) -> None:
        """Textile chapter detection works."""
        assert is_textile_hs_code("5201") is True  # Chapter 52
        assert is_textile_hs_code("6301") is True  # Chapter 63
        assert is_textile_hs_code("5001") is True  # Chapter 50
        assert is_textile_hs_code("4901") is False  # Chapter 49 (not textile)
        assert is_textile_hs_code("6401") is False  # Chapter 64 (not textile)

    def test_get_hs_codes_returns_frozenset(self) -> None:
        """get_hs_codes returns a frozenset."""
        codes = get_hs_codes()
        assert isinstance(codes, frozenset)
        assert len(codes) > 0
        assert "5201" in codes

    def test_get_hs_chapter_description(self) -> None:
        """Chapter descriptions are returned correctly."""
        assert get_hs_chapter_description("5201") == "Cotton"
        assert get_hs_chapter_description("5101") == "Wool, fine or coarse animal hair"
        assert get_hs_chapter_description("6101") == "Articles of apparel, knitted or crocheted"
        assert get_hs_chapter_description("9901") is None


class TestGTINValidation:
    """Tests for GS1 GTIN checksum validation."""

    def test_valid_gtin13(self) -> None:
        """Valid GTIN-13 numbers pass checksum."""
        # Example valid GTIN-13
        assert validate_gtin("5901234123457") is True
        assert validate_gtin("4006381333931") is True

    def test_valid_gtin8(self) -> None:
        """Valid GTIN-8 numbers pass checksum."""
        assert validate_gtin("96385074") is True

    def test_valid_gtin14(self) -> None:
        """Valid GTIN-14 numbers pass checksum."""
        assert validate_gtin("10614141000415") is True

    def test_invalid_gtin_checksum(self) -> None:
        """Invalid GTIN checksums are rejected."""
        # Same as valid but last digit changed
        assert validate_gtin("5901234123458") is False
        assert validate_gtin("4006381333932") is False

    def test_invalid_gtin_length(self) -> None:
        """Invalid GTIN lengths are rejected."""
        assert validate_gtin("123") is False
        assert validate_gtin("12345678901234567") is False
        assert validate_gtin("") is False

    def test_gtin_with_non_digits(self) -> None:
        """Non-digit characters are stripped."""
        # Valid GTIN-13 with formatting
        assert validate_gtin("590-123-412345-7") is True


class TestGS1DigitalLink:
    """Tests for GS1 Digital Link URL handling."""

    def test_extract_gtin_from_url(self) -> None:
        """GTIN is extracted from GS1 Digital Link URL."""
        url = "https://id.gs1.org/01/09506000134352"
        assert extract_gtin_from_gs1_digital_link(url) == "09506000134352"

    def test_extract_gtin_with_additional_path(self) -> None:
        """GTIN is extracted even with additional path segments."""
        url = "https://example.com/01/09506000134352/21/12345"
        assert extract_gtin_from_gs1_digital_link(url) == "09506000134352"

    def test_extract_gtin_no_match(self) -> None:
        """None is returned when no GTIN found."""
        assert extract_gtin_from_gs1_digital_link("https://example.com") is None
        assert extract_gtin_from_gs1_digital_link("https://example.com/product/123") is None

    def test_is_valid_gs1_digital_link(self) -> None:
        """Valid GS1 Digital Links are accepted."""
        # This requires a valid GTIN with correct checksum
        # Using a made-up but checksum-valid GTIN
        valid_url = "https://id.gs1.org/01/5901234123457"
        assert is_valid_gs1_digital_link(valid_url) is True

    def test_invalid_gs1_digital_link(self) -> None:
        """Invalid GS1 Digital Links are rejected."""
        invalid_url = "https://id.gs1.org/01/5901234123458"  # Bad checksum
        assert is_valid_gs1_digital_link(invalid_url) is False


class TestVocabularyModuleExports:
    """Tests for vocabulary module exports."""

    def test_code_lists_exported(self) -> None:
        """Code list functions are exported from vocabularies.code_lists submodule."""
        from dppvalidator.vocabularies import (
            is_valid_hs_code,
            is_valid_material_code,
            validate_gtin,
        )
        from dppvalidator.vocabularies.code_lists import (
            get_hs_codes,
            get_material_codes,
            is_textile_hs_code,
            is_valid_gs1_digital_link,
        )

        assert callable(get_material_codes)
        assert callable(get_hs_codes)
        assert callable(is_valid_material_code)
        assert callable(is_valid_hs_code)
        assert callable(is_textile_hs_code)
        assert callable(validate_gtin)
        assert callable(is_valid_gs1_digital_link)


class TestValidationRulesExported:
    """Tests for validation rules being exported."""

    def test_voc_rules_in_all_rules(self) -> None:
        """VOC003-VOC005 rules are in ALL_RULES."""
        from dppvalidator.validators.rules import ALL_RULES

        rule_ids = [rule.rule_id for rule in ALL_RULES]
        assert "VOC003" in rule_ids
        assert "VOC004" in rule_ids
        assert "VOC005" in rule_ids

    def test_rule_classes_exported(self) -> None:
        """Rule classes are exported from rules module."""
        from dppvalidator.validators.rules import (
            GTINChecksumRule,
            HSCodeRule,
            MaterialCodeRule,
        )

        assert MaterialCodeRule.rule_id == "VOC003"
        assert HSCodeRule.rule_id == "VOC004"
        assert GTINChecksumRule.rule_id == "VOC005"


class TestCodeListErrorHandling:
    """Tests for error handling in code list loading."""

    def test_load_code_list_file_not_found(self) -> None:
        """Missing code list file returns empty frozenset."""
        from unittest.mock import MagicMock, patch

        from dppvalidator.vocabularies.code_lists import _load_code_list

        mock_data_files = MagicMock()
        mock_path = MagicMock()
        mock_path.read_text.side_effect = FileNotFoundError("File not found")
        mock_data_files.joinpath.return_value = mock_path

        with patch(
            "dppvalidator.vocabularies.code_lists._get_data_files",
            return_value=mock_data_files,
        ):
            result = _load_code_list("nonexistent")

        assert result == frozenset()

    def test_load_code_list_invalid_json(self) -> None:
        """Invalid JSON in code list file returns empty frozenset."""
        from unittest.mock import MagicMock, patch

        from dppvalidator.vocabularies.code_lists import _load_code_list

        mock_data_files = MagicMock()
        mock_path = MagicMock()
        mock_path.read_text.return_value = "{ invalid json }"
        mock_data_files.joinpath.return_value = mock_path

        with patch(
            "dppvalidator.vocabularies.code_lists._get_data_files",
            return_value=mock_data_files,
        ):
            result = _load_code_list("invalid")

        assert result == frozenset()


class TestTextileHSCodeEdgeCases:
    """Tests for edge cases in textile HS code validation."""

    def test_empty_code_returns_false(self) -> None:
        """Empty code returns False."""
        assert is_textile_hs_code("") is False

    def test_single_char_returns_false(self) -> None:
        """Single character code returns False."""
        assert is_textile_hs_code("5") is False

    def test_non_numeric_chapter_returns_false(self) -> None:
        """Non-numeric chapter code returns False."""
        assert is_textile_hs_code("AB01") is False
        assert is_textile_hs_code("XX") is False


class TestHSChapterDescriptionEdgeCases:
    """Tests for edge cases in HS chapter description."""

    def test_empty_code_returns_none(self) -> None:
        """Empty code returns None."""
        assert get_hs_chapter_description("") is None

    def test_single_char_returns_none(self) -> None:
        """Single character code returns None."""
        assert get_hs_chapter_description("5") is None

    def test_unknown_chapter_returns_none(self) -> None:
        """Unknown chapter returns None."""
        assert get_hs_chapter_description("9901") is None
        assert get_hs_chapter_description("0100") is None
