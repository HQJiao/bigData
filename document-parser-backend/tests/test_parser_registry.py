import pytest
from pathlib import Path
from unittest.mock import MagicMock

from src.parsers.registry import ParserRegistry
from src.parsers.base import IParser
from src.parsers.models import ParsedContent


class MockParser(IParser):
    def __init__(self, extensions: list[str]):
        self._extensions = extensions

    def parse(self, file_path: Path) -> ParsedContent:
        return ParsedContent(text="mocked", parser_type="mock")

    def supported_extensions(self) -> list[str]:
        return self._extensions


def test_parser_registry_register():
    registry = ParserRegistry()
    parser = MockParser([".txt", ".log"])
    registry.register(parser)
    assert ".txt" in registry.supported_extensions()
    assert ".log" in registry.supported_extensions()


def test_parser_registry_get_parser():
    registry = ParserRegistry()
    parser = MockParser([".test"])
    registry.register(parser)
    found = registry.get_parser(Path("file.test"))
    assert found is parser


def test_parser_registry_is_supported():
    registry = ParserRegistry()
    parser = MockParser([".supported"])
    registry.register(parser)
    assert registry.is_supported(Path("file.supported")) is True
    assert registry.is_supported(Path("file.unsupported")) is False


def test_parser_registry_parse_file():
    registry = ParserRegistry()
    mock_parser = MockParser([".mock"])
    registry.register(mock_parser)
    result = registry.parse_file(Path("file.mock"))
    assert result.text == "mocked"
    assert result.parser_type == "mock"


def test_parser_registry_parse_unsupported():
    registry = ParserRegistry()
    with pytest.raises(ValueError, match="Unsupported file format"):
        registry.parse_file(Path("file.unknown"))
