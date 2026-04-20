import pytest
from unittest.mock import patch
from src.clients.factory import create_client
from src.clients.dashscope import DashScopeClient
from src.clients.openrouter import OpenRouterClient


def test_create_dashscope_client():
    """DashScope provider 创建正确的客户端"""
    with patch("src.clients.factory.settings") as mock_settings:
        mock_settings.llm_provider = "dashscope"
        mock_settings.dashscope_api_key = "test-key"
        mock_settings.dashscope_model = "qwen-turbo"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 1024

        client = create_client()
        assert isinstance(client, DashScopeClient)
        assert client.model == "qwen-turbo"
        assert client.temperature == 0.7


def test_create_openrouter_client():
    """OpenRouter provider 创建正确的客户端"""
    with patch("src.clients.factory.settings") as mock_settings:
        mock_settings.llm_provider = "openrouter"
        mock_settings.openrouter_api_key = "or-key"
        mock_settings.openrouter_model = "openai/gpt-4o"
        mock_settings.openrouter_base_url = "https://openrouter.ai/api/v1"
        mock_settings.llm_temperature = 0.5
        mock_settings.llm_max_tokens = 2048

        client = create_client()
        assert isinstance(client, OpenRouterClient)
        assert client.model == "openai/gpt-4o"
        assert client.temperature == 0.5


def test_missing_dashscope_key():
    """DashScope 缺少 API Key 时报错"""
    with patch("src.clients.factory.settings") as mock_settings:
        mock_settings.llm_provider = "dashscope"
        mock_settings.dashscope_api_key = ""
        with pytest.raises(ValueError, match="DASHSCOPE_API_KEY"):
            create_client()


def test_missing_openrouter_key():
    """OpenRouter 缺少 API Key 时报错"""
    with patch("src.clients.factory.settings") as mock_settings:
        mock_settings.llm_provider = "openrouter"
        mock_settings.openrouter_api_key = ""
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
            create_client()


def test_unsupported_provider():
    """不支持的 provider 时报错"""
    with patch("src.clients.factory.settings") as mock_settings:
        mock_settings.llm_provider = "unknown"
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            create_client()
