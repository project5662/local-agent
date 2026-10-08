FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
COPY src/ src/
RUN pip install .
ENV OLLAMA_HOST=http://host.docker.internal:11434
CMD ["agent", "chat", "/local_agent"]

