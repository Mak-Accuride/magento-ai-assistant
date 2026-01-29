# src/rag/session_logger.py

import json
from datetime import datetime
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def log_turn(session_id: str, user_input: str, response: str):
    log_file = LOG_DIR / f"{session_id}.jsonl"

    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_input": user_input,
        "response": response,
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(record) + "\n")
