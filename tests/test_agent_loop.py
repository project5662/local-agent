from agent.agent_loop import _try_parse_fallback_tool_call

def test_parses_plain_json_tool_call():
    content = '{"name": "read_file", "arguments": {"path": "a.py"}}'
    result = _try_parse_fallback_tool_call(content)
    assert result == {"name": "read_file", "arguments": {"path": "a.py"}}

def test_parses_tool_call_wrapped_in_tags():
    content = '<tool_call>\n{"name": "list_dir", "arguments": {"path": "."}}\n</tool_call>'
    result = _try_parse_fallback_tool_call(content)
    assert result == {"name": "list_dir", "arguments": {"path": "."}}

def test_returns_none_for_normal_text():
    assert _try_parse_fallback_tool_call("Det här är bara ett vanligt svar.") is None
