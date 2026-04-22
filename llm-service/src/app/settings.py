from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Provider 选择: dashscope | openrouter
    llm_provider: str = "dashscope"

    # 百炼 (DashScope) 配置
    dashscope_api_key: str = ""
    dashscope_model: str = "qwen-turbo"

    # OpenRouter 配置
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # 通用参数
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2048
    host: str = "0.0.0.0"
    port: int = 8001

    # 文档服务地址
    doc_parser_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"


settings = Settings()
