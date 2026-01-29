# src/rag/clarify.py

def needs_clarification(query: str) -> bool:
    """
    Detect vague or underspecified queries.
    """
    return len(query.split()) <= 2


def clarification_prompt(query: str) -> str:
    return (
        f"I found multiple possibilities for '{query}'. "
        "Could you clarify what you're looking for? "
        "For example: size, capacity, or product type."
    )
