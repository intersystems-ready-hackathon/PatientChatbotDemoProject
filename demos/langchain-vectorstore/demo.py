"""
langchain-intersystems IRISVectorStore demo
-------------------------------------------
Uses OpenAI embeddings (text-embedding-3-small) to load the State of the Union
speech into an IRIS vector store, then runs a few semantic similarity searches.

Requirements:
    pip install -r requirements.txt

Environment variables:
    OPENAI_API_KEY   - your OpenAI API key (required)
    IRIS_HOSTNAME    - IRIS host          (default: localhost)
    IRIS_PORT        - IRIS superserver   (default: 1972)
    IRIS_NAMESPACE   - IRIS namespace     (default: USER)
    IRIS_USERNAME    - IRIS username      (default: _SYSTEM)
    IRIS_PASSWORD    - IRIS password      (default: SYS)

Usage:
    python demo.py
    python demo.py --query "What did the president say about Ukraine?"
    python demo.py --query "climate and clean energy" --top-k 3
"""

import argparse
import os
import textwrap
from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain_intersystems import IRISVectorStore, SimilarityMetric, Predicate


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------


def get_connect_kwargs() -> dict:
    return {
        "hostname": os.environ.get("IRIS_HOSTNAME", "localhost"),
        "port": int(os.environ.get("IRIS_PORT", "1972")),
        "namespace": os.environ.get("IRIS_NAMESPACE", "USER"),
        "username": os.environ.get("IRIS_USERNAME", "_SYSTEM"),
        "password": os.environ.get("IRIS_PASSWORD", "SYS"),
    }


def get_embeddings() -> OpenAIEmbeddings:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY environment variable is not set.\n"
            "Export it before running:  export OPENAI_API_KEY=sk-..."
        )
    return OpenAIEmbeddings(model="text-embedding-3-small")


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------


def load_documents():
    """Load and chunk the State of the Union speech."""
    sotu_path = Path(__file__).parent / "state_of_the_union.txt"
    if not sotu_path.exists():
        # Fall back to the copy in the P4 workspace if running from there
        raise FileNotFoundError(
            f"state_of_the_union.txt not found at {sotu_path}\n"
            "Copy it from the langchain_intersystems P4 workspace root."
        )
    loader = TextLoader(str(sotu_path), encoding="utf-8")
    raw = loader.load()
    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = splitter.split_documents(raw)
    print(f"Loaded {len(docs)} document chunks from {sotu_path.name}")
    return docs


def build_store(docs, embeddings, connect_kwargs) -> IRISVectorStore:
    """Create (or replace) the IRIS vector store and index all documents."""
    print("Building IRIS vector store (this embeds all chunks via OpenAI)...")
    store = IRISVectorStore(
        embeddings,
        connect_kwargs=connect_kwargs,
        collection_name="sotu_demo",
        replace_collection=True,
        similarity_metric=SimilarityMetric.COSINE,
    )
    store.add_documents(docs)
    print(f"Indexed {len(docs)} chunks into IRIS.")
    return store


def run_queries(store: IRISVectorStore, query: str, top_k: int):
    """Run a similarity search and print results."""
    print(f"\n{'=' * 60}")
    print(f"Query: {query!r}   top_k={top_k}")
    print("=" * 60)

    results = store.similarity_search_with_score(query, k=top_k)
    for rank, (doc, score) in enumerate(results, 1):
        snippet = textwrap.fill(doc.page_content[:300], width=72, subsequent_indent="    ")
        print(f"\n[{rank}] score={score:.4f}")
        print(f"    {snippet}...")

    # Also show a filtered search example
    print(f"\n--- Same query filtered to source=state_of_the_union.txt ---")
    filtered = store.similarity_search_with_score(
        query,
        k=top_k,
        filter={"source": (Predicate.CONTAINS, "state_of_the_union.txt")},
    )
    print(f"    {len(filtered)} results with filter applied (should match)")


def main():
    parser = argparse.ArgumentParser(description="IRISVectorStore OpenAI demo")
    parser.add_argument("--query", default="Freedom and democracy", help="Semantic search query")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to return")
    args = parser.parse_args()

    connect_kwargs = get_connect_kwargs()
    print(
        f"Connecting to IRIS at {connect_kwargs['hostname']}:{connect_kwargs['port']} "
        f"({connect_kwargs['namespace']})"
    )

    embeddings = get_embeddings()
    docs = load_documents()
    store = build_store(docs, embeddings, connect_kwargs)
    run_queries(store, args.query, args.top_k)

    print("\nDemo complete. Vector store left in IRIS as 'sotu_demo' collection.")


if __name__ == "__main__":
    main()
