from sentence_transformers import SentenceTransformer
import chromadb
import os

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

def get_collection():
    global _client, _collection
    if _collection is None:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        _client = chromadb.PersistentClient(path=os.path.join(BASE_DIR, "../chroma_db"))
        _collection = _client.get_or_create_collection(name="tutor_docs")
    return _collection

def retrieve(query: str, top_k: int = 3) -> str:
    model = get_rag_model()
    collection = get_collection()
    query_embedding = model.encode([query]).tolist()
    
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
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