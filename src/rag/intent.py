# src/rag/intent.py

from enum import Enum

class Intent(str, Enum):
    PRODUCT_SEARCH = "product_search"
    PRODUCT_QUESTION = "product_question"
    GENERAL_QUESTION = "general_question"
    OFF_TOPIC = "off_topic"

# Keywords tailored to Accuride products
PRODUCT_KEYWORDS = [
    "slide", "drawer", "ball bearing", "mounting", "capacity", "liter",
    "model", "disconnect", "full extension", "hold-in", "soft-close",
    "self-close", "corrosion", "finish", "material", "length", "width",
    "load", "temperature", "dimensions"
]

GENERAL_QUESTION_KEYWORDS = ["how", "what", "why", "when", "where", "who"]

def classify_intent(query: str) -> Intent:
    q = query.lower()

    # Check if query matches known product-related keywords
    if any(k.lower() in q for k in PRODUCT_KEYWORDS):
        return Intent.PRODUCT_QUESTION

    # Check for general informational questions
    if any(q.startswith(w) for w in GENERAL_QUESTION_KEYWORDS):
        return Intent.GENERAL_QUESTION

    # Short queries are usually product searches (e.g., "DZ4501 slide")
    if len(q.split()) <= 3:
        return Intent.PRODUCT_SEARCH

    return Intent.OFF_TOPIC
