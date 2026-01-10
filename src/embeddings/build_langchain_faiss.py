import json
from pathlib import Path
from sentence_transformers import SentenceTransformer

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document


# ========================
# PATHS
# ========================

PROCESSED_FILE = Path("data/processed/clean_products_with_pdf_parent_child2.json")
EMBEDDING_DIR = Path("data/embeddings")
EMBEDDING_DIR.mkdir(parents=True, exist_ok=True)

META_FILE = EMBEDDING_DIR / "product_metadata.json"


# ========================
# EMBEDDER
# ========================

class ProductFAISSBuilder:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L12-v2"):
        print(f"🧠 Loading embedding model: {model_name}")
        self.embedding_model_name = model_name
        self.lc_embeddings = HuggingFaceEmbeddings(model_name=model_name)

    def load_products(self):
        if not PROCESSED_FILE.exists():
            raise FileNotFoundError(f"❌ Missing processed file: {PROCESSED_FILE}")

        with open(PROCESSED_FILE, "r") as f:
            products = json.load(f)

        print(f"📦 Loaded {len(products)} products")
        return products

    def build_text(self, p: dict) -> str:
        """Build semantic text for embedding"""
        parts = [
            p.get("sku", ""),
            p.get("name", ""),
            p.get("short_description", ""),
            p.get("description", ""),
            p.get("specifications", ""),
            p.get("features", ""),
            p.get("material", ""),
            p.get("type", ""),
            p.get("uom", ""),
            p.get("country_of_manufacture", ""),
            p.get("meta_keyword", ""),
            p.get("meta_description", ""),
            p.get("corrosion_resistant", False),
            p.get("finish", ""),
            p.get("temperature_range", ""),
            p.get("material", ""),
            # Add inherited or PDF specs
            self._extract_specs(p.get("pdf_specs") or p.get("inherited_specs", {})),
            # Explicit keywords for capacity/load
            f"Capacity: {p.get('capacity', '')}" if p.get("capacity") else "",
            f"Load Rating: {p.get('load_rating', '')}" if p.get("load_rating") else "",
            f"Dimensions: {p.get('dimensions', '')}" if p.get("dimensions") else "",
        ]
        cleaned_parts = [str(part).strip() for part in parts if part]
        return ". ".join(cleaned_parts).strip()

    def _extract_specs(self, specs):
        if not specs:
            return ""
        key_fields = [
            "load_rating", "slide_extension", "slide_height", "slide_thickness",
            "temperature_range", "main_material", "finish", "features_summary"
        ]
        return " ".join([f"{k.replace('_', ' ').title()}: {specs.get(k, '')}" for k in key_fields if specs.get(k)])
    
    def build_documents(self, products):
        docs = []
        metadata_out = []

        for p in products:
            text = self.build_text(p)

            metadata = {
                "product_id": p["product_id"],
                "product_id": p["product_id"],
                "sku": p.get("sku"),
                "name": p.get("name"),
                "type": p.get("type"),
                "material": p.get("material"),
                "load_rating": self._extract_specs((p.get("pdf_specs") or p.get("inherited_specs", {}))),
                "capacity": p.get("capacity"),
                "category_id": p.get("category_id")
            }

            docs.append(
                Document(
                    page_content=text,
                    metadata=metadata
                )
            )

            metadata_out.append(metadata)

        return docs, metadata_out

    def save_metadata(self, metadata):
        with open(META_FILE, "w") as f:
            json.dump(metadata, f, indent=2)

        print(f"📘 Metadata saved → {META_FILE}")

    def build_and_save_faiss(self):
        products = self.load_products()

        print("🧩 Building LangChain documents...")
        docs, metadata = self.build_documents(products)

        print("🔗 Creating FAISS vectorstore...")
        vectorstore = FAISS.from_documents(docs, self.lc_embeddings)

        print("💾 Saving FAISS index (LangChain format)...")
        vectorstore.save_local(EMBEDDING_DIR)

        self.save_metadata(metadata)

        print("✅ FAISS index saved successfully!")
        print("📁 Files created:")
        print("  - index.faiss")
        print("  - index.pkl")
        print("  - product_metadata.json")


# ========================
# MAIN
# ========================

if __name__ == "__main__":
    builder = ProductFAISSBuilder()
    builder.build_and_save_faiss()

    print("🎉 Done!")