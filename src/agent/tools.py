from pathlib import Path

def read_file(path: str):
    try:
        return Path(path).read_text()
    except Exception:
        return f"Error: file not found {path}"
    

def grep(pattern: str, root: str):
    #1
    matches = []
    #2
    for path in Path(root).rglob("*"):
        if not path.is_file():
            continue

        try:
            lines = path.read_text().splitlines()
        except UnicodeDecodeError:
            continue
        
        for line_number, line in enumerate(lines, start=1):
            if pattern in line:
                matches.append(f"{path}:{line_number}: {line}")

    return matches

def list_dir(path: str):
    file_name = [item.name for item in Path(path).iterdir()]
    return file_name

def search_code(retriever, query: str, top_k: int):
    return retriever.search(query, top_k)

def propose_edit(path: str, explanation: str, diff: str):
    return f"Proposed edit to {path}:\n{explanation}\n\n{diff}"
