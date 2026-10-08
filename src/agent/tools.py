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

def find_min_stock(data_path: str, location: str = None):
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

            min_article = min(totals, key=totals.get)
            if location is not None:
                return f"{min_article} med totalt {totals[min_article]} st i {location}"
            return f"{min_article} med totalt {totals[min_article]} st över alla lagerplatser"
    except Exception:
        return f"Error: could not open file {data_path}"

def list_stock_by_location(data_path: str, artikelnummer: str):
    try:
        with open(data_path) as f:
            results = []
            article_name = None
            for row in f:
                row_art_number = row[0:10].strip()
                if row_art_number.lower() != artikelnummer.lower():
                    continue
                if article_name is None:
                    article_name = row[10:45].strip()
                row_location = row[66:81].strip()
                stock = int(row[45:51])
                results.append(f"- {row_location}: {stock} st")

            if not results:
                return f"Error: article {artikelnummer} not found"

            return f"Artikel: {artikelnummer} {article_name}\n" + "\n".join(results)
    except Exception:
        return f"Error: could not open file {data_path}"

def list_locations(data_path: str):
    try:
        with open(data_path) as f:
            locations = set()
            for row in f:
                locations.add(row[66:81].strip())
            return "\n".join(f"- {loc}" for loc in sorted(locations))
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

def stock_totals_by_location(data_path: str):
    totals_per_location = {}
    with open(data_path) as f:
        for row in f:
            location = row[66:81].strip()
            stock = int(row[45:51])
            totals_per_location[location] = totals_per_location.get(location, 0) + stock
    return totals_per_location

def stock_distribution_chart(data_path: str):
    try:
        with open(data_path) as f:
            totals_per_location = {}
            for row in f:
                location = row[66:81].strip()
                stock = int(row[45:51])
                totals_per_location[location] = totals_per_location.get(location, 0) + stock

        if not totals_per_location:
            return f"Error: no stock data found in {data_path}"

        max_stock = max(totals_per_location.values())
        max_bar_width = 30

        rows = [
            "Totalt lagersaldo per ort (summa av alla artiklars antal, st)",
            "Total stock per location (sum of all articles' units)",
            "",
        ]
        for location, total in sorted(totals_per_location.items(), key=lambda item: item[1], reverse=True):
            bar_length = int((total / max_stock) * max_bar_width) if max_stock > 0 else 0
            bar = "█" * bar_length
            rows.append(f"{location:15} {bar} {total} st")

        return "```\n" + "\n".join(rows) + "\n```"
    except Exception:
        return f"Error: could not open file {data_path}"