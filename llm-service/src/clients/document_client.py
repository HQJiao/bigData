import httpx


class DocumentClient:
    """从主文档服务拉取文档列表和内容"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    async def list_documents(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/files", params={"page": 1, "page_size": 100})
            resp.raise_for_status()
            return resp.json().get("items", [])

    async def get_document(self, doc_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/files/{doc_id}")
            resp.raise_for_status()
            return resp.json()
