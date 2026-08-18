# Lokal RAG-kodningsagent — Implementationsplan

> **Anpassning från standardmallen:** Ägaren av projektet skriver all implementationskod själv, för att lära sig. Därför innehåller stegen nedan **pseudokod/skelett** (funktionssignaturer + kommentarer om logik) istället för färdig implementation, enligt "Samarbetsläge" i designspecen (`docs/superpowers/specs/2026-08-18-local-coding-agent-design.md`). Testkod är däremot komplett, eftersom testerna är mekanisk verifiering, inte inlärningsmålet.
>
> **Exekvering:** Detta körs INTE via subagent-driven-development eller executing-plans (de förutsätter att en agent skriver den riktiga koden). Vi går igenom uppgifterna en i taget i den här konversationen: jag ger skelett, du skriver, jag granskar.

**Mål:** En Python-CLI som indexerar en godtycklig projektmapp (RAG via Chroma + Ollama-embeddings) och låter dig chatta med en lokal kodmodell som kan läsa/söka i koden och föreslå ändringar.

**Arkitektur:** Se designspecen. Kort: CLI → Agent Loop → Ollama (chat med tool-calling) + Retriever → Chroma. Indexer bygger Chroma-collectionen separat.

**Tech Stack:** Python 3.11+, `ollama` (officiella Python-klienten, pratar med lokala Ollama-servern), `chromadb` (vektordatabas, lokal/persisterad), `click` (CLI), `pytest` (tester).

---

## Filstruktur

```
local_agent/
├── pyproject.toml
├── src/
│   └── agent/
│       ├── __init__.py
│       ├── config.py         # konstanter: modellnamn, chunk-storlek, top_k, ignore-lista
│       ├── chunking.py        # klipper filinnehåll i overlappande chunks
│       ├── filters.py         # avgör om en fil/mapp ska indexeras
│       ├── ollama_client.py   # tunna wrapper-funktioner mot ollama-paketet
│       ├── indexer.py         # går igenom mapp -> chunkar -> embeddar -> sparar i Chroma
│       ├── retriever.py       # fråga -> embedding -> topp-k från Chroma
│       ├── tools.py           # read_file, grep, list_dir, search_code, propose_edit
│       ├── agent_loop.py      # tool-calling-loopen
│       └── cli.py             # `agent index`, `agent chat`
└── tests/
    ├── test_chunking.py
    ├── test_filters.py
    ├── test_tools.py
    ├── test_retriever.py
    └── test_indexer.py
```

---

### Task 0: Projektskelett och verifiera Ollama

**Filer:**
- Create: `pyproject.toml`
- Create: `src/agent/__init__.py`

- [ ] **Steg 1: Verifiera att Ollama körs och modellerna finns**

Kör:
```bash
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text
ollama list
```
Förväntat: båda modellerna listas.

- [ ] **Steg 2: Skapa `pyproject.toml`**

Skriv en `pyproject.toml` med:
- `[project]`: namn `local-agent`, Python-krav `>=3.11`
- Beroenden: `ollama`, `chromadb`, `click`
- Dev-beroenden: `pytest`
- Ett entry point/script `agent = agent.cli:main` (så `agent index ...` går att köra som kommando)

- [ ] **Steg 3: Skapa `src/agent/__init__.py` (tom fil räcker för nu)**

- [ ] **Steg 4: Installera i editable-läge och verifiera**

Kör: `pip install -e ".[dev]"` (lägg till ett `[project.optional-dependencies] dev = ["pytest"]`-block för detta)
Förväntat: installation lyckas utan fel.

- [ ] **Steg 5: Commit**

```bash
git add pyproject.toml src/agent/__init__.py
git commit -m "chore: project scaffolding"
```

---

### Task 1: Config-modul

**Filer:**
- Create: `src/agent/config.py`

- [ ] **Steg 1: Skriv skelettet**

