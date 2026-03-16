"""
langchain-intersystems ConfigStore demo
----------------------------------------
Shows the pattern from the user story "Building a simple chatbot with LangChain":

    connection = iris.connect(...)
    model = IRISChatModel.from_config("openai-demo", connection=conn)

The LLM provider (name, model, credentials) is resolved from the IRIS AI Hub
ConfigStore — no hardcoded API keys in application code.

Also shows IRISVectorStore backed by the same IRIS instance, then uses the
chat model to summarize the top semantic search hits.

Prerequisites:
    1. pip install -r requirements.txt
    2. python seed_configstore.py        # register the 'openai-demo' provider
    3. export OPENAI_API_KEY=sk-...
    4. python demo_configstore.py

Environment variables:
    OPENAI_API_KEY  (required)
    IRIS_HOSTNAME   (default: localhost)
    IRIS_PORT       (default: 1972)
    IRIS_NAMESPACE  (default: USER)
    IRIS_USERNAME   (default: _SYSTEM)
    IRIS_PASSWORD   (default: SYS)
"""

import argparse
import os
import textwrap

import iris
import iris.dbapi
from langchain_community.document_loaders import TextLoader
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_intersystems import IRISVectorStore, SimilarityMetric
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter

from iris_chat_model import IRISChatModel


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------


def get_connect_kwargs() -> dict:
    return {
        "hostname": os.environ.get("IRIS_HOSTNAME", "localhost"),
        "port": int(os.environ.get("IRIS_PORT", "1972")),
        "namespace": os.environ.get("IRIS_NAMESPACE", "USER"),
        "username": os.environ.get("IRIS_USERNAME", "_SYSTEM"),
        "password": os.environ.get("IRIS_PASSWORD", "SYS"),
    }


# ---------------------------------------------------------------------------
# Step 1: Load vector store (reuse existing 'sotu_demo' or rebuild)
# ---------------------------------------------------------------------------


def get_or_build_vectorstore(conn_kwargs: dict) -> IRISVectorStore:
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # Check if collection already exists from demo.py run
    conn = iris.dbapi.connect(**conn_kwargs)
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM SQLUser.sotu_demo")
        count = cur.fetchone()[0]
        conn.close()
        if count > 0:
            print(f"Reusing existing 'sotu_demo' vector store ({count} chunks)")
            return IRISVectorStore(
                embeddings,
                connect_kwargs=conn_kwargs,
                collection_name="sotu_demo",
            )
    except Exception:
        conn.close()

    # Build fresh
    from pathlib import Path

    sotu_path = Path(__file__).parent / "state_of_the_union.txt"
    docs = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100).split_documents(
        TextLoader(str(sotu_path), encoding="utf-8").load()
    )
    print(f"Building vector store from {len(docs)} chunks...")
    store = IRISVectorStore(
        embeddings,
        connect_kwargs=conn_kwargs,
        collection_name="sotu_demo",
        replace_collection=True,
        similarity_metric=SimilarityMetric.COSINE,
    )
    store.add_documents(docs)
    print(f"✓ Indexed {len(docs)} chunks")
    return store


# ---------------------------------------------------------------------------
# Step 2: Resolve chat model from ConfigStore
# ---------------------------------------------------------------------------


def get_chat_model(conn_kwargs: dict) -> IRISChatModel:
    dbapi_conn = iris.dbapi.connect(**conn_kwargs)
    model = IRISChatModel.from_config("openai-demo", connection=dbapi_conn)
    print(f"✓ Resolved '{model.provider_name}' → model={model.model_name} from IRIS ConfigStore")
    return model


# ---------------------------------------------------------------------------
# Step 3: Search + summarize
# ---------------------------------------------------------------------------


def search_and_summarize(vectorstore, chat_model, query: str, top_k: int):
    print(f"\n{'=' * 65}")
    print(f"Query: {query!r}")
    print("=" * 65)

    # Semantic search
    hits = vectorstore.similarity_search_with_score(query, k=top_k)
    print(f"\n[Vector Search — top {top_k} results]")
    context_parts = []
    for rank, (doc, score) in enumerate(hits, 1):
        snippet = doc.page_content[:200].replace("\n", " ")
        print(f"  [{rank}] score={score:.4f}  {snippet}...")
        context_parts.append(doc.page_content)

    # Summarize with chat model from ConfigStore
    context = "\n\n---\n\n".join(context_parts)
    print(f"\n[Chat Model ({chat_model.provider_name} / {chat_model.model_name})]")
    print("Summarizing top results...")

    response = chat_model.invoke(
        [
            SystemMessage(
                content=(
                    "You are a concise summarizer. Given excerpts from a speech, "
                    "answer the user's question in 2-3 sentences using only the provided text."
                )
            ),
            HumanMessage(content=f"Question: {query}\n\nExcerpts:\n{context}"),
        ]
    )

    summary = response.content
    print(f"\nSummary: {textwrap.fill(summary, width=70, subsequent_indent='         ')}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="IRISChatModel + IRISVectorStore ConfigStore demo")
    parser.add_argument("--query", default="What did the president say about Ukraine?")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    conn_kwargs = get_connect_kwargs()
    print(f"IRIS: {conn_kwargs['hostname']}:{conn_kwargs['port']} ({conn_kwargs['namespace']})")

    vectorstore = get_or_build_vectorstore(conn_kwargs)
    chat_model = get_chat_model(conn_kwargs)

    search_and_summarize(vectorstore, chat_model, args.query, args.top_k)

    print("\n✓ Demo complete.")
    print("  The LLM provider name/model/credentials came from IRIS ConfigStore.")
    print("  Application code never touched an API key directly.")


if __name__ == "__main__":
    main()
