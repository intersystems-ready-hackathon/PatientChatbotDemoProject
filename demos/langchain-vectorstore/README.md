# LangChain IRISVectorStore Demo

Demonstrates [`langchain-intersystems`](https://gitlab.iscinternal.com/iris/lang-interop/langchain-intersystems) — Aohan Dang's LangChain `VectorStore` implementation backed by InterSystems IRIS vector search + HNSW indexing.

## What it does

Loads the 2022 State of the Union speech, chunks it, embeds it via OpenAI `text-embedding-3-small`, stores vectors in IRIS, then runs semantic similarity searches with optional metadata filters.

## Requirements

- Python 3.10+
- InterSystems IRIS 2025.1+ (see connection options below)
- `OPENAI_API_KEY` environment variable

## Setup

```bash
cd demos/langchain-vectorstore
pip install -r requirements.txt
```

## Run

```bash
export OPENAI_API_KEY=sk-...

# Default query against localhost:1972
python demo.py

# Custom query
python demo.py --query "What did the president say about Ukraine?" --top-k 3

# Point at a different IRIS instance
export IRIS_PORT=11972
python demo.py --query "climate and clean energy"
```

## IRIS connection environment variables

| Variable | Default | Description |
|---|---|---|
| `IRIS_HOSTNAME` | `localhost` | IRIS host |
| `IRIS_PORT` | `1972` | IRIS superserver port |
| `IRIS_NAMESPACE` | `USER` | IRIS namespace |
| `IRIS_USERNAME` | `_SYSTEM` | IRIS username |
| `IRIS_PASSWORD` | `SYS` | IRIS password |

## What makes this interesting

- **No SQLAlchemy** — uses IRIS DB-API directly for performance
- **HNSW index** created automatically on the embedding column
- **Rich metadata filtering** — composable SQL-inspired predicates (`CONTAINS`, `BETWEEN`, `IN`, `LIKE`, etc.)
- **Separate metadata columns** — each metadata key gets its own indexed SQL column (not stuffed into JSON)
- Full LangChain `VectorStore` interface: `add_documents`, `similarity_search`, `similarity_search_with_score`, MMR search, async variants

## Source

Code lives in Perforce at `//Users/adang/langchain_intersystems/` (Aohan Dang).
Moving to GitLab: [CRE-14103](https://usjira.iscinternal.com/browse/CRE-14103)
