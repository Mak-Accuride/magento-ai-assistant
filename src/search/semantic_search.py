import json
import faiss
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

# File paths
EMBEDDING_DIR = Path("data/embeddings")
INDEX_FILE = EMBEDDING_DIR / "faiss_index.bin"
META_FILE = EMBEDDING_DIR / "product_metadata.json"

class SemanticSearcher:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        print("🔍 Loading FAISS index and embedding model...")
        
        self.index = faiss.read_index(str(INDEX_FILE))
        print(f"📦 FAISS index loaded — vectors: {self.index.ntotal}")

        with open(META_FILE, "r") as f:
            self.metadata = json.load(f)
        print(f"📘 Metadata loaded — {len(self.metadata)} items")

        self.model = SentenceTransformer(model_name)
        print(f"🧠 Embedding model ready: {model_name}")

    def encode_query(self, text: str):
        """Convert query into embedding."""
        emb = self.model.encode([text], convert_to_tensor=False)
        emb = np.asarray(emb).astype("float32")
        
        # Normalize for cosine similarity
        faiss.normalize_L2(emb)
        return emb

    def search(self, query: str, top_k: int = 50):
        print(f"\n🔎 Searching for: \"{query}\"")

        q_emb = self.encode_query(query)

        distances, indices = self.index.search(q_emb, top_k)
        print(distances , indices)
        results = []
        for rank, idx in enumerate(indices[0]):
            if idx == -1:
                continue
            meta = self.metadata[idx]
            results.append({
                "rank": rank + 1,
                "score": float(distances[0][rank]),
                "sku": meta["sku"],
                "name": meta["name"]
            })

        return results


def test_search():
    searcher = SemanticSearcher()

    while True:
        query = input("\n🔍 Enter search query (or 'exit'): ")
        if query.lower() in {"exit", "quit"}:
            break

        results = searcher.search(query, top_k=5)

        print("\n📌 Top Results:")
        for r in results:
            print(f" {r['rank']}. [{r['sku']}] {r['name']}  (score={r['score']:.4f})")


if __name__ == "__main__":
    test_search()
