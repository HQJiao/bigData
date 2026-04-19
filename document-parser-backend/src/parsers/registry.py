from typing import Dict, List, Optional, Type
from pathlib import Path

from src.parsers.base import IParser
from src.parsers.models import ParsedContent
from src.core.logging import get_logger

logger = get_logger("parser-registry")


class ParserRegistry:
    def __init__(self):
        self._parsers: Dict[str, IParser] = {}

    def register(self, parser: IParser) -> None:
        for ext in parser.supported_extensions():
            self._parsers[ext.lower()] = parser
            logger.info("parser_registered", extra={"extension": ext, "parser": parser.__class__.__name__})

    def get_parser(self, file_path: Path) -> Optional[IParser]:
        ext = file_path.suffix.lower()
        parser = self._parsers.get(ext)
        if parser:
            logger.debug("parser_found", extra={"extension": ext, "parser": parser.__class__.__name__})
        else:
            logger.warning("parser_not_found", extra={"extension": ext})
        return parser

    def parse_file(self, file_path: Path) -> ParsedContent:
        parser = self.get_parser(file_path)
        if not parser:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        return parser.parse(file_path)

    def is_supported(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self._parsers

    def supported_extensions(self) -> List[str]:
        return list(self._parsers.keys())


parser_registry = ParserRegistry()
