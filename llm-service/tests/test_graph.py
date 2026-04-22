from unittest.mock import patch, MagicMock
from src.agents.agent_graph import build_agent_graph


def test_graph_single_turn():
    with patch("src.agents.agent_graph.create_client") as mock_create:
        mock_client = MagicMock()
        mock_client.chat.return_value = "这是回答。"
        mock_create.return_value = mock_client

        graph = build_agent_graph()
        result = graph.invoke({"messages": [("human", "你好")], "tools_used": []})

        assert result["llm_response"] == "这是回答。"


def test_graph_multi_turn():
    with patch("src.agents.agent_graph.create_client") as mock_create:
        mock_client = MagicMock()
        mock_client.chat.side_effect = ["北京。", "故宫。"]
        mock_create.return_value = mock_client

        graph = build_agent_graph()

        # 第一轮
        result = graph.invoke({"messages": [("human", "中国首都是哪？")], "tools_used": []})
        assert result["llm_response"] == "北京。"

        # 第二轮（复用之前的 messages）
        result = graph.invoke(
            {"messages": result["messages"] + [("human", "有什么著名景点？")], "tools_used": []}
        )
        assert result["llm_response"] == "故宫。"
