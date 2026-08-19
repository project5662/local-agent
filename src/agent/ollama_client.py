import ollama
from . import config

def embed(text: str):
    response = ollama.embeddings(model=config.EMBED_MODEL, prompt=text)
    return response["embedding"]

def chat(messages: list[dict], tools: list[dict] | None=None):
    response = ollama.chat(model=config.CHAT_MODEL, messages=messages, tools=tools)
    return response["message"]
