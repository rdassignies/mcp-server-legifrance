FROM python:3.12-alpine

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

COPY uv.lock pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv export --no-group dev > requirements.txt && \
    uv pip install --python /usr/local/bin/python3 -r requirements.txt

# Copy source code
COPY src ./src


EXPOSE 8000

ENV PYTHONPATH="/app/src:$PYTHONPATH"
ENTRYPOINT ["python", "-m", "src.server"]