```python
# src/agent/config.py

# Modell som används för chatt/tool-calling
CHAT_MODEL = "qwen2.5-coder:7b"

# Modell som används för embeddings (RAG)
EMBED_MODEL = "nomic-embed-text"

# Hur många rader per chunk vid indexering, och hur mycket överlapp mellan chunks
CHUNK_SIZE_LINES = ...   # t.ex. 300
CHUNK_OVERLAP_LINES = ...  # t.ex. 50

# Hur många chunks Retriever hämtar per fråga som default
DEFAULT_TOP_K = ...  # t.ex. 5

# Mappar/filer som ALDRIG ska indexeras, oavsett .gitignore
DEFAULT_IGNORE_DIRS = {...}  # .git, node_modules, __pycache__, .venv, venv, dist, build
DEFAULT_IGNORE_EXTENSIONS = {...}  # binärfiler: .png, .jpg, .pdf, .zip, .so, .pyc, ...

# Max antal loop-iterationer i agent-loopen innan vi ger upp
MAX_AGENT_ITERATIONS = ...  # t.ex. 6

# Var Chroma sparar sin data på disk
CHROMA_PERSIST_DIR = ...  # t.ex. en dold mapp i användarens hem, eller ".agent_index" relativt indexerad mapp
```

Fyll i värdena själv (kommentarerna ovan ger riktvärden). Ingen logik i den här filen, bara konstanter.

- [ ] **Steg 2: Commit**

```bash
git add src/agent/config.py
git commit -m "feat: add config constants"
```

---

### Task 2: Chunking

**Filer:**
- Create: `src/agent/chunking.py`
- Test: `tests/test_chunking.py`

- [ ] **Steg 1: Skriv testerna**

```python
# tests/test_chunking.py
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
    # Varje chunk innehåller max chunk_size_lines rader
    for c in chunks:
        assert len(c.splitlines()) <= 300
    # Överlappen: sista raderna i chunk 1 ska vara samma som första raderna i chunk 2
    first_chunk_lines = chunks[0].splitlines()
    second_chunk_lines = chunks[1].splitlines()
    assert first_chunk_lines[-50:] == second_chunk_lines[:50]

def test_empty_text_returns_no_chunks():
    assert chunk_text("", chunk_size_lines=300, overlap_lines=50) == []
```

- [ ] **Steg 2: Kör testerna, verifiera att de failar**

Kör: `pytest tests/test_chunking.py -v`
Förväntat: FAIL, `ModuleNotFoundError` eller `ImportError` (funktionen finns inte än).

- [ ] **Steg 3: Skriv skelettet för implementationen**

```python
# src/agent/chunking.py

def chunk_text(text: str, chunk_size_lines: int, overlap_lines: int) -> list[str]:
    """Klipper text i overlappande chunks, radbaserat."""
    # 1. Om text är tom -> returnera []
    # 2. Dela text i rader (text.splitlines())
    # 3. Om antal rader <= chunk_size_lines -> returnera [text] (en enda chunk)
    # 4. Annars: loopa med ett fönster av storlek chunk_size_lines,
    #    stega fram (chunk_size_lines - overlap_lines) rader varje varv,
    #    join:a varje fönster tillbaka till en sträng med "\n".join(...)
    # 5. Sluta när fönstret skulle börja bortom slutet av raderna
    pass
```

Implementera stegen ovan själv.

- [ ] **Steg 4: Kör testerna igen, verifiera att de passerar**

Kör: `pytest tests/test_chunking.py -v`
Förväntat: PASS, alla tre testerna gröna.

- [ ] **Steg 5: Commit**

```bash
git add src/agent/chunking.py tests/test_chunking.py
git commit -m "feat: add line-based chunking with overlap"
```

---

### Task 3: Filfiltrering (vad ska indexeras)

**Filer:**
- Create: `src/agent/filters.py`
- Test: `tests/test_filters.py`

- [ ] **Steg 1: Skriv testerna**

```python
# tests/test_filters.py
from pathlib import Path
from agent.filters import should_index_file

def test_rejects_ignored_directory(tmp_path):
    p = tmp_path / ".git" / "config"
    p.parent.mkdir()
    p.write_text("x")
    assert should_index_file(p, tmp_path) is False

def test_rejects_binary_extension(tmp_path):
    p = tmp_path / "logo.png"
    p.write_bytes(b"\x89PNG")
    assert should_index_file(p, tmp_path) is False

def test_accepts_python_file(tmp_path):
    p = tmp_path / "main.py"
    p.write_text("print('hi')")
    assert should_index_file(p, tmp_path) is True

def test_rejects_gitignored_file(tmp_path):
    (tmp_path / ".gitignore").write_text("secret.txt\n")
    p = tmp_path / "secret.txt"
    p.write_text("shh")
    assert should_index_file(p, tmp_path) is False
```

- [ ] **Steg 2: Kör testerna, verifiera att de failar**

