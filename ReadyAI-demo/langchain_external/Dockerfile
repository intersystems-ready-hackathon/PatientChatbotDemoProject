# Stage 1: dependency caching
FROM ghcr.io/astral-sh/uv:python3.11-trixie-slim

WORKDIR /app
COPY requirements.txt ./
COPY dist /app/dist


RUN uv init && \
    uv pip install --system -r requirements.txt

