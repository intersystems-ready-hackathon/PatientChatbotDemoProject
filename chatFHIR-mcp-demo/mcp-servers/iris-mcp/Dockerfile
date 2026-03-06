# Stage 1: dependency caching
FROM ghcr.io/astral-sh/uv:python3.11-trixie-slim

WORKDIR /app
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

COPY server.py .
EXPOSE 8000
CMD ["uv", "run", "mcpo", "--host", "0.0.0.0", "--port", "8000", "--", "python", "/app/server.py"]