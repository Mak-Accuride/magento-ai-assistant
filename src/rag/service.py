from src.rag.rag_chain import build_rag_chain
from src.rag.formatter import format_rag_response


def is_confident_enough(docs, min_docs=8):
    """
    Determine if the retrieval is confident enough to answer.
    Returns True if the number of documents meets the threshold.
    """
    return len(docs) >= min_docs


class ProductRAGService:
    """
    A simple service wrapper around your RAG chain.
    Provides an ask() method for querying products.
    """
    def __init__(self):
        print("🚀 Initializing ProductRAGService...")
        self.qa = build_rag_chain()
        print("✅ Service ready!")

    def ask(self, query: str, min_docs: int = 8):
        """
        Query the RAG chain and return formatted response.
        Only returns an answer if the retrieval is confident enough.
        """
        raw_result = self.qa.invoke({"input": query})

        # Get the retrieved docs from the raw RAG response
        retrieved_docs = raw_result.get("context", [])

        # Check confidence
        print(f"Confidence: min_docs={min_docs}, retrieved_docs={len(retrieved_docs)}")
        if is_confident_enough(retrieved_docs, min_docs=min_docs):
            return format_rag_response(raw_result)
        else:
            # Not enough confident docs, respond safely
            return {
                "answer": "I don't know",
                "matched_products": [doc.metadata for doc in retrieved_docs]
            }


# ===========================
# Quick test
# ===========================
if __name__ == "__main__":
    service = ProductRAGService()

    queries = [
        "550 liter chest freezer",
        "large pocket door system",
        "energy efficient freezer",
        "does this include warranty?",
        "how to cook pasta"
    ]

    for q in queries:
        print("=" * 60)
        print(f"Query: {q}")
        res = service.ask(q)
        print(res)
        print("\n")
