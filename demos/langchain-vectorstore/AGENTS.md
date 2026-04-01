# AGENTS.md — demos/langchain-vectorstore/

Standalone demo of `langchain-intersystems` `IRISVectorStore`. Separate IRIS instance — NOT connected to the ReadyAI-demo container.

## Files

| File | Purpose |
|------|---------|
| `demo.py` | Load SOTU speech → OpenAI embeddings → IRIS vector store → similarity search |
| `demo_configstore.py` | E2E: ConfigStore → `IRISChatModel` + `IRISVectorStore` → LLM summarization (no API key in app) |
| `iris_chat_model.py` | Demo `IRISChatModel` — resolves provider/model from IRIS ConfigStore (DP-445282 pattern) |
| `seed_configstore.py` | Admin setup: creates `AIGateway_Storage.LLMProvider` table, registers `openai-demo` |
| `LANGCHAIN_INTERSYSTEMS_DOCS.md` | API reference for `langchain-intersystems` |

## Connection

All env vars — no hardcoded values:

```bash
export IRIS_HOSTNAME=localhost  # default
export IRIS_PORT=1972           # default
export IRIS_NAMESPACE=USER      # default
export IRIS_USERNAME=_SYSTEM    # default
export IRIS_PASSWORD=SYS        # default
export OPENAI_API_KEY=sk-...    # required for demo.py
```

## IRISVectorStore Patterns

```python
from langchain_intersystems import IRISVectorStore, SimilarityMetric, Predicate

# Create/replace
store = IRISVectorStore(embeddings, connect_kwargs=..., collection_name="my_store",
                        replace_collection=True, similarity_metric=SimilarityMetric.COSINE)

# Attach to existing (don't recreate)
store = IRISVectorStore(embeddings, connect_kwargs=..., collection_name="my_store",
                        replace_collection=False)

# Metadata filter
store.similarity_search_with_score(query, k=5,
    filter={"source": (Predicate.CONTAINS, "file.txt")})
```

## Anti-Patterns

- `replace_collection=True` destroys existing data — only use for fresh load
- Do NOT mix embedding models between store creation and query — dimension mismatch error
- Source: P4 `//Users/adang/langchain_intersystems/`, GitLab CRE-14103 (Aohan Dang)
