from pathlib import Path

def read_file(path: str):
    try:
        return Path(path).read_text()
    except Exception:
        return f"Error: file not found {path}"

def find_max_stock(data_path: str):
    try:
        with open(data_path) as f:
            totals = {}
            for row in f:
                art_number = row[0:10].strip()
                stock = int(row[45:51])
                totals[art_number] = totals.get(art_number, 0) + stock
            best_article = max(totals, key=totals.get)
            return f"{best_article} med totalt {totals[best_article]} st över alla lagerplatser"
    except Exception:
        return f"Error: could not open file {data_path}"



def resolve_within_project(path_str, project_root):
    p = Path(path_str)
    if p.is_absolute():
        pass
    else:
        p = project_root/p 
    return p



def is_within_project(path_str, project_root):
    try:
        resolved = resolve_within_project(path_str, project_root).resolve()
        return resolved.is_relative_to(project_root.resolve())
    except Exception:
        return False
    

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


