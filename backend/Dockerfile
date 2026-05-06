FROM ghcr.io/astral-sh/uv:python3.12-bookworm
WORKDIR /app
COPY pyproject.toml uv.lock* README.md ./
COPY src ./src
RUN uv sync --frozen || uv sync
COPY . .
CMD ["uv", "run", "uvicorn", "hexarag_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
