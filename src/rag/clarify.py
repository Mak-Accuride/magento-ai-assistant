# src/rag/clarify.py

def needs_clarification(query: str) -> bool:
    """
    Detect vague or underspecified queries.
    """
    vague_words = ["this", "that", "it", "those", "these"]
    return any(word in query.lower() for word in vague_words)


def clarification_prompt(query: str) -> str:
    return f"I'm not sure what you mean by '{query}'. Could you clarify?"
