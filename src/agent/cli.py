import click
import chromadb
import random 
import threading
import time
import logging
from pathlib import Path
from . import config
from .indexer import build_index
from .retriever import Retriever
from .ollama_client import embed
from .agent_loop import run_agent_loop
from . import tools
from chromadb.config import Settings
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()

PROMPT_WORDS = ["Dance", "Go on vacation", "Fly to Mallorca", "Sing a song", "Dream a little", "It's only life", "Have some coffee"]

MODEL_ALIASES = {
    "7b": "qwen2.5-coder:7b",
    "14b": "qwen2.5-coder:14b",
    "3.8": "qwen3.8:27b-q4_K_M",
}

def _spinner(stop_event, status_holder=None):
    dot_patterns = [".", "..", "..."]
    word = random.choice(PROMPT_WORDS)
    tick = 0

    while not stop_event.is_set():
        dots = dot_patterns[tick%len(dot_patterns)]
        if status_holder is not None and status_holder[0]:
            display = status_holder[0]
        else:
            display = word
        print(f"\r{display}{dots}             ", end="", flush=True)
        tick +=1

        if tick %6 == 0:
            word = random.choice(PROMPT_WORDS)
        time.sleep(0.3)
    print("\r" + " " * 40 +"\r", end="", flush=True)

@click.group()
def main():
    pass

@main.command()
@click.argument("path")
def index(path):
    #1
    project_root = Path(path).resolve()
    #2
    chroma_client = chromadb.PersistentClient(
        path=str(project_root / config.CHROMA_PERSIST_DIR),
        settings=Settings(anonymized_telemetry=False),
    )
    collection_name = project_root.name
    collection = build_index(project_root, chroma_client, collection_name, embed_fn=embed)
    print(f"Indexerade {collection.count()} chunks från {project_root}")
    pass

@main.command()
@click.argument("path")
def chat(path):
    project_root = Path(path).resolve()
    chorma_client = chromadb.PersistentClient(
        path=str(project_root / config.CHROMA_PERSIST_DIR),
        settings=Settings(anonymized_telemetry=False),
    )
    collection = chorma_client.get_collection(project_root.name)
    retriever = Retriever(collection, embed_fn=embed)
    tool_dispatch = {
        "read_file": lambda path: tools.read_file(str(tools.resolve_within_project(path, project_root))) if tools.is_within_project(path, project_root) else f"Error: path is outside the project directory: {path}",
        "grep": lambda pattern, root: tools.grep(pattern, str(tools.resolve_within_project(root, project_root))) if tools.is_within_project(root, project_root) else f"Error: path is outside the project directory: {root}",
        "list_dir": lambda path: tools.list_dir(str(tools.resolve_within_project(path, project_root))) if tools.is_within_project(path, project_root) else f"Error: path is outside the project directory: {path}",
        "search_code": lambda query, top_k: tools.search_code(retriever, query, top_k),
        "find_max_stock": lambda data_path: tools.find_max_stock(str(tools.resolve_within_project(data_path, project_root))) if tools.is_within_project(data_path, project_root) else f"Error: outside project: {data_path}",
    }

    system_prompt = (
        "You are a coding assistant with access to tools that let you explore a real "
        "codebase on disk: search_code (semantic search over indexed code), grep (exact "
        "text search), read_file, and list_dir. When asked about code, functions, or "
        "errors, use these tools to look up the real answer before responding. "
        "IMPORTANT: Once a tool call returns results that answer the question, STOP "
        "calling tools and write your final answer directly using those results. "
        "Do not call the same tool again with the same or similar arguments. "
        "This project also contains a warehouse inventory system: 'lager.dat' is a "
        "fixed-width data file where each line is one article's stock at one "
        "location, and 'lager_copybook.txt' describes the exact field layout "
        "(article number, name, stock quantity, category, location). Whenever "
        "asked about stock, inventory, article numbers, or warehouse locations, "
        "ALWAYS read lager_copybook.txt first to get the field layout, then read "
        "or grep lager.dat to find the relevant line(s) — do not wait to be told "
        "to do this explicitly. An article can appear on multiple lines (one per "
        "location); sum lagerstatus across matching lines when asked for a total. "
        "If asked which article has the most total stock, use the find_max_stock "
        "tool directly instead of reading the whole file yourself."
    )

    history = [{"role": "system", "content": system_prompt}]

    console.print(
        f"[bold cyan]Hi, I'm your local coding agent[/bold cyan] (running {config.CHAT_MODEL}). "
        f"Ask me anything about this project — type 'exit' to quit. "
        f"To switch models, just type 7b, 14b, or 3.8. in the chat."
    )

    logging.basicConfig(
        filename=project_root / "agent.log",
        level=logging.INFO,
        format="%(asctime)s %(message)s"
    )

    while True:
        user_input = console.input("[bold cyan]You:[/bold cyan] ")
        if user_input in ("exit", "quit"):
            break
        if user_input.strip().lower() in MODEL_ALIASES:
            config.CHAT_MODEL = MODEL_ALIASES[user_input.strip().lower()]
            print(f"Changed model to: {config.CHAT_MODEL}")
            continue
        if user_input.strip().lower() == "paste":
            print("Paste your text, then end with a line containing only: END")
            lines = []
            while True:
                line = input()
                if line.strip().upper() == "END":
                    break
                lines.append(line)
            user_input = "\n".join(lines)

        stop_event = threading.Event()
        status_holder = [""]
        spinner_thread = threading.Thread(target=_spinner, args=(stop_event, status_holder))
        spinner_thread.start()

        answer = run_agent_loop(user_input, history, tool_dispatch, status_holder)
        
        stop_event.set()
        spinner_thread.join()
        console.print(Panel(Markdown(answer), title="Agent", border_style="cyan"))