# src/rag/requirement_collector.py

import re

# Questions to ask in order
REQUIRED_FIELDS = ["application", "load_kg", "length_mm", "slide_type"]

QUESTIONS = {
    "application": "What is the application? (e.g. kitchen drawer, tool box, medical trolley, industrial rack)",
    "load_kg":     "What load capacity do you need? (e.g. 45kg, 100kg, 200kg)",
    "length_mm":   "What length do you need? (e.g. 300mm, 500mm, 700mm)",
    "slide_type":  "Any preference on mechanism? (soft close / self close / locking / standard)",
}

# Optional — nice to have but not required
OPTIONAL_FIELDS = ["material", "extension"]
OPTIONAL_QUESTIONS = {
    "material":   "Any material preference? (e.g. stainless steel, zinc plated, aluminium) — or say 'any'",
    "extension":  "Do you need full extension (100%) or partial? — or say 'any'",
}
FOLLOWUP_SIGNALS = [
    "does it", "do they", "is it", "what is", "what's", "how much",
    "which one", "can it", "will it", "tell me more", "what about",
    "and the", "that one", "those", "this one"
]
def extract_load(text: str):
    """Extract kg value from text like 'around 100kg' or '200 kg'"""
    match = re.search(r'(\d+)\s*kg', text.lower())
    return float(match.group(1)) if match else None

def extract_length(text: str):
    """Extract mm value from text like '500mm' or '500 mm'"""
    match = re.search(r'(\d+)\s*mm', text.lower())
    return float(match.group(1)) if match else None

def extract_slide_type(text: str):
    text_lower = text.lower()
    if "soft" in text_lower:
        return "soft close"
    elif "self" in text_lower:
        return "self close"
    elif "lock" in text_lower:
        return "locking"
    elif "standard" in text_lower or "any" in text_lower:
        return "standard"
    return None

def update_requirements(reqs: dict, user_input: str) -> dict:
    """
    Try to extract any known fields from user message
    and fill into requirements dict
    """
    if not reqs.get("load_kg"):
        val = extract_load(user_input)
        if val:
            reqs["load_kg"] = val

    if not reqs.get("length_mm"):
        val = extract_length(user_input)
        if val:
            reqs["length_mm"] = val

    if not reqs.get("slide_type"):
        val = extract_slide_type(user_input)
        if val:
            reqs["slide_type"] = val

    # Application — just store raw text if not set
    if not reqs.get("application"):
        reqs["application"] = user_input

    return reqs

def get_next_question(reqs: dict) -> str | None:
    """Returns next question to ask, or None if all required fields collected"""
    for field in REQUIRED_FIELDS:
        if not reqs.get(field):
            return QUESTIONS[field]
    return None  # ✅ All collected — ready to search

def build_search_query(reqs: dict) -> str:
    """Build a natural language query from collected requirements"""
    parts = []
    if reqs.get("application"):
        parts.append(reqs["application"])
    if reqs.get("load_kg"):
        parts.append(f"{reqs['load_kg']}kg load capacity")
    if reqs.get("length_mm"):
        parts.append(f"{reqs['length_mm']}mm length")
    if reqs.get("slide_type"):
        parts.append(reqs["slide_type"])
    return " ".join(parts)

def is_followup_question(text: str) -> bool:
    """Returns True if this looks like a follow-up about a previously shown product"""
    text_lower = text.lower().strip()
    return any(text_lower.startswith(signal) for signal in FOLLOWUP_SIGNALS)
def extract_features_from_followup(text: str, reqs: dict) -> dict:
    """Extract slide_type from a follow-up question like 'does it have locking?'"""
    text_lower = text.lower()
    
    if not reqs.get("slide_type"):
        if "lock" in text_lower:
            reqs["slide_type"] = "locking"
        elif "soft" in text_lower:
            reqs["slide_type"] = "soft close"
        elif "self close" in text_lower:
            reqs["slide_type"] = "self close"

    return reqs

# --- Test ---
if __name__ == "__main__":
    reqs = {}
    
    inputs = [
        "around 100kg",
        "500mm",
        "locking",
        "I need something for a tool box",
    ]
    
    for user_input in inputs:
        reqs = update_requirements(reqs, user_input)
        next_q = get_next_question(reqs)
        
        print(f"User: {user_input}")
        print(f"Reqs so far: {reqs}")
        
        if next_q:
            print(f"Bot asks: {next_q}")
        else:
            query = build_search_query(reqs)
            print(f"✅ Ready to search: '{query}'")
        print()