from . import config
from .ollama_client import chat

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
        message = chat(history, tools=TOOL_SCHEMAS)
        history.append({"role": "assistant", "content": message.content, "tool_calls": message.tool_calls})

        if not message.tool_calls:
            return message.content

        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            arguments = tool_call.function.arguments
            result = tool_dispatch[function_name](**arguments)
            history.append({"role": "tool", "content": str(result), "name": function_name})

    return "Agenten gav upp efter för många steg utan ett slutgiltigt svar"