# src/rag/intent.py

import re

# src/rag/intent.py

INTENT_PATTERNS = {
    "spec_compare": ["compare", "difference", "vs", "versus", "better", "which one"],
    "price_query": ["price", "cost", "cheap", "expensive", "how much", "affordable"],
    "load_capacity": ["kg", "load", "weight", "capacity", "heavy", "support", "hold"],
    "product_query": ["slide", "drawer", "pocket door", "telescopic", "extension","soft close", "self close", "locking", "corrosion", "stainless"],
    "dimension_query": ["mm", "size", "length", "width", "depth", "dimension"],
    "warranty_query": ["warranty", "guarantee", "defect", "return", "replacement"],
    "application_query": ["kitchen", "office", "industrial", "medical", "outdoor","cabinet", "wardrobe", "freezer", "tool box", "rack", "toolbox"],
    "general_info": ["hello", "hi", "help", "what can you", "who are you"],
    "off_topic": ["cook", "recipe", "weather", "sport", "news", "movie"]
}

OFF_TOPIC_REPLY = "I specialise in sliding systems and drawer slides. Can I help you find the right slide for your project?"

def detect_intent(query: str) -> str:
    query_lower = query.lower()
    for intent, keywords in INTENT_PATTERNS.items():
        if any(kw in query_lower for kw in keywords):
            return intent
    return "unknown"

def is_off_topic(intent: str) -> bool:
    return intent == "off_topic"

def needs_clarification(intent: str) -> bool:
    return intent in ("unknown", "off_topic")


def get_clarification_prompt(intent: str) -> str:
    return CLARIFY_PROMPTS.get(intent, CLARIFY_PROMPTS["unknown"])


# --- Test ---
if __name__ == "__main__":
    test_queries = [
        "kitchen drawers",
        "compare heavy duty vs standard",
        "how much does this cost?",
        "does it hold 200kg?",
        "how to cook pasta",
        "hello",
        "I need something for a tool box",
    ]

    for q in test_queries:
        intent = detect_intent(q)
        clarify = needs_clarification(intent)
        print(f"Q: {q}")
        print(f"   Intent: {intent} | Needs clarification: {clarify}")
        if clarify:
            print(f"   Bot: {get_clarification_prompt(intent)}")
        print()