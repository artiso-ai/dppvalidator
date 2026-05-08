"""Tests for vocabulary loader error handling."""

from unittest.mock import MagicMock, patch


class TestBundledVocabularyLoading:
    """Tests for bundled vocabulary loading error paths."""

    def test_load_bundled_vocabulary_file_not_found(self) -> None:
        """Missing bundled vocabulary file returns empty frozenset."""
        from dppvalidator.vocabularies.loader import _load_bundled_vocabulary

        mock_data_files = MagicMock()
        mock_path = MagicMock()
        mock_path.read_text.side_effect = FileNotFoundError("File not found")
        mock_data_files.joinpath.return_value = mock_path

        with patch(
            "dppvalidator.vocabularies.loader._get_data_files",
            return_value=mock_data_files,
        ):
            result = _load_bundled_vocabulary("nonexistent")

        assert result == frozenset()

    def test_load_bundled_vocabulary_invalid_json(self) -> None:
        """Invalid JSON in bundled vocabulary returns empty frozenset."""
        from dppvalidator.vocabularies.loader import _load_bundled_vocabulary

        mock_data_files = MagicMock()
        mock_path = MagicMock()
        mock_path.read_text.return_value = "{ invalid json }"
        mock_data_files.joinpath.return_value = mock_path

        with patch(
            "dppvalidator.vocabularies.loader._get_data_files",
            return_value=mock_data_files,
        ):
            result = _load_bundled_vocabulary("invalid")

        assert result == frozenset()

    def test_load_bundled_vocabulary_os_error(self) -> None:
        """OSError during bundled vocabulary load returns empty frozenset."""
        from dppvalidator.vocabularies.loader import _load_bundled_vocabulary

        mock_data_files = MagicMock()
        mock_path = MagicMock()
        mock_path.read_text.side_effect = OSError("Permission denied")
        mock_data_files.joinpath.return_value = mock_path

        with patch(
            "dppvalidator.vocabularies.loader._get_data_files",
            return_value=mock_data_files,
        ):
            result = _load_bundled_vocabulary("protected")

        assert result == frozenset()
