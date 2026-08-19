from agent.chunking import chunk_text

def test_short_text_becomes_one_chunk():
    text = "\n".join(f"line {i}" for i in range(10))
    chunks = chunk_text(text, chunk_size_lines=300, overlap_lines=50)
    assert len(chunks) == 1
    assert chunks[0] == text

def test_long_text_splits_into_multiple_overlapping_chunks():
    lines = [f"line {i}" for i in range(700)]
    text = "\n".join(lines)
    chunks = chunk_text(text, chunk_size_lines=300, overlap_lines=50)
    assert len(chunks) == 3
    for c in chunks:
        assert len(c.splitlines()) <= 300
    first_chunk_lines = chunks[0].splitlines()
    second_chunk_lines = chunks[1].splitlines()
    assert first_chunk_lines[-50:] == second_chunk_lines[:50]

def test_empty_text_returns_no_chunks():
    assert chunk_text("", chunk_size_lines=300, overlap_lines=50) == []