Kör: `pytest tests/test_filters.py -v`
Förväntat: FAIL (funktionen finns inte än).

- [ ] **Steg 3: Skriv skelettet**

```python
# src/agent/filters.py

def should_index_file(path, project_root) -> bool:
    """Avgör om en fil ska indexeras."""
    # 1. Om någon del av path (relativt project_root) matchar
    #    config.DEFAULT_IGNORE_DIRS -> False
    # 2. Om path.suffix finns i config.DEFAULT_IGNORE_EXTENSIONS -> False
    # 3. Om path matchar ett mönster i project_root/.gitignore -> False
    #    (för v1 räcker enkel exact-match/rad-för-rad-jämförelse,
    #     ingen fullständig gitignore-glob-motor)
    # 4. Annars -> True
    pass
```

Implementera. Tips: `.gitignore`-hantering kan vara mycket enkel i v1 (exakta filnamn, inga wildcards) — det är en medveten YAGNI-avgränsning, inte ett krav på fullständig gitignore-spec.

- [ ] **Steg 4: Kör testerna igen, verifiera att de passerar**

Kör: `pytest tests/test_filters.py -v`
Förväntat: PASS.

- [ ] **Steg 5: Commit**

```bash
git add src/agent/filters.py tests/test_filters.py
git commit -m "feat: add file filtering for indexing"
```

---

### Task 4: Ollama-klient (tunn wrapper)

**Filer:**
- Create: `src/agent/ollama_client.py`

Ingen automatiserad test här — den här modulen pratar med en riktig lokal server, så vi verifierar den manuellt (integrationstest, inte enhetstest). Det är en medveten avgränsning: att mocka bort Ollama helt hade gett falsk trygghet utan att testa det som faktiskt kan gå fel (modell saknas, server nere, fel svarsformat).

- [ ] **Steg 1: Skriv skelettet**

```python
# src/agent/ollama_client.py
import ollama
from . import config

def embed(text: str) -> list[float]:
    """Skickar text till embedding-modellen, returnerar embedding-vektorn."""
    # Använd ollama.embeddings(model=config.EMBED_MODEL, prompt=text)
    # Returnera response["embedding"]
    pass

def chat(messages: list[dict], tools: list[dict] | None = None) -> dict:
    """Skickar en konversation till chatt-modellen, med ev. tool-definitioner.
    Returnerar hela response["message"] (kan innehålla "content" och/eller "tool_calls")."""
    # Använd ollama.chat(model=config.CHAT_MODEL, messages=messages, tools=tools)
    # Returnera response["message"]
    pass
```

- [ ] **Steg 2: Manuell verifiering av `embed`**

Kör i en Python-shell:
```python
from agent.ollama_client import embed
vec = embed("def add(a, b): return a + b")
print(len(vec), vec[:5])
```
Förväntat: en lista med flera hundra flyttal (nomic-embed-text ger 768-dimensionella vektorer).

- [ ] **Steg 3: Manuell verifiering av `chat`**

```python
from agent.ollama_client import chat
msg = chat([{"role": "user", "content": "Say hello in one word."}])
print(msg)
```
Förväntat: ett dict med `"content"` som innehåller ett hälsningsord.

- [ ] **Steg 4: Commit**

```bash
git add src/agent/ollama_client.py
git commit -m "feat: add thin ollama client wrapper"
```

---

### Task 5: Retriever

**Filer:**
- Create: `src/agent/retriever.py`
- Test: `tests/test_retriever.py`

**Designval för testbarhet:** `Retriever` tar en Chroma-collection och en `embed_fn` som konstruktorargument (dependency injection), så testerna kan skicka in en påhittad, deterministisk embedding-funktion istället för att anropa den riktiga Ollama-servern. Det gör testet snabbt och stabilt.

- [ ] **Steg 1: Skriv testerna**

```python
# tests/test_retriever.py
import chromadb
from agent.retriever import Retriever

def fake_embed(text: str) -> list[float]:
    # Deterministisk låtsas-embedding: en dimension per unikt ord i texten,
    # räcker för att testa att "lika text ger lika vektor, olika text ger olika vektor"
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
```

- [ ] **Steg 2: Kör testet, verifiera att det failar**

Kör: `pytest tests/test_retriever.py -v`
Förväntat: FAIL (klassen finns inte än).

- [ ] **Steg 3: Skriv skelettet**

