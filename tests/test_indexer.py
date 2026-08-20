import chromadb
from agent.indexer import build_index

def fake_embed(text: str) -> list[float]:
    words = set(text.lower().split())
    vocab = ["def", "add", "class", "widget", "hello"]
    return [1.0 if w in words else 0.0 for w in vocab]

def test_build_index_skips_ignored_files_and_stores_rest(tmp_path):
    (tmp_path / "main.py").write_text("def add(a, b): return a + b")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("ignore me")

    client = chromadb.PersistentClient(path=str(tmp_path / ".chroma"))
    collection = build_index(
        project_root=tmp_path,
        chroma_client=client,
        collection_name="testproj",
        embed_fn=fake_embed,
    )

    stored = collection.get()
    paths = [m["path"] for m in stored["metadatas"]]
    assert any("main.py" in p for p in paths)
    assert not any(".git" in p for p in paths)
