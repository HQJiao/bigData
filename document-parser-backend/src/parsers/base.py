from typing import Protocol, List
from pathlib import Path
from src.parsers.models import ParsedContent


class IParser(Protocol):
    def parse(self, file_path: Path) -> ParsedContent:
        """解析文件并返回内容"""
        ...

    def supported_extensions(self) -> List[str]:
        """返回支持的文件扩展名列表"""
        ...
