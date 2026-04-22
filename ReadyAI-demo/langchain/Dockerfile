FROM ghcr.io/astral-sh/uv:python3.11-trixie-slim

WORKDIR /app
COPY requirements.txt ./requirements.txt
COPY dist /app/dist
COPY ./ /app/

RUN uv pip install --system -r requirements.txt

RUN sed -i "s|sc = config_from_iris\.getValue()\.invoke('GetDetailsWithSecrets', details)|sc = config_from_iris\.getValue()\.invoke('CopyDetails',  details, 1)|g" /usr/local/lib/python3.11/site-packages/langchain_intersystems/chat_models.py
CMD ["streamlit", "run", "readyai_app/app/main.py"]