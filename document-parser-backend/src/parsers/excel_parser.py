from pathlib import Path
from typing import List
import pandas as pd
from openpyxl import load_workbook

from src.parsers.base import IParser
from src.parsers.models import ParsedContent
from src.parsers.registry import parser_registry


class ExcelParser(IParser):
    def parse(self, file_path: Path) -> ParsedContent:
        ext = file_path.suffix.lower()
        
        if ext == ".csv":
            df = pd.read_csv(file_path)
        else:
            dfs = pd.read_excel(file_path, sheet_name=None)
            df = pd.concat(dfs.values(), ignore_index=True) if dfs else pd.DataFrame()
        
        text_parts = []
        # 先输出列名（表头）
        text_parts.append(" | ".join(str(c) for c in df.columns))
        for _, row in df.iterrows():
            row_text = " | ".join(str(v) for v in row.values if pd.notna(v) and str(v).strip())
            if row_text:
                text_parts.append(row_text)
        
        all_text = "\n".join(text_parts)
        
        return ParsedContent(
            text=all_text,
            parser_type="excel",
            metadata={"row_count": len(df), "column_count": len(df.columns)},
        )

    def supported_extensions(self) -> List[str]:
        return [".xlsx", ".xls", ".csv"]


parser_registry.register(ExcelParser())
