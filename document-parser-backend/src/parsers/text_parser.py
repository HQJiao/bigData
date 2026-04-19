from pathlib import Path
from typing import List

from src.parsers.base import IParser
from src.parsers.models import ParsedContent
from src.parsers.registry import parser_registry


class TextParser(IParser):
    def parse(self, file_path: Path) -> ParsedContent:
        content = self._read_file(file_path)

        lines = content.split("\n")
        non_empty_lines = [line.strip() for line in lines if line.strip()]

        return ParsedContent(
            text=content,
            parser_type="text",
            metadata={"line_count": len(non_empty_lines)},
        )

    def _read_file(self, file_path: Path) -> str:
        for encoding in ("utf-8", "gbk", "gb2312", "latin-1"):
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, LookupError):
                continue
        raise UnicodeDecodeError("utf-8", b"", 0, 1, f"Unable to decode file: {file_path}")

    def supported_extensions(self) -> List[str]:
        return [".txt", ".md", ".json", ".xml", ".yaml", ".yml"]


parser_registry.register(TextParser())
