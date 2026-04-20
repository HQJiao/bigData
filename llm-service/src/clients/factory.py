from src.app.settings import settings
from src.clients.dashscope import DashScopeClient
from src.clients.openrouter import OpenRouterClient


def create_client():
    """根据配置创建 LLM 客户端"""
    provider = settings.llm_provider.lower()

    if provider == "dashscope":
        if not settings.dashscope_api_key:
            raise ValueError("DASHSCOPE_API_KEY is not configured")
        return DashScopeClient(
            api_key=settings.dashscope_api_key,
            model=settings.dashscope_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )
    elif provider == "openrouter":
        if not settings.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY is not configured")
        return OpenRouterClient(
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
            base_url=settings.openrouter_base_url,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}. Use 'dashscope' or 'openrouter'.")
