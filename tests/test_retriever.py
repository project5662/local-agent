import chromadb
from agent.retriever import Retriever

def fake_embed(text: str) -> list[float]:
    words = set(text.lower().split())
    vocab = ["def", "add", "subtract", "class", "widget"]
    return [1.0 if w in words else 0.0 for w in vocab]

def test_retriever_returns_most_similar_chunk(tmp_path):
    client = chromadb.PersistentClient(path=str(tmp_path))
    collection = client.create_collection("test")
    collection.add(
        ids=["1", "2"],
        embeddings=[fake_embed("def add(a, b): return a + b"), fake_embed("class Widget: pass")],
        metadatas=[{"path": "math.py"}, {"path": "ui.py"}],
        documents=["def add(a, b): return a + b", "class Widget: pass"],
    )
    retriever = Retriever(collection=collection, embed_fn=fake_embed)
    results = retriever.search("def add function", top_k=1)
    assert len(results) == 1
    assert results[0]["metadata"]["path"] == "math.py"
