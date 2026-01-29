# src/rag/intent.py

from enum import Enum


class Intent(str, Enum):
    PRODUCT_SEARCH = "product_search"
    PRODUCT_QUESTION = "product_question"
    GENERAL_QUESTION = "general_question"
    OFF_TOPIC = "off_topic"


PRODUCT_KEYWORDS = [
    "price", "size", "capacity", "liter", "warranty",
    "drawer", "freezer", "door", "system", "model","slide","Ball Bearing","Mounting",
]


def classify_intent(query: str) -> Intent:
    q = query.lower()

    if any(k in q for k in PRODUCT_KEYWORDS):
        return Intent.PRODUCT_QUESTION

    if q.startswith(("how", "what", "why")):
        return Intent.GENERAL_QUESTION

    if len(q.split()) <= 3:
        return Intent.PRODUCT_SEARCH

    return Intent.OFF_TOPIC
