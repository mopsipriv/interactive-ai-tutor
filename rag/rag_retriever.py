from sentence_transformers import SentenceTransformer
import chromadb
import os
import re
import logging

logger = logging.getLogger("RAGRetriever")

_model = None
_client = None
_collection = None

def get_rag_model():
    global _model
    if _model is None:
        try:
            _model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            _model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
    return _model


def _auto_index_documents(collection):
    """Automatically index documents/*.txt into ChromaDB if collection is empty."""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    docs_dirs = [
        os.path.join(BASE_DIR, "../documents"),
        BASE_DIR,  # also pick up rag/study_right_guide.txt if present
    ]
    all_chunks = []
    all_ids = []
    all_metadata = []
    seen_files = set()

    for d in docs_dirs:
        if not os.path.isdir(d):
            continue
        for filename in sorted(os.listdir(d)):
            if not filename.endswith(".txt") or filename in seen_files:
                continue
            seen_files.add(filename)
            filepath = os.path.join(d, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                logger.warning(f"Failed to read {filepath}: {e}")
                continue

            if content.count("---") >= 3:
                chunks = [
                    c.strip() for c in content.split("---")
                    if c.strip() and not re.fullmatch(r"[=\s]+", c.strip()) and len(c.strip()) >= 30
                ]
            else:
                chunks = []
                start = 0
                while start < len(content):
                    chunk = content[start:start + 500].strip()
                    if chunk:
                        chunks.append(chunk)
                    start += 450

            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_ids.append(f"{filename}_{i}")
                all_metadata.append({"source": filename, "chunk_index": i})

    if not all_chunks:
        logger.warning("No .txt documents found to auto-index for RAG.")
        return

    logger.info(f"Auto-indexing {len(all_chunks)} chunks from {len(seen_files)} document(s) into ChromaDB...")
    model = get_rag_model()
    embeddings = model.encode(all_chunks).tolist()
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        collection.upsert(
            documents=all_chunks[i:i + batch_size],
            embeddings=embeddings[i:i + batch_size],
            ids=all_ids[i:i + batch_size],
            metadatas=all_metadata[i:i + batch_size],
        )
    logger.info(f"Auto-indexed {len(all_chunks)} chunks successfully.")


def get_collection():
    global _client, _collection
    if _collection is None:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        _client = chromadb.PersistentClient(path=os.path.join(BASE_DIR, "../chroma_db"))
        _collection = _client.get_or_create_collection(name="tutor_docs")
        if _collection.count() == 0:
            _auto_index_documents(_collection)
    return _collection


def retrieve(query: str, top_k: int = 3) -> str:
    collection = get_collection()
    if collection.count() == 0:
        return "No relevant information found."
    model = get_rag_model()
    query_embedding = model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(top_k, collection.count())
    )

    if not results["documents"] or not results["documents"][0]:
        return "No relevant information found."

    context_parts = []
    for i, doc in enumerate(results["documents"][0]):
        source = results["metadatas"][0][i]["source"]
        context_parts.append(f"[Source: {source}]\n{doc}")

    return "\n\n---\n\n".join(context_parts)

if __name__ == "__main__":
    result = retrieve("What should a tutor do in January?")
    print(result)