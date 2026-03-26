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

## Connect to an existing vector store collection

`IRISVectorStore` can attach to an already-created IRIS table. You do not need
to recreate the collection each run.

Use the same `collection_name` and keep `replace_collection=False` (default):

```python
from langchain_openai import OpenAIEmbeddings
from langchain_intersystems.vectorstore import IRISVectorStore, SimilarityMetric

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

store = IRISVectorStore(
	embedding_function=embeddings,
	connect_kwargs={
		"hostname": "localhost",
		"port": 1972,
		"namespace": "USER",
		"username": "_SYSTEM",
		"password": "SYS",
	},
	collection_name="SOTU_Demo",      # existing table/collection name
	replace_collection=False,           # important: do not drop/recreate
	similarity_metric=SimilarityMetric.COSINE,
)

results = store.similarity_search("What did the president say about jobs?", k=3)
for doc in results:
	print(doc.id, doc.metadata)
```

Behavior when the collection already exists:

- Reuses the existing table.
- Validates that embedding dimension matches.
- Validates that stored embedding model marker matches.
- Loads existing metadata columns automatically.

When to use each constructor path:

- Use `IRISVectorStore(...)` to connect to an existing collection.
- Use `IRISVectorStore.from_texts(...)` when you want to create/load data from
  text immediately (it initializes the store and then adds texts).

Common failure cases:

- Different embedding model than what the collection was created with.
- Different embedding dimension.
- Invalid collection name format.
- Setting `replace_collection=True` (this will replace existing table data).

## What makes this interesting

- **No SQLAlchemy** — uses IRIS DB-API directly for performance
- **HNSW index** created automatically on the embedding column
- **Rich metadata filtering** — composable SQL-inspired predicates (`CONTAINS`, `BETWEEN`, `IN`, `LIKE`, etc.)
- **Separate metadata columns** — each metadata key gets its own indexed SQL column (not stuffed into JSON)
- Full LangChain `VectorStore` interface: `add_documents`, `similarity_search`, `similarity_search_with_score`, MMR search, async variants

## Source

Code lives in Perforce at `//Users/adang/langchain_intersystems/` (Aohan Dang).
Moving to GitLab: [CRE-14103](https://usjira.iscinternal.com/browse/CRE-14103)

## Demo files

| File | Purpose |
|---|---|
| `demo.py` | Simple demo with direct OpenAI credentials |
| `demo_configstore.py` | Full e2e: ConfigStore → `IRISChatModel` + `IRISVectorStore` → semantic search → LLM summarization, no API key in app code |
| `iris_chat_model.py` | `IRISChatModel` — `BaseChatModel` that resolves provider/model from IRIS ConfigStore (demo implementation of DP-445282) |
| `seed_configstore.py` | Creates `AIGateway_Storage.LLMProvider` table and registers `openai-demo` — the admin setup step from the user story |
