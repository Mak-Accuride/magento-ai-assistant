import json
from pathlib import Path
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

    def _extract_specs_text(self, specs: dict) -> str:
        """Flatten inherited/pdf specs for embedding text."""
        if not specs:
            return ""
        parts = []
        for k, v in specs.items():
            if v:
                parts.append(f"{k.replace('_',' ').title()}: {v}")
        return ". ".join(parts)

    def build_text(self, p: dict) -> str:
        """Build a large text blob for embedding including all relevant attributes."""
        parts = [
            p.get("sku", ""),
            p.get("name", ""),
            p.get("short_description", ""),
            p.get("description", ""),
            p.get("product_features", ""),
            p.get("material", ""),
            p.get("length_mm", ""),
            str(p.get("dimensions", "")),
            str(p.get("capacity", "")),
            str(p.get("weight_kg", "")),
            p.get("uom", ""),
            p.get("country_of_manufacture", ""),
            p.get("category_id", ""),
            p.get("mpn", ""),
            p.get("gtin", ""),
            p.get("hub_product_id", ""),
            p.get("commodity_code", ""),
            p.get("finish", ""),
            p.get("tax_class_id", ""),
            str(p.get("product_for_sales", "")),
            str(p.get("is_top_choice", "")),
            str(p.get("is_returnable", "")),
            str(p.get("soft_close", "")),
            str(p.get("self_close", "")),
            str(p.get("self_open", "")),
            str(p.get("hold_in", "")),
            str(p.get("hold_out", "")),
            str(p.get("lock_in", "")),
            str(p.get("lock_out", "")),
            str(p.get("interlock", "")),
            str(p.get("cam_adjust", "")),
            str(p.get("rohs", "")),
            str(p.get("bhma", "")),
            str(p.get("awi", "")),
            str(p.get("weather_resistant", "")),
            str(p.get("corrosion_resistant", "")),
            str(p.get("required_options", "")),
            str(p.get("has_options", "")),
            str(p.get("options_container", "")),
            str(p.get("gift_message_available", "")),
            str(p.get("gift_wrapping_available", "")),
            p.get("subaccount", ""),
            p.get("project_number", ""),
            self._extract_specs_text(p.get("inherited_specs", {})),
            self._extract_specs_text(p.get("pdf_specs", {})),
            str(p.get("prices", {})),
            f"Download datasheet: {p.get('download_datasheet', '')}" if p.get("download_datasheet") else ""
        ]
        # remove empty parts and join
        return ". ".join([str(part).strip() for part in parts if part]).strip()

    def build_documents(self, products):
        docs = []
        metadata_out = []

        for p in products:
            text = self.build_text(p)
            metadata = {k: v for k, v in p.items() if v is not None}  # Keep all attributes
            docs.append(Document(page_content=text, metadata=metadata))
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
