from sentence_transformers import SentenceTransformer
import chromadb
import os

model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="tutor_docs")

def load_documents(docs_folder="../documents"):
    """Reads all .txt files from the documents folder"""
    documents = []
    for filename in os.listdir(docs_folder):
        if filename.endswith(".txt"):
            with open(os.path.join(docs_folder, filename), "r", encoding="utf-8") as f:
                content = f.read()
                documents.append({
                    "filename": filename,
                    "content": content
                })
    return documents

def chunk_text(text, chunk_size=500, overlap=50):
    """Splits text into chunks of chunk_size characters with overlapping characters."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks

def index_documents():
    """The main function of indexing"""
    print("Loading documents...")
    documents = load_documents()
    
    all_chunks = []
    all_ids = []
    all_metadata = []
    
    for doc in documents:
        chunks = chunk_text(doc["content"])
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_ids.append(f"{doc['filename']}_{i}")
            all_metadata.append({"source": doc["filename"]})
    
    print(f"Creating embeddings for {len(all_chunks)} chunks...")
    embeddings = model.encode(all_chunks).tolist()
    
    collection.upsert(
        documents=all_chunks,
        embeddings=embeddings,
        ids=all_ids,
        metadatas=all_metadata
    )
    
    print(f"Done! Indexed {len(all_chunks)} chunks from {len(documents)} documents.")

if __name__ == "__main__":
    index_documents()