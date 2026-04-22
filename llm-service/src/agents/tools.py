from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Tool 抽象接口 — 后续 RAG 升级时新增 Tool 实现此类即可"""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @abstractmethod
    async def run(self, **kwargs: Any) -> str:
        ...


class SearchDocumentsTool(BaseTool):
    """简单文本匹配搜索已上传文档"""

    @property
    def name(self) -> str:
        return "search_documents"

    @property
    def description(self) -> str:
        return "Search in uploaded documents. Accepts 'query' parameter."

    async def run(self, query: str = "", doc_ids: list[str] | None = None, **kwargs: Any) -> str:
        from src.clients.document_client import DocumentClient

        client = DocumentClient()
        if doc_ids:
            # 获取指定文档的完整内容
            results = []
            for doc_id in doc_ids:
                try:
                    doc = await client.get_document(doc_id)
                    content = doc.get("content", "")
                    if content:
                        results.append(f"【{doc['filename']}】\n{content}")
                    else:
                        results.append(f"【{doc.get('filename', doc_id)}】内容为空或解析失败。")
                except Exception:
                    results.append(f"文档 {doc_id} 获取失败。")
            return "\n\n---\n\n".join(results) if results else "指定文档中未找到相关内容。"

        # 搜索所有已完成文档
        docs = await client.list_documents()
        completed = [d for d in docs if d.get("status") == "completed"]
        results = []
        for doc in completed[:20]:  # 限制数量
            full = await client.get_document(doc["id"])
            content = full.get("content", "")
            if query.lower() in content.lower():
                # 提取匹配上下文
                idx = content.lower().index(query.lower())
                start = max(0, idx - 50)
                end = min(len(content), idx + len(query) + 50)
                snippet = content[start:end].strip()
                results.append(f"【{doc['filename']}】...\n{snippet}\n...")
                if len(results) >= 5:
                    break
        return "\n\n---\n\n".join(results) if results else "未找到相关内容。"


# 已注册的工具列表
available_tools: list[BaseTool] = [SearchDocumentsTool()]
