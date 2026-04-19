from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ParsedContent:
    text: str
    parser_type: str
    metadata: dict = field(default_factory=dict)
    page_count: Optional[int] = None
    table_count: Optional[int] = None
