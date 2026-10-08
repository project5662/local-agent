# Diary

## Purpose of the project
I wanted to learn how to build a local AI agent that uses a RAG pipeline to work against specific files. In this case, a simulated warehouse.

I downloaded various Qwen model weights (GGUF format) via Ollama, and the model runs through the Ollama app.

Next was building the RAG pipeline, where external libraries handle embedding (nomic-embed-text) and vector search / cosine similarity (ChromaDB). I built the chunking of the files myself as Python functions, and tested different configurations until the results became reasonable. The results became reasonable once the answers were actually grounded in real facts from the files being indexed and searched.

Chunking and searching alone wasn't enough to get grounded answers, though. It also took a fair amount of system-prompt work: I knew what kind of answers I wanted, and used that to tweak, add, or remove instructions. I also added keywords the agent can recognize in the user's question (e.g. "lager"/"warehouse"), which route it to the right tools.

I also needed to build my own tools so the agent could handle specific tasks, such as calculating different stock balances.

So that the agent could remember what a user had written earlier in a chat, I built session IDs: a dict where the conversation's context is stored, so the agent can retrieve it from there. The dict is cleared whenever the chat is closed and a new session starts.

I also added Docker containerization, so the whole project could be shipped to, for example, a company that wants to run my AI assistant themselves.

Debugging was done by following terminal logs in real time while a chat was running, to catch whether the agent used the right tool at the right time (via Python's built-in `logging` library).

Finally, I built two different UIs: one terminal-based and one web-based.
