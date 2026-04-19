from pathlib import Path
from typing import List
import msg_parser

from src.parsers.base import IParser
from src.parsers.models import ParsedContent
from src.parsers.registry import parser_registry


class MsgParser(IParser):
    def parse(self, file_path: Path) -> ParsedContent:
        msg = msg_parser.parse(str(file_path))
        
        parts = []
        
        if msg.subject:
            parts.append(f"Subject: {msg.subject}")
        
        if msg.sender:
            parts.append(f"From: {msg.sender}")
        
        if msg.recipients:
            parts.append(f"To: {msg.recipients}")
        
        if msg.date:
            parts.append(f"Date: {msg.date}")
        
        parts.append("")
        
        if msg.body:
            parts.append(msg.body)
        
        all_text = "\n".join(parts)
        
        return ParsedContent(
            text=all_text,
            parser_type="msg",
            metadata={
                "subject": msg.subject,
                "sender": msg.sender,
                "recipients": msg.recipients,
            },
        )

    def supported_extensions(self) -> List[str]:
        return [".msg"]


parser_registry.register(MsgParser())
