from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    dashscope_api_key: str = ""
    llm_model: str = "qwen-turbo"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2048
    host: str = "0.0.0.0"
    port: int = 8001

    class Config:
        env_file = ".env"


settings = Settings()
