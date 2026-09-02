from agent.agent_loop import _try_parse_fallback_tool_call, _strip_leaked_tags

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

def test_parses_tool_call_wrapped_in_markdown_fence():
    content = '```json\n{"name": "grep", "arguments": {"pattern": "x", "root": "."}}\n```'
    result = _try_parse_fallback_tool_call(content)
    assert result == {"name": "grep", "arguments": {"pattern": "x", "root": "."}}

def test_parses_tool_call_after_explanatory_prose():
    content = (
        'Here is what chunk_text does: it splits text into chunks.\n\n'
        'Next, I will read the other files.\n\n'
        '{"name": "read_file", "arguments": {"path": "src/agent/config.py"}}'
    )
    result = _try_parse_fallback_tool_call(content)
    assert result == {"name": "read_file", "arguments": {"path": "src/agent/config.py"}}

def test_returns_none_when_no_json_object_present():
    assert _try_parse_fallback_tool_call("Just an explanation, no tool call here.") is None

def test_strip_leaked_tags_removes_tool_response_block():
    content = 'Some prefix <tool_response>[{"document": "..."}]</tool_response> and an actual answer.'
    assert _strip_leaked_tags(content) == "Some prefix  and an actual answer."

def test_strip_leaked_tags_leaves_normal_text_unchanged():
    assert _strip_leaked_tags("A normal answer with no leaked tags.") == "A normal answer with no leaked tags."

def test_strip_leaked_tags_handles_none():
    assert _strip_leaked_tags(None) is None