```python
# src/agent/retriever.py

class Retriever:
    def __init__(self, collection, embed_fn):
        # spara collection och embed_fn som instansattribut
        pass

    def search(self, query: str, top_k: int) -> list[dict]:
        """Embeddar query, frågar Chroma-collectionen, returnerar en lista av
        {"document": ..., "metadata": ..., "distance": ...} för de top_k mest lika chunks."""
        # 1. query_vec = self.embed_fn(query)
        # 2. results = self.collection.query(query_embeddings=[query_vec], n_results=top_k)
        # 3. Chroma returnerar parallella listor (documents, metadatas, distances) under
        #    nycklar som är listor-av-listor (en lista per query). Packa ihop dem till
        #    en lista av dicts, ett dict per resultat.
        pass
```

- [ ] **Steg 4: Kör testet igen, verifiera att det passerar**

Kör: `pytest tests/test_retriever.py -v`
Förväntat: PASS.

- [ ] **Steg 5: Commit**

```bash
git add src/agent/retriever.py tests/test_retriever.py
git commit -m "feat: add Retriever with injectable embedding function"
```

---

### Task 6: Indexer

**Filer:**
- Create: `src/agent/indexer.py`
- Test: `tests/test_indexer.py`

- [ ] **Steg 1: Skriv testerna**

```python
# tests/test_indexer.py
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
```

- [ ] **Steg 2: Kör testet, verifiera att det failar**

Kör: `pytest tests/test_indexer.py -v`
Förväntat: FAIL.

- [ ] **Steg 3: Skriv skelettet**

```python
# src/agent/indexer.py
from pathlib import Path
from . import config
from .chunking import chunk_text
from .filters import should_index_file

def build_index(project_root, chroma_client, collection_name, embed_fn):
    """Går igenom project_root, chunkar godkända filer, embeddar varje chunk,
    lagrar allt i en (om-skapad) Chroma-collection. Returnerar collection-objektet."""
    # 1. Ta bort ev. existerande collection med samma namn (om den finns) och
    #    skapa en ny — v1 bygger alltid om från scratch.
    # 2. Gå igenom alla filer under project_root (Path.rglob("*") + is_file())
    # 3. Filtrera med should_index_file(path, project_root); hoppa över de som inte klarar
    # 4. Läs filens innehåll (försök läsa som text; om det failar med UnicodeDecodeError,
    #    logga en varning och hoppa över filen — se "Felhantering" i designspecen)
    # 5. Chunka innehållet med chunk_text(...) och config.CHUNK_SIZE_LINES/CHUNK_OVERLAP_LINES
    # 6. För varje chunk: embedda den med embed_fn, samla ihop id (t.ex. f"{path}:{i}"),
    #    embedding, metadata ({"path": relativ sökväg som sträng}), och document (chunk-texten)
    # 7. Lägg till alla chunks i collectionen med collection.add(ids=..., embeddings=...,
    #    metadatas=..., documents=...)
    # 8. Returnera collectionen
    pass
```

- [ ] **Steg 4: Kör testet igen, verifiera att det passerar**

Kör: `pytest tests/test_indexer.py -v`
Förväntat: PASS.

- [ ] **Steg 5: Commit**

```bash
git add src/agent/indexer.py tests/test_indexer.py
git commit -m "feat: add indexer that walks, chunks, embeds, and stores a project"
```

---

### Task 7: Tools

**Filer:**
- Create: `src/agent/tools.py`
- Test: `tests/test_tools.py`

- [ ] **Steg 1: Skriv testerna**

```python
# tests/test_tools.py
from agent.tools import read_file, grep, list_dir

def test_read_file_returns_content(tmp_path):
    p = tmp_path / "a.py"
    p.write_text("line1\nline2\n")
    assert read_file(str(p)) == "line1\nline2\n"

def test_read_file_missing_file_returns_error_string(tmp_path):
    result = read_file(str(tmp_path / "missing.py"))
    assert "not found" in result.lower() or "error" in result.lower()

def test_grep_finds_matching_lines(tmp_path):
    (tmp_path / "a.py").write_text("def add(): pass\ndef sub(): pass\n")
    (tmp_path / "b.py").write_text("class Widget: pass\n")
    results = grep("def ", str(tmp_path))
    assert any("a.py" in r and "def add" in r for r in results)
    assert not any("b.py" in r for r in results)

def test_list_dir_lists_entries(tmp_path):
    (tmp_path / "a.py").write_text("x")
    (tmp_path / "sub").mkdir()
    entries = list_dir(str(tmp_path))
    assert "a.py" in entries
    assert "sub" in entries
```

