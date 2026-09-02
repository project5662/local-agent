from pathlib import Path
from . import config

def read_file(path: str):
    try:
        # st_size är bytes, inte tecken - med å/ä/ö (multi-byte i UTF-8)
        # blir det inte exakt samma som teckenantal, men nära nog för syftet
        # här: att stoppa modellen från att av misstag svälja hela stora
        # datafiler (t.ex. lager.dat) och spränga kontextfönstret.
        size = Path(path).stat().st_size
        if size > config.MAX_READ_FILE_CHARS:
            return f"Error: file too large to read in full ({size} bytes). Use grep or search_code instead."
        return Path(path).read_text()
    except Exception:
        return f"Error: file not found {path}"

def find_max_stock(data_path: str, location: str = None):
    try:
        with open(data_path) as f:
            totals = {}
            for row in f:
                row_location = row[66:81].strip()
                if location is not None and row_location.lower() != location.lower():
                    continue
                art_number = row[0:10].strip()
                stock = int(row[45:51])
                totals[art_number] = totals.get(art_number, 0) + stock

            if not totals:
                return f"Error: no stock data found for location {location}"

            best_article = max(totals, key=totals.get)
            if location is not None:
                return f"{best_article} med totalt {totals[best_article]} st i {location}"
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

        # Hoppa över filer i ignorerade mappar (.venv, .git, osv) - annars
        # kan grep dra igenom tiotusentals paketfiler i onödan och drunkna
        # i irrelevanta träffar.
        if any(part in config.DEFAULT_IGNORE_DIRS for part in path.parts):
            continue

        try:
            lines = path.read_text().splitlines()
        except UnicodeDecodeError:
            continue

        for line_number, line in enumerate(lines, start=1):
            if pattern in line:
                matches.append(f"{path}:{line_number}: {line}")
                if len(matches) >= config.MAX_GREP_MATCHES:
                    matches.append(
                        f"... truncated at {config.MAX_GREP_MATCHES} matches, refine your search"
                    )
                    return matches

    return matches

def list_dir(path: str):
    file_name = [item.name for item in Path(path).iterdir()]
    return file_name

def search_code(retriever, query: str, top_k: int):
    return retriever.search(query, top_k)

def propose_edit(path: str, explanation: str, diff: str):
    return f"Proposed edit to {path}:\n{explanation}\n\n{diff}"


