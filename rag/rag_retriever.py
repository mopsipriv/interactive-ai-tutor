from sentence_transformers import SentenceTransformer
import chromadb

model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="tutor_docs")

def retrieve(query: str, top_k: int = 3) -> str:
    """
    Accepts a question and returns the top_k relevant pieces of text as a single string.
    Used in the RAG agent to obtain context.
    """
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