- [ ] **Steg 2: Kör testerna, verifiera att de failar**

Kör: `pytest tests/test_tools.py -v`
Förväntat: FAIL.

- [ ] **Steg 3: Skriv skelettet**

```python
# src/agent/tools.py
from pathlib import Path

def read_file(path: str) -> str:
    """Läser och returnerar hela filens innehåll som text.
    Vid fel (fil saknas, ej läsbar): returnera ett beskrivande felmeddelande
    som sträng istället för att kasta ett exception — verktygsresultat matas
    tillbaka till modellen som text, den ska kunna reagera på ett fel."""
    pass

def grep(pattern: str, root: str) -> list[str]:
    """Söker efter `pattern` (enkel substr-match, inte regex i v1) i alla filer
    under `root`. Returnerar en lista av strängar i formatet
    "<relativ_path>:<radnummer>: <radinnehåll>" för varje match."""
    # Tips: gå igenom filer med Path(root).rglob("*"), hoppa över samma
    # ignore-lista som filters.py (återanvänd should_index_file om det passar,
    # annars en enklare variant här)
    pass

def list_dir(path: str) -> list[str]:
    """Returnerar namnen (inte fullständiga sökvägar) på alla filer och
    mappar direkt under `path` (inte rekursivt)."""
    pass

def search_code(retriever, query: str, top_k: int) -> list[dict]:
    """Tunn wrapper: anropar retriever.search(query, top_k) och returnerar
    resultatet. Finns som egen funktion så den kan exponeras som ett separat
    named tool för modellen, skiljt från grep/read_file."""
    pass

def propose_edit(path: str, explanation: str, diff: str) -> str:
    """Skriver INTE till disk. Formaterar bara ett läsbart textblock som visar
    vilken fil som föreslås ändras, varför, och den föreslagna diffen — detta
    är vad som visas för användaren i CLI:et. Returnerar den formaterade strängen."""
    pass
```

- [ ] **Steg 4: Kör testerna igen, verifiera att de passerar**

Kör: `pytest tests/test_tools.py -v`
Förväntat: PASS (obs: testerna ovan täcker inte `search_code`/`propose_edit` eftersom de kräver en riktig retriever/inget att asserta på — verifiera dem manuellt i Task 9:s end-to-end-test istället).

- [ ] **Steg 5: Commit**

```bash
git add src/agent/tools.py tests/test_tools.py
git commit -m "feat: add read-only agent tools"
```

---

### Task 8: Agent Loop

**Filer:**
- Create: `src/agent/agent_loop.py`

Ingen automatiserad test av själva LLM-resonemanget (modellsvar varierar, se designspecen). Vi verifierar loopens *mekanik* (att den stannar, att verktyg anropas och matas tillbaka korrekt) manuellt i Task 9.

- [ ] **Steg 1: Skriv skelettet**

```python
# src/agent/agent_loop.py
from . import config
from .ollama_client import chat

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the full contents of a file at the given path.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    # Lägg till resten (grep, list_dir, search_code) med samma struktur.
    # Titta på tools.py-signaturerna för att veta vilka "properties" varje
    # verktyg behöver.
]

def run_agent_loop(user_message: str, history: list[dict], tool_dispatch: dict) -> str:
    """Kör tool-calling-loopen tills modellen ger ett slutgiltigt svar utan
    fler verktygsanrop, eller tills config.MAX_AGENT_ITERATIONS nås.

    - history: mutabel lista av {"role": ..., "content": ...}-meddelanden,
      byggs på i denna funktion (både med user_message och alla mellansteg).
    - tool_dispatch: dict som mappar verktygsnamn (str) -> callable som tar
      **kwargs och returnerar en sträng, t.ex. {"read_file": tools.read_file, ...}
    """
    # 1. Lägg till {"role": "user", "content": user_message} i history
    # 2. Loopa upp till config.MAX_AGENT_ITERATIONS gånger:
    #      a. message = chat(history, tools=TOOL_SCHEMAS)
    #      b. Lägg till message i history
    #      c. Om message inte har "tool_calls" (eller den är tom):
    #             returnera message["content"]  # klart svar
    #      d. Annars, för varje tool_call i message["tool_calls"]:
    #             hämta funktionsnamn och argument från tool_call["function"]
    #             slå upp funktionen i tool_dispatch, kalla den med argumenten
    #             lägg till ett {"role": "tool", "content": <resultat som sträng>,
    #                            "name": <funktionsnamn>} i history
    #      e. (loopen fortsätter till nästa iteration)
    # 3. Om loopen tar slut utan slutgiltigt svar: returnera ett meddelande
    #    som säger att agenten gav upp efter för många steg.
    pass
```

