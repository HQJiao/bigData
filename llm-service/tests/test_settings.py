from src.app.settings import Settings


def test_default_settings():
    """默认值测试"""
    s = Settings(_env_file=None)
    assert s.llm_provider == "dashscope"
    assert s.dashscope_model == "qwen-turbo"
    assert s.openrouter_model == "openai/gpt-4o-mini"
    assert s.openrouter_base_url == "https://openrouter.ai/api/v1"
    assert s.llm_temperature == 0.7
    assert s.llm_max_tokens == 2048
    assert s.host == "0.0.0.0"
    assert s.port == 8001


def test_env_var_override():
    """环境变量覆盖测试"""
    s = Settings(
        llm_provider="openrouter",
        openrouter_api_key="test-key",
        openrouter_model="anthropic/claude-3.5-sonnet",
        llm_temperature=0.5,
        _env_file=None,
    )
    assert s.llm_provider == "openrouter"
    assert s.openrouter_api_key == "test-key"
    assert s.openrouter_model == "anthropic/claude-3.5-sonnet"
    assert s.llm_temperature == 0.5
