from src.app.settings import Settings


def test_default_settings():
    """默认值测试"""
    s = Settings(_env_file=None)
    assert s.llm_model == "qwen-turbo"
    assert s.llm_temperature == 0.7
    assert s.llm_max_tokens == 2048
    assert s.host == "0.0.0.0"
    assert s.port == 8001


def test_env_var_override():
    """环境变量覆盖测试"""
    s = Settings(
        dashscope_api_key="test-key",
        llm_model="qwen-plus",
        llm_temperature=0.5,
        _env_file=None,
    )
    assert s.dashscope_api_key == "test-key"
    assert s.llm_model == "qwen-plus"
    assert s.llm_temperature == 0.5
