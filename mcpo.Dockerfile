FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN node -v && npm -v

COPY . /app
WORKDIR /app

ENV VIRTUAL_ENV=/app/.venv
RUN uv venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN uv pip install . && rm -rf ~/.cache

RUN which mcpo

EXPOSE 8000

ENV MCP_TRANSPORT=stdio
ENTRYPOINT ["mcpo"]

CMD ["--host", "0.0.0.0", "--port", "8000", "--", "uv", "run", "python", "-m", "src.server"]
