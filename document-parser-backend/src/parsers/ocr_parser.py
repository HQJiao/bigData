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
            self._ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
        return self._ocr

    def parse(self, file_path: Path) -> ParsedContent:
        ext = file_path.suffix.lower()
        
        if ext in [".png", ".jpg", ".jpeg", ".bmp"]:
            result = self.ocr.ocr(str(file_path), cls=True)
        else:
            raise ValueError(f"OcrParser does not support format: {ext}")
        
        text_lines = []
        if result and result[0]:
            for line in result[0]:
                if line and len(line) >= 2:
                    text = line[1][0]
                    text_lines.append(text)
        
        all_text = "\n".join(text_lines)
        
        return ParsedContent(
            text=all_text,
            parser_type="ocr",
            metadata={"line_count": len(text_lines)},
        )

    def supported_extensions(self) -> List[str]:
        return [".png", ".jpg", ".jpeg", ".bmp"]


parser_registry.register(OcrParser())
