def format_rag_response(response: dict) -> dict:
    """
    Formats the output of the modern RAG chain into a structured dictionary.
    
    Args:
        response (dict): Output from create_retrieval_chain, containing 'answer' and 'context' keys.
    
    Returns:
        dict: Structured response with 'answer' and 'matched_products'.
    """
    # Extract the generated answer (required)
    answer = response.get("answer", "").strip()
    
    # Extract retrieved documents (fallback to empty list if missing)
    docs = response.get("context", [])
    
    # Build list of matched products from document metadata
    products = [
        {
            "sku": doc.metadata.get("sku"),
            "name": doc.metadata.get("name")
        }
        for doc in docs
        if doc.metadata.get("sku") or doc.metadata.get("name")  # Optional: skip if no useful metadata
    ]
    
    return {
        "answer": answer,
        "matched_products": products
    }