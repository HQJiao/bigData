import pytest
from unittest.mock import patch, MagicMock
from src.clients.dashscope import DashScopeClient


class MockResponse:
    def __init__(self, content, status_code=200):
        self.status_code = status_code
        self.code = "200" if status_code == 200 else "500"
        self.message = "OK" if status_code == 200 else "Error"
        self.output = MagicMock()
        choice = MagicMock()
        choice.message.content = content
        self.output.choices = [choice]


def test_chat_success():
    client = DashScopeClient(
        api_key="test-key",
        model="qwen-turbo",
        temperature=0.7,
        max_tokens=100,
    )

    with patch("src.clients.dashscope.Generation") as mock_gen:
        mock_gen.call.return_value = MockResponse("你好，我是助手。")
        result = client.chat([{"role": "user", "content": "你好"}])
        assert result == "你好，我是助手。"
        mock_gen.call.assert_called_once()
        call_kwargs = mock_gen.call.call_args[1]
        assert call_kwargs["model"] == "qwen-turbo"
        assert call_kwargs["temperature"] == 0.7


def test_chat_api_error():
    client = DashScopeClient(
        api_key="bad-key",
        model="qwen-turbo",
        temperature=0.7,
        max_tokens=100,
    )

    with patch("src.clients.dashscope.Generation") as mock_gen:
        mock_gen.call.return_value = MockResponse("", status_code=500)
        with pytest.raises(RuntimeError, match="DashScope API error"):
            client.chat([{"role": "user", "content": "test"}])


@pytest.mark.asyncio
async def test_chat_stream_success():
    client = DashScopeClient(
        api_key="test-key",
        model="qwen-turbo",
        temperature=0.7,
        max_tokens=100,
    )

    class MockStreamResponse:
        def __init__(self, content):
            self.status_code = 200
            self.output = MagicMock()
            choice = MagicMock()
            choice.message = {"content": content}
            self.output.choices = [choice]

    with patch("src.clients.dashscope.Generation") as mock_gen:
        mock_gen.call.return_value = [
            MockStreamResponse("你"),
            MockStreamResponse("好"),
            MockStreamResponse("!"),
        ]
        chunks = []
        async for chunk in client.chat_stream([{"role": "user", "content": "hi"}]):
            chunks.append(chunk)
        assert chunks == ["你", "好", "!"]
