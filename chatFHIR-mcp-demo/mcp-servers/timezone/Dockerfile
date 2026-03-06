FROM ghcr.io/astral-sh/uv:python3.11-trixie-slim
WORKDIR /app
RUN uv pip install --system mcpo

# Replace with your MCP server command; example: uvx mcp-server-time
CMD ["uvx", "mcpo", "--host", "0.0.0.0", "--port", "8000", "--", "uvx", "mcp-server-time", "--local-timezone=America/New_York"]