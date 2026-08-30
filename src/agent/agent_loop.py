import json
from . import config
from .ollama_client import chat

def _try_parse_fallback_tool_call(content):
    if content == None:
        return None

    text = content.replace("<tool_call>", "").replace("</tool_call>", "")
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None

    if isinstance(data, dict) and "name" in data and "arguments" in data:
        return data
    return None

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the full contents of a file at the given path.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": "Search for a text pattern across files under a root directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "root": {"type": "string"},
                },
                "required": ["pattern", "root"]
               
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List files and directories directly under a path.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "Semantically search the indexed codebase for relevant snippets",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer"}
                },
                "required": ["query", "top_k"]                              
            },
        },
    },
]

def run_agent_loop(user_message: str, history: list[dict], tool_dispatch: dict):
    history.append({"role": "user", "content": user_message})

    for _ in range(config.MAX_AGENT_ITERATIONS):
        try:
            message = chat(history, tools=TOOL_SCHEMAS)
        except Exception as e:
            return f"Fel vid anrop till modellen: {e}"

        history.append({"role": "assistant", "content": message.content, "tool_calls": message.tool_calls})

        if not message.tool_calls:
            fallback = _try_parse_fallback_tool_call(message.content)
            if fallback is None:
                return message.content
            function_name = fallback["name"]
            arguments = fallback["arguments"]

            try:
                result = tool_dispatch[function_name](**arguments)
            except Exception as e:
                result = f"Error running {function_name}: {e}"

            history.append({"role": "tool", "content": str(result), "name": function_name})
            continue

        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            arguments = tool_call.function.arguments

            try:
                result = tool_dispatch[function_name](**arguments)
            except Exception as e:
                result = f"Error running {function_name}: {e}"

            history.append({"role": "tool", "content": str(result), "name": function_name})

    return "Agenten gav upp efter för många steg utan ett slutgiltigt svar"