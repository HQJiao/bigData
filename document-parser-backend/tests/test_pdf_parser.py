import pytest
from pathlib import Path

from src.parsers.pdf_parser import PdfTextParser


def test_pdf_parser_supported_extensions():
    parser = PdfTextParser()
    assert ".pdf" in parser.supported_extensions()


def test_pdf_parser_with_real_file():
    parser = PdfTextParser()
    pdf_path = Path("tests/assets/纪检数据处理方案评估.pdf")
    
    if not pdf_path.exists():
        pytest.skip("Test PDF file not found")
    
    result = parser.parse(pdf_path)
    assert result.parser_type == "pdf_text"
    assert len(result.text) > 0
    assert "纪检" in result.text or "方案" in result.text


def test_pdf_parser_metadata():
    parser = PdfTextParser()
    pdf_path = Path("tests/assets/纪检数据处理方案评估.pdf")
    
    if not pdf_path.exists():
        pytest.skip("Test PDF file not found")
    
    result = parser.parse(pdf_path)
    assert "line_count" in result.metadata
    assert result.metadata["line_count"] > 0
