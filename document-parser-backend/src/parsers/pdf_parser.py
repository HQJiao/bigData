from pathlib import Path
from typing import List
from pdfminer.high_level import extract_text
from pdfminer.pdfparser import PDFSyntaxError

from src.parsers.base import IParser
from src.parsers.models import ParsedContent
from src.parsers.registry import parser_registry


class PdfTextParser(IParser):
    def parse(self, file_path: Path) -> ParsedContent:
        text = extract_text(file_path)
        
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        return ParsedContent(
            text="\n".join(lines),
            parser_type="pdf_text",
            metadata={"line_count": len(lines)},
        )

    def supported_extensions(self) -> List[str]:
        return [".pdf"]


parser_registry.register(PdfTextParser())
