from sentence_transformers import SentenceTransformer
import chromadb
import os
import re

model = SentenceTransformer("all-MiniLM-L6-v2")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
client = chromadb.PersistentClient(path=os.path.join(BASE_DIR, "../chroma_db"))
collection = client.get_or_create_collection(name="tutor_docs")


def load_documents(docs_folder=None):
    if docs_folder is None:
        docs_folder = os.path.join(BASE_DIR, "../documents")
    documents = []
    for filename in os.listdir(docs_folder):
        if filename.endswith(".txt"):
            filepath = os.path.join(docs_folder, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                documents.append({"filename": filename, "content": content})
    print(f"Loaded {len(documents)} document(s): {[d['filename'] for d in documents]}")
    return documents


def chunk_by_separator(text, separator="---"):
    raw_chunks = text.split(separator)
    chunks = []
    for chunk in raw_chunks:
        cleaned = chunk.strip()
        if not cleaned:
            continue
        if re.fullmatch(r'[=\s]+', cleaned):
            continue
        if len(cleaned) < 30:
            continue
        chunks.append(cleaned)
    return chunks


def chunk_by_characters(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
    return chunks


def smart_chunk(filename, content):
    separator_count = content.count("---")
    if separator_count >= 3:
        print(f"  [{filename}] separator chunking ({separator_count} separators)")
        return chunk_by_separator(content)
    else:
        print(f"  [{filename}] character chunking")
        return chunk_by_characters(content)


def index_documents():
    print("=" * 50)
    print("Loading documents...")
    documents = load_documents()

    all_chunks = []
    all_ids = []
    all_metadata = []

    for doc in documents:
        chunks = smart_chunk(doc["filename"], doc["content"])
        print(f"  [{doc['filename']}] → {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_ids.append(f"{doc['filename']}_{i}")
            all_metadata.append({"source": doc["filename"], "chunk_index": i})

    print(f"\nCreating embeddings for {len(all_chunks)} total chunks...")
    embeddings = model.encode(all_chunks, show_progress_bar=True).tolist()

    print("Upserting into ChromaDB...")
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        collection.upsert(
            documents=all_chunks[i:i+batch_size],
            embeddings=embeddings[i:i+batch_size],
            ids=all_ids[i:i+batch_size],
            metadatas=all_metadata[i:i+batch_size]
        )

    print(f"\n✅ Done! Indexed {len(all_chunks)} chunks from {len(documents)} documents.")
    print("=" * 50)


if __name__ == "__main__":
    index_documents()
