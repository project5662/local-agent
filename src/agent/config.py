# Modell som används för chatt/tool-calling
CHAT_MODEL = "qwen2.5-coder:7b"

# Modell som används för embeddings (RAG)
EMBED_MODEL = "nomic-embed-text"

# Hur många rader per chunk vid indexering, och hur mycket överlapp mellan chunks.
# 80 rader är satt för att pålitligt hålla sig inom nomic-embed-text:s
# standardkontextfönster (2048 tokens) i Ollama, testat mot hela projektet.
# OBS: chunking.py mäter bara radantal, inte faktisk teckentäthet — en fil med
# få men mycket långa rader (t.ex. tät markdown/kod) kan fortfarande i teorin
# överskrida gränsen även med denna chunk-storlek. 80 gav marginal (värsta
# uppmätta chunk: ~4300 tecken, ca hälften av gränsen) men är ingen garanti.
CHUNK_SIZE_LINES = 80
CHUNK_OVERLAP_LINES = 15

# Hur många chunks Retriever hämtar per fråga som default
DEFAULT_TOP_K = 10

# Mappar som aldrig ska indexeras, oavsett .gitignore.
# "docs" är med eftersom planerings-/specdokumenten där innehåller gammal
# pseudokod som modellen annars kan blanda ihop med den faktiska koden.
DEFAULT_IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".agent_index", "docs"}

# Filändelser som ALDRIG ska indexeras (binärfiler m.m.)
DEFAULT_IGNORE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".so", ".pyc", ".whl", ".bin"}

# Max antal loop-iterationer i agent-loopen innan vi ger upp
MAX_AGENT_ITERATIONS = 6

# Var Chroma sparar sin data på disk (relativt den indexerade projektmappen)
CHROMA_PERSIST_DIR = ".agent_index"


