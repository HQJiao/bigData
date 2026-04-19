from pathlib import Path
from typing import List
from src.parsers.base import IParser
from src.parsers.models import ParsedContent
from src.parsers.registry import parser_registry


class OcrParser(IParser):
    def __init__(self):
        self._ocr = None

    @property
    def ocr(self):
        if self._ocr is None:
            from paddleocr import PaddleOCR
            self._ocr = PaddleOCR(lang="ch")
        return self._ocr

    def parse(self, file_path: Path) -> ParsedContent:
        ext = file_path.suffix.lower()

        if ext not in [".png", ".jpg", ".jpeg", ".bmp"]:
            raise ValueError(f"OcrParser does not support format: {ext}")

        result = self.ocr.predict(str(file_path))

        text_lines = []
        if result and isinstance(result, list) and result[0]:
            rec_texts = result[0].get("rec_texts", [])
            text_lines = [t for t in rec_texts if t]

        all_text = "\n".join(text_lines)

        return ParsedContent(
            text=all_text,
            parser_type="ocr",
            metadata={"line_count": len(text_lines)},
        )

    def supported_extensions(self) -> List[str]:
        return [".png", ".jpg", ".jpeg", ".bmp"]


parser_registry.register(OcrParser())
