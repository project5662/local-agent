# Köra agenten / Running the agent

## Lokalt / Locally (snabbast för utveckling / fastest for development)

**Svenska:** Förutsättning: Ollama är igång (öppna Ollama-appen, eller `ollama serve`).

**English:** Requirement: Ollama is running (open the Ollama app, or run `ollama serve`).

```
agentlocal          # startar chatten mot projektet / starts the chat against the project
agentlog            # följer agent.log i realtid / follows agent.log live (in a second terminal window)
```

**Svenska:** Byt modell i chatten: skriv `7b`, `14b` eller `3.8`. Avsluta: `exit`.

**English:** Switch model in the chat: type `7b`, `14b` or `3.8`. Quit: `exit`.

## Webb-UI / Web UI (chatt i webbläsaren, med diagram och modellval / browser chat, with chart and model picker)

**Svenska:** Förutsättning: Ollama är igång, samma som ovan.

**English:** Requirement: Ollama is running, same as above.

```
cd /path/to/local_agent
source .venv/bin/activate
uvicorn agent.server:app --port 8000 --reload
```

**Svenska:** Öppna sedan `http://localhost:8000` i webbläsaren. `--reload` startar om servern automatiskt när du ändrar kod.

**English:** Then open `http://localhost:8000` in the browser. `--reload` restarts the server automatically when you change code.

## I Docker / In Docker (samma agent, containeriserad / same agent, containerized)

**Svenska:** Förutsättning: Docker Desktop är igång (ikonen i menyraden ska sluta animera).

**English:** Requirement: Docker Desktop is running (the menu bar icon should stop animating).

```
docker compose build             # efter varje kodändring / after every code change
docker compose run --rm agent    # startar chatten, containern städas bort vid exit / starts the chat, container is removed on exit
```

**Svenska:** Stoppa en hängd session: `Ctrl+C`, eller `docker ps` och sedan `docker stop <container-id>`.

**English:** Stop a hung session: `Ctrl+C`, or `docker ps` followed by `docker stop <container-id>`.

## Kom ihåg / Remember

- **Svenska:** Har du ändrat kod i `src/`: kör `agent index /path/to/local_agent` innan du testar, annars använder agenten gamla kodsnuttar.
  **English:** If you changed code in `src/`: run `agent index /path/to/local_agent` before testing, otherwise the agent uses old code snippets.
- **Svenska:** Har du ändrat kod och kör i Docker: kör `docker compose build` först.
  **English:** If you changed code and run in Docker: run `docker compose build` first.
- **Svenska:** Har du lagt till en ny fil som ska vara sökbar: kör `agent index` igen.
  **English:** If you added a new file that should be searchable: run `agent index` again.

## Felsökning / Troubleshooting

- `Cannot connect to the Docker daemon`
  - **Svenska:** Docker Desktop är inte startad.
  - **English:** Docker Desktop is not started.
- `Collection [...] does not exist`
  - **Svenska:** Indexet saknas, kör `agent index <projektmapp>`.
  - **English:** The index is missing, run `agent index <project folder>`.
- `Fel vid anrop till modellen` / `Error calling the model`
  - **Svenska:** Ollama är inte igång.
  - **English:** Ollama is not running.
