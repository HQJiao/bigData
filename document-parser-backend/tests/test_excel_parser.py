import pytest
import tempfile
from pathlib import Path

from src.parsers.excel_parser import ExcelParser


def test_excel_parser_supported_extensions():
    parser = ExcelParser()
    extensions = parser.supported_extensions()
    assert ".xlsx" in extensions
    assert ".xls" in extensions
    assert ".csv" in extensions


def test_excel_parser_csv():
    parser = ExcelParser()
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", encoding="utf-8") as f:
        f.write("name,age,city\n")
        f.write("Alice,25,Beijing\n")
        f.write("Bob,30,Shanghai\n")
        temp_path = Path(f.name)

    try:
        result = parser.parse(temp_path)
        assert result.parser_type == "excel"
        assert "Alice" in result.text
        assert "Bob" in result.text
        assert result.metadata["row_count"] == 2
    finally:
        temp_path.unlink()


def test_excel_parser_metadata():
    parser = ExcelParser()
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", encoding="utf-8") as f:
        f.write("a,b\n1,2\n")
        temp_path = Path(f.name)

    try:
        result = parser.parse(temp_path)
        assert "column_count" in result.metadata
    finally:
        temp_path.unlink()
