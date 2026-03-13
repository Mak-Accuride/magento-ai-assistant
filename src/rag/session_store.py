# src/rag/session_store.py
# Simple file-based session log (no Redis needed yet)

import json
import os
from datetime import datetime
from pathlib import Path

LOG_DIR = Path("data/sessions")
LOG_DIR.mkdir(parents=True, exist_ok=True)


def log_turn(session_id: str, user_input: str, bot_response: dict):
    log_file = LOG_DIR / f"{session_id}.json"

    # Load existing log
    if log_file.exists():
        with open(log_file) as f:
            history = json.load(f)
    else:
        history = []

    # Append new turn
    history.append({
        "timestamp": datetime.utcnow().isoformat(),
        "user": user_input,
        "intent": bot_response.get("intent"),
        "answer": bot_response.get("answer"),
        "products": bot_response.get("matched_products", [])
    })

    with open(log_file, "w") as f:
        json.dump(history, f, indent=2)


def get_session_log(session_id: str) -> list:
    log_file = LOG_DIR / f"{session_id}.json"
    if not log_file.exists():
        return []
    with open(log_file) as f:
        return json.load(f)