from pathlib import Path
from typing import List
import mailparser

from src.parsers.base import IParser
from src.parsers.models import ParsedContent
from src.parsers.registry import parser_registry


class EmlParser(IParser):
    def parse(self, file_path: Path) -> ParsedContent:
        mail = mailparser.parse_from_file(str(file_path))
        
        parts = []
        
        if mail.subject:
            parts.append(f"Subject: {mail.subject}")
        
        if mail.from_:
            parts.append(f"From: {mail.from_}")
        
        if mail.to:
            parts.append(f"To: {mail.to}")
        
        if mail.date:
            parts.append(f"Date: {mail.date}")
        
        parts.append("")
        
        if mail.body:
            parts.append(mail.body)
        
        for attachment in mail.attachments:
            parts.append(f"\n[Attachment: {attachment['filename']}]")
        
        all_text = "\n".join(parts)
        
        return ParsedContent(
            text=all_text,
            parser_type="eml",
            metadata={
                "subject": mail.subject,
                "from": mail.from_,
                "to": mail.to,
                "attachment_count": len(mail.attachments),
            },
        )

    def supported_extensions(self) -> List[str]:
        return [".eml"]


parser_registry.register(EmlParser())
