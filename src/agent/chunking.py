def chunk_text(text: str, chunk_size_lines: int, overlap_lines: int):
    #1
    if len(text) == 0:
        return []
    #2
    rows = text.splitlines()

    #3
    if len(rows) <= chunk_size_lines:
        return [text]

    #4
    chunks = []
    step = chunk_size_lines - overlap_lines
    start = 0

    while start < len(rows):
        window = rows[start: start + chunk_size_lines]
        chunk = "\n".join(window)
        chunks.append(chunk)
        start += step
    return chunks