- [ ] **Steg 2: Commit**

```bash
git add src/agent/agent_loop.py
git commit -m "feat: add tool-calling agent loop"
```

---

### Task 9: CLI och end-to-end-verifiering

**Filer:**
- Create: `src/agent/cli.py`

- [ ] **Steg 1: Skriv skelettet**

```python
# src/agent/cli.py
import click
import chromadb
from pathlib import Path
from . import config
from .indexer import build_index
from .retriever import Retriever
from .ollama_client import embed
from .agent_loop import run_agent_loop
from . import tools

@click.group()
def main():
    pass

@main.command()
@click.argument("path")
def index(path):
    """Bygg RAG-index för en projektmapp."""
    # 1. project_root = Path(path).resolve()
    # 2. chroma_client = chromadb.PersistentClient(path=str(project_root / ".agent_index"))
    # 3. collection_name = project_root.name (sanera ev. otillåtna tecken)
    # 4. build_index(project_root, chroma_client, collection_name, embed_fn=embed)
    # 5. Skriv ut ett bekräftelsemeddelande med antal chunks (collection.count())
    pass

@main.command()
@click.argument("path")
def chat(path):
    """Starta en REPL-chattsession mot en tidigare indexerad mapp."""
    # 1. Öppna samma Chroma-collection som `index` skapade för denna path
    #    (samma persist-path och collection_name-logik som ovan)
    # 2. Bygg en Retriever(collection, embed_fn=embed)
    # 3. Bygg tool_dispatch-dicten: mappa "read_file" -> tools.read_file,
    #    "grep" -> en lambda som anropar tools.grep(pattern, root=path),
    #    "list_dir" -> en lambda mot tools.list_dir,
    #    "search_code" -> en lambda som anropar tools.search_code(retriever, ...)
    # 4. history = []  (tom konversation att börja med)
    # 5. Loopa: läs en rad input från användaren (input(">>> ")),
    #    avsluta loopen vid t.ex. "exit"/"quit",
    #    annars: svar = run_agent_loop(user_input, history, tool_dispatch);
    #    skriv ut svar
    pass

if __name__ == "__main__":
    main()
```

- [ ] **Steg 2: End-to-end manuell verifiering**

```bash
agent index .
agent chat .
```
I chattsessionen, testa t.ex.: "Vilka filer finns i detta projekt?" och "Förklara vad chunk_text-funktionen gör."
Förväntat: agenten anropar `list_dir`/`search_code`/`read_file` (synligt om du loggar tool-calls, valfritt att lägga till en `print` för det under utveckling) och ger ett svar baserat på den riktiga koden i mappen, inte gissningar.

- [ ] **Steg 3: Commit**

```bash
git add src/agent/cli.py
git commit -m "feat: add CLI with index and chat commands"
```

---

## Självgranskning

- **Speccheckning:** Indexer (spec: Indexer) ✓ Task 6, Retriever ✓ Task 5, Tools (read-only, spec: Tools) ✓ Task 7, Agent Loop ✓ Task 8, CLI (`agent index`/`agent chat`) ✓ Task 9, Felhantering (spec: tydliga felmeddelanden, hoppa över oläsbara filer) ✓ täckt i Task 6/7 pseudokodkommentarer, Testning (spec: pytest för deterministiska delar, ingen exact-match på LLM-svar) ✓ matchar Task 2/3/5/6/7 (pytest) och Task 8/9 (manuell verifiering).
- **Placeholder-scan:** Inga "TBD"/"fyll i senare" kvar — de enda "ofullständiga" bitarna är de avsiktliga pseudokod-kommentarerna i implementationsstegen, vilket är den överenskomna metoden, inte en plan-brist.
- **Typkonsistens:** `Retriever.search(query, top_k)` (Task 5) matchar hur den anropas i `tools.search_code` (Task 7) och i CLI:ets `chat`-kommando (Task 9). `tool_dispatch`-mönstret i Task 8 matchar hur det byggs upp i Task 9.
