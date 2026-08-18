# Modell som används för chatt/tool-calling
CHAT_MODEL = "qwen2.5-coder:7b"

# Modell som används för embeddings (RAG)
EMBED_MODEL = "nomic-embed-text"

# Hur många rader per chunk vid indexering, och hur mycket överlapp mellan chunks
CHUNK_SIZE_LINES = 300
CHUNK_OVERLAP_LINES = 50

# Hur många chunks Retriever hämtar per fråga som default
DEFAULT_TOP_K = 5

# Mappar som aldrig ska indexeras, oavsett .gitignore
DEFAULT_IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".agent_index"}

# Filändelser som ALDRIG ska indexeras (binärfiler m.m.)
DEFAULT_IGNORE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".so", ".pyc", ".whl", ".bin"}

# Max antal loop-iterationer i agent-loopen innan vi ger upp
MAX_AGENT_ITERATIONS = 6

# Var Chroma sparar sin data på disk (relativt den indexerade projektmappen)
CHROMA_PERSIST_DIR = ".agent_index"


