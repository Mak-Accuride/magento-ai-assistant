import json
import faiss
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Paths
EMBED_DIR = Path("data/embeddings")
INDEX_FILE = EMBED_DIR / "faiss_index.bin"
META_FILE = EMBED_DIR / "product_metadata.json"


def load_index_and_metadata():
    index = faiss.read_index(str(INDEX_FILE))
    with open(META_FILE, "r") as f:
        metadata = json.load(f)
    return index, metadata


def run_faiss_search(index, query_vec, top_k=5):
    query_vec = np.asarray([query_vec]).astype("float32")
    faiss.normalize_L2(query_vec)
    distances, indices = index.search(query_vec, top_k)
    return indices[0]


def precision_at_k(retrieved_skus, relevant_skus, k=5):
    retrieved_top_k = set(retrieved_skus[:k])
    relevant_set = set(relevant_skus)
    correct = len(retrieved_top_k.intersection(relevant_set))
    return correct / k


def evaluate_search():
    print("📘 Loading FAISS index and metadata...")
    index, metadata = load_index_and_metadata()

    # Create SKU lookup by index
    sku_lookup = [item["sku"] for item in metadata]

    print("🧠 Loading embedding model...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    # -----------------------------
    # TEST QUERY SET (edit as needed)
    # -----------------------------
    test_queries = [
        {
            "query": "550 liter chest freezer",
            "relevant": ['DZ2907', 'DZ0305', 'DZ0301', 'DZ2807']
        },
        {
            "query": "glass door upright cooler",
            "relevant": ["DZ9308-0040L-E4", "DZ9308-0044R-E4"]
        },
        {
            "query": "commercial ice machine",
            "relevant": ["DZ4501-0050", "DZ4501-0060"]
        },
        {
            "query": "double door refrigerator",
            "relevant": ["DZ4501-0070TR", "DZ4501-0070EC"]
        },
        {
            "query": "undercounter freezer",
            "relevant": ["DS4180-080-035-0185U", "DS4180-080-035-0060U"]
        }
    ]

    print(f"📝 Evaluating {len(test_queries)} queries...")
    results = []
    
    for item in test_queries:
        query = item["query"]
        relevant = item["relevant"]

        print(f"\n🔎 Query: {query}")

        # Generate embedding
        vec = model.encode(query)

        # Run FAISS search
        idxs = run_faiss_search(index, vec, top_k=5)
        retrieved_skus = [sku_lookup[i] for i in idxs]

        print("   Retrieved:", retrieved_skus)
        print("   Relevant: ", relevant)

        # Calculate precision@5
        score = precision_at_k(retrieved_skus, relevant, k=5)
        results.append(score)
        print(f"   🎯 Precision@5: {score:.2f}")

    avg_precision = sum(results) / len(results)
    print("\n=====================================")
    print(f"⭐ Average Precision@5: {avg_precision:.2f}")
    print("=====================================")


if __name__ == "__main__":
    evaluate_search()
