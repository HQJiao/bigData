import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from src.app.main import app


@pytest.fixture
def client():
    """带 mock 的测试客户端"""
    with TestClient(app) as c:
        yield c


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "llm-service"


def test_chat_sync(client):
    with patch("src.app.routes.create_client") as mock_create:
        mock_client = MagicMock()
        mock_client.chat.return_value = "你好！我是助手。"

        mock_graph = MagicMock()
        mock_graph.invoke.return_value = {
            "llm_response": "你好！我是助手。",
            "messages": [],
        }

        def fake_build(client):
            return mock_graph

        with patch("src.app.routes.build_chat_graph", side_effect=fake_build):
            mock_create.return_value = mock_client
            response = client.post(
                "/api/llm/chat",
                json={"message": "你好", "stream": False},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["reply"] == "你好！我是助手。"
        assert data["conversation_id"] is not None


def test_chat_missing_api_key(client):
    """API Key 未配置时返回 500"""
    with patch("src.app.routes.create_client", side_effect=ValueError("DASHSCOPE_API_KEY is not configured")):
        response = client.post(
            "/api/llm/chat",
            json={"message": "你好"},
        )
        assert response.status_code == 500
        assert "DASHSCOPE_API_KEY" in response.json()["detail"]
