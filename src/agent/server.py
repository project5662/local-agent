import logging
import os

import chromadb
from chromadb.config import Settings

from .ollama_client import embed
from .retriever import Retriever

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import config
from .agent_loop import run_agent_loop
from . import tools
from .cli import build_tools_for_message, build_tool_dispatch, SYSTEM_PROMPT, MODEL_ALIASES

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

app = FastAPI()
sessions = {}

PROJECT_ROOT = Path(__file__).resolve().parents[2]

client = chromadb.PersistentClient(
    path=str(PROJECT_ROOT / config.CHROMA_PERSIST_DIR),
    settings=Settings(anonymized_telemetry=False),
)
collection_name = os.environ.get("AGENT_COLLECTION_NAME", PROJECT_ROOT.name)
collection = client.get_collection(collection_name)
retriever = Retriever(collection, embed_fn=embed)
tool_dispatch = build_tool_dispatch(PROJECT_ROOT, retriever)

class AskRequest(BaseModel):
    question: str
    session_id: str
    model: str = "7b"

@app.get("/")
def index_page():
    return FileResponse(PROJECT_ROOT / "web" / "index.html")

@app.get("/chart/stock-by-location")
def stock_by_location_chart():
    totals = tools.stock_totals_by_location(str(PROJECT_ROOT / "lager.dat"))
    locations = [{"location": loc, "total": total} for loc, total in sorted(totals.items(), key=lambda item: item[1], reverse=True)]
    return {"locations": locations}

@app.get("/health")
def health():
    return {"Status": "ok"}

@app.post("/ask")
def ask(req: AskRequest):
    if req.model in MODEL_ALIASES:
        config.CHAT_MODEL = MODEL_ALIASES[req.model]

    tools = build_tools_for_message(req.question)

    if req.session_id not in sessions:
        sessions[req.session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    history = sessions[req.session_id]

    answer = run_agent_loop(req.question, history, tool_dispatch, tools=tools)

    return {"answer": answer}
