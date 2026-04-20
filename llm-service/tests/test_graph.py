from unittest.mock import patch, MagicMock
from src.clients.dashscope import DashScopeClient
from src.graph.chat_graph import build_chat_graph


def test_graph_single_turn():
    client = DashScopeClient(
        api_key="test", model="qwen-turbo", temperature=0.7, max_tokens=100
    )

    with patch("src.clients.dashscope.Generation") as mock_gen:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.output.choices = [MagicMock()]
        mock_resp.output.choices[0].message.content = "这是回答。"
        mock_gen.call.return_value = mock_resp

        graph = build_chat_graph(client)
        result = graph.invoke({"messages": [("human", "你好")]})

        assert result["llm_response"] == "这是回答。"
        assert len(result["messages"]) == 2  # HumanMessage + AIMessage


def test_graph_multi_turn():
    client = DashScopeClient(
        api_key="test", model="qwen-turbo", temperature=0.7, max_tokens=100
    )

    with patch("src.clients.dashscope.Generation") as mock_gen:
        mock_resp1 = MagicMock()
        mock_resp1.status_code = 200
        mock_resp1.output.choices = [MagicMock()]
        mock_resp1.output.choices[0].message.content = "北京。"
        mock_resp2 = MagicMock()
        mock_resp2.status_code = 200
        mock_resp2.output.choices = [MagicMock()]
        mock_resp2.output.choices[0].message.content = "故宫。"
        mock_gen.call.side_effect = [mock_resp1, mock_resp2]

        graph = build_chat_graph(client)

        # 第一轮
        result = graph.invoke({"messages": [("human", "中国首都是哪？")]})
        assert result["llm_response"] == "北京。"

        # 第二轮（复用之前的 messages）
        result = graph.invoke(
            {"messages": result["messages"] + [("human", "有什么著名景点？")]}
        )
        assert result["llm_response"] == "故宫。"
        # messages 应包含: 2 条第一轮 + 1 条新的 human = 3
        assert len(result["messages"]) >= 3
