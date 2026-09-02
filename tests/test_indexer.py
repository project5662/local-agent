import time

import chromadb
from agent.indexer import build_index

def fake_embed(text: str) -> list[float]:
    words = set(text.lower().split())
    vocab = ["def", "add", "class", "widget", "hello"]
    return [1.0 if w in words else 0.0 for w in vocab]

def make_counting_embed():
    """Wraps fake_embed and counts how many times it's actually called,
    so tests can assert on skip/re-embed behavior instead of just on
    the resulting collection contents."""
    calls = {"n": 0}

    def counting_embed(text: str) -> list[float]:
        calls["n"] += 1
        return fake_embed(text)

    return counting_embed, calls

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

def test_build_index_skips_unchanged_file_on_second_run(tmp_path):
    (tmp_path / "main.py").write_text("def add(a, b): return a + b")
    client = chromadb.PersistentClient(path=str(tmp_path / ".chroma"))
    embed_fn, calls = make_counting_embed()

    build_index(tmp_path, client, "testproj", embed_fn)
    assert calls["n"] == 1

    build_index(tmp_path, client, "testproj", embed_fn)
    assert calls["n"] == 1

def test_build_index_reembeds_changed_file(tmp_path):
    path = tmp_path / "main.py"
    path.write_text("def add(a, b): return a + b")
    client = chromadb.PersistentClient(path=str(tmp_path / ".chroma"))
    embed_fn, calls = make_counting_embed()

    build_index(tmp_path, client, "testproj", embed_fn)
    assert calls["n"] == 1

    # mtime has (at least) second-level resolution on most filesystems,
    # so we sleep to guarantee the new mtime is actually different.
    time.sleep(1.1)
    path.write_text("class Widget: pass")
    collection = build_index(tmp_path, client, "testproj", embed_fn)
    assert calls["n"] == 2

    stored = collection.get()
    assert len(stored["ids"]) == 1
    assert stored["documents"][0] == "class Widget: pass"

def test_build_index_removes_chunks_for_deleted_file(tmp_path):
    path = tmp_path / "main.py"
    path.write_text("def add(a, b): return a + b")
    client = chromadb.PersistentClient(path=str(tmp_path / ".chroma"))
    embed_fn, _ = make_counting_embed()

    build_index(tmp_path, client, "testproj", embed_fn)
    path.unlink()
    collection = build_index(tmp_path, client, "testproj", embed_fn)

    assert collection.count() == 0
