FROM python:3.14-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.9.27 /uv /uvx /bin/

RUN apt-get update && apt-get install -y --no-install-recommends \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libice6 \
    libsm6 \
    libglib2.0-0 \
    libxml2 \
    libgl1 \
    libatomic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN uv sync --locked

RUN mkdir -p /app/output

EXPOSE 8000

CMD ["uv", "run", "src/main.py"]
