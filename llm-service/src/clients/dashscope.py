from typing import AsyncGenerator

from dashscope import Generation


class DashScopeClient:
    """DashScope (阿里百炼) API 封装"""

    def __init__(self, api_key: str, model: str, temperature: float, max_tokens: int):
        import dashscope

        dashscope.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def chat(self, messages: list[dict]) -> str:
        """同步对话，返回完整文本"""
        response = Generation.call(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            result_format="message",
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"DashScope API error: {response.code} — {response.message}"
            )
        return response.output.choices[0].message.content

    async def chat_stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        """流式对话，yield 每个 token"""
        responses = Generation.call(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            result_format="message",
            stream=True,
        )
        for response in responses:
            if response.status_code != 200:
                raise RuntimeError(
                    f"DashScope API error: {response.code} — {response.message}"
                )
            content = response.output.choices[0].message.get("content", "")
            if content:
                yield content
