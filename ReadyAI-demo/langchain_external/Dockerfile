# Stage 1: dependency caching
FROM ghcr.io/astral-sh/uv:python3.11-trixie-slim

WORKDIR /app
COPY requirements.txt ./
COPY dist /app/dist
COPY readyai_app/app ./app

RUN uv pip install --system -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "/app/readyai_app/app/main.py", "--server.address=0.0.0.0", "--server.port=8501"]

