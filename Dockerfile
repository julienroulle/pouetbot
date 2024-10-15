FROM python:3.12.6-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

RUN apt-get update -y && apt-get install -y gnupg2 \
    && apt-key update \
    && apt-get update -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work
COPY . /work/

RUN uv sync --frozen --compile-bytecode \
    && uv build

ENTRYPOINT ["uv", "run", "bot.py"]
