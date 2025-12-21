import json
import numpy as np
from pathlib import Path

import faiss
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
# from langchain_community.vectorstores.utils import InMemoryDocstore



# Paths
EMBED_DIR = Path("data/embeddings")
INDEX_FILE = EMBED_DIR / "faiss_index.bin"
EMBEDDINGS_FILE = EMBED_DIR / "product_embeddings.npy"
META_FILE = EMBED_DIR / "product_metadata.json"



class ProductRetriever:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        print("🧠 Loading embedding model...")
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)

        print("📦 Loading metadata...")
        with open(META_FILE, "r") as f:
            self.metadata = json.load(f)

        print("🔢 Loading vectors...")
        vectors = np.load(EMBEDDINGS_FILE).astype("float32")

        print("🔗 Creating FAISS vectorstore from documents...")
        docs = [
            Document(page_content=f"{meta['name']} (SKU: {meta['sku']})", metadata=meta)
            for meta in self.metadata
        ]
        # self.vectorstore = FAISS.from_documents(docs, self.embeddings)
        self.vectorstore = FAISS.load_local(
            folder_path=EMBED_DIR,
            embeddings=self.embeddings,
            allow_dangerous_deserialization=True
        )


        print("✅ Retriever ready!")

    def get_retriever(self, top_k=5):
        return self.vectorstore.as_retriever(search_kwargs={"k": top_k})

    def search(self, query, k=5):
        retriever = self.get_retriever(top_k=k)
         # Safe call: use internal method if public one is unavailable
        if hasattr(retriever, "get_relevant_documents"):
            return retriever.get_relevant_documents(query)
        return retriever._get_relevant_documents(query, run_manager=None)


if __name__ == "__main__":
    r = ProductRetriever()
    results = r.search("550 liter chest freezer")
    print(dir(results))

    print("\n🔍 RESULTS\n")
    for doc in results:
        print(f"- {doc.metadata['sku']} → {doc.metadata['name']}")
