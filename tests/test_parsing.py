from ati.parsing import parse_trace, trace_features


def test_parse_basic():
    row = {
        "model": "model-atlas", "job": "run-01", "task_id": "t1", "status": "OK", "reward": 1,
        "conversation": [
            {"role": "assistant", "content": "read it", "reasoning_content": "plan", "tool_calls": [{"function": {"name": "read", "arguments": '{"path":"a.py"}'}}]},
            {"role": "tool", "content": "hello"},
            {"role": "assistant", "content": "done"},
        ],
        "proxy_requests": [200, 200],
    }
    eps = parse_trace(row, "tr1")
    assert eps[0].tool == "read"
    assert eps[0].tool_args
    assert eps[0].tool_result == "hello"
    f = trace_features(row, "tr1")
    assert f["n_tool_calls"] == 1
    assert f["proxy_429"] == 0
