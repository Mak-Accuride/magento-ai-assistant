import json
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

# Paths
EMBED_DIR = Path("data/embeddings")
META_FILE = EMBED_DIR / "product_metadata.json"


class ProductRetriever:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L12-v2"):
        print("🧠 Loading embedding model...")
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)

        print("📦 Loading metadata...")
        with open(META_FILE, "r") as f:
            self.metadata = json.load(f)

        print("🔗 Loading FAISS index from disk...")
        # self.vectorstore = FAISS.load_local(EMBED_DIR, embeddings=self.embeddings)
        self.vectorstore = FAISS.load_local(
            EMBED_DIR,
            embeddings=self.embeddings,
            allow_dangerous_deserialization=True  # ⚠️ Only for trusted local files
        )
        print("✅ Retriever ready!")

    def get_retriever(self, top_k=5):
        return self.vectorstore.as_retriever(search_kwargs={"k": top_k})

    def search(self, query, k=5):
        retriever = self.get_retriever(top_k=k)
        # Use the internal method safely
        if hasattr(retriever, "_get_relevant_documents"):
            return retriever._get_relevant_documents(query, run_manager=None)
        else:
            raise RuntimeError("Retriever does not support _get_relevant_documents")



if __name__ == "__main__":
    r = ProductRetriever()
    results = r.search("550 liter chest freezer", k=5)

    print("\n🔍 RESULTS\n")
    for doc in results:
        print(f"- {doc.metadata['sku']} → {doc.metadata['name']}")
