import ast

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

def chunk_python_code(text: str) -> list[str] | None:
  
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None

    rows = text.splitlines()

    
    chunks = []

    for node in tree.body:
      
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = node.lineno - 1
            end = node.end_lineno
            chunk_lines = rows[start:end]
            # En enskild funktion/klass kan i sig vara för stor för
            # embedding-modellens kontextgräns (hände på riktigt med en
            # 7700-tecken chat()-funktion). Falla då tillbaka på den
            # radbaserade chunkningen för just den här funktionen, istället
            # för att alltid skicka in den som en enda chunk.
            if len(chunk_lines) > 80:
                chunks.extend(chunk_text("\n".join(chunk_lines), 80, 15))
            else:
                chunks.append("\n".join(chunk_lines))
    
    return chunks
