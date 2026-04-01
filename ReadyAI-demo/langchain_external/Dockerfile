FROM ghcr.io/astral-sh/uv:python3.11-trixie-slim

WORKDIR /app
COPY requirements.txt ./requirements.txt
COPY dist /app/dist
COPY ./ /app/

RUN uv pip install --system -r requirements.txt


CMD ["streamlit", "run", "readyai_app/app/main.py"]