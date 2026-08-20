import click
import chromadb
import random 
import threading
import time
from pathlib import Path
from . import config
from .indexer import build_index
from .retriever import Retriever
from .ollama_client import embed
from .agent_loop import run_agent_loop
from . import tools

PROMPT_WORDS = ["Sjung en sång", "Dansa en dans", "Fundera inte mer", "Livet löser sig", "Lek ha kul", "En dag ska vi ändå dö", "Lika bra att le", "Jobb kan vi hoppas på", "Res till Mallorca"]

def _spinner(stop_event):
    dot_patterns = [".", "..", "..."]
    word = random.choice(PROMPT_WORDS)
    tick = 0

    while not stop_event.is_set():
        dots = dot_patterns[tick%len(dot_patterns)]
        print(f"\r{word}{dots}             ", end="", flush=True)
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
    chroma_client = chromadb.PersistentClient(path=str(project_root / config.CHROMA_PERSIST_DIR))
    collection_name = project_root.name
    collection = build_index(project_root, chroma_client, collection_name, embed_fn=embed)
    print(f"Indexerade {collection.count()} chunks från {project_root}")
    pass

@main.command()
@click.argument("path")
def chat(path):
    project_root = Path(path).resolve()
    chorma_client = chromadb.PersistentClient(path=str(project_root / config.CHROMA_PERSIST_DIR))
    collection = chorma_client.get_collection(project_root.name)
    retriever = Retriever(collection, embed_fn=embed)
    tool_dispatch = {
        "read_file": lambda path: tools.read_file(path),
        "grep": lambda pattern, root: tools.grep(pattern, root),
        "list_dir": lambda path: tools.list_dir(path),
        "search_code": lambda query, top_k: tools.search_code(retriever, query, top_k),
    }

    system_prompt = (
        "You are a coding assistant with access to tools that let you explore a real "
        "codebase on disk: search_code (semantic search over indexed code), grep (exact "
        "text search), read_file, and list_dir. When asked about code, functions, or "
        "errors, use these tools to look up the real answer before responding. "
        "IMPORTANT: Once a tool call returns results that answer the question, STOP "
        "calling tools and write your final answer directly using those results. "
        "Do not call the same tool again with the same or similar arguments."
    )

    history = [{"role": "system", "content": system_prompt}]
    
    while True:
        user_input = input("Vad fan behöver du hjälp med nu då!? ")
        if user_input in ("exit", "quit"):
            break

        stop_event = threading.Event()
        spinner_thread = threading.Thread(target=_spinner, args=(stop_event,))
        spinner_thread.start()

        answer = run_agent_loop(user_input, history, tool_dispatch)
        
        stop_event.set()
        spinner_thread.join()
        print(answer)