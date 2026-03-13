# src/eval_week5.py

from src.rag.memory_chain import chat
from src.rag.session_store import log_turn, get_session_log

SESSION_ID = "eval-week5-001"

# 5 test conversations
SESSIONS = [
    # Session 1 — product then memory follow-up
    [
        "What slides do you have for kitchen drawers?",
        "Which one has the best soft close?",
        "What is the load capacity?",
    ],
    # Session 2 — comparison
    [
        "Compare heavy duty vs standard drawer slides",
    ],
    # Session 3 — off-topic filter
    [
        "how to cook pasta",
        "what is the weather today",
    ],
    # Session 4 — warranty
    [
        "Does your product include a warranty?",
    ],
    # Session 5 — application based
    [
        "I need slides for a medical trolley",
        "Does it have a locking mechanism?",
        "around 50kg",                         # → asks length
        "400mm",                               # → asks type (already locking)
        "locking",                             # → asks length
    ],
]

if __name__ == "__main__":
    for i, session in enumerate(SESSIONS):
        sid = f"eval-session-{i+1}"
        print(f"\n{'='*60}")
        print(f"SESSION {i+1}")
        print('='*60)

        for question in session:
            print(f"\n👤 User: {question}")
            response = chat(sid, question)
            log_turn(sid, question, response)

            print(f"🤖 Bot  [{response['intent']}]: {response['answer']}")
            if response["matched_products"]:
                print(f"   📦 SKUs: {[p['sku'] for p in response['matched_products']]}")

    # Print session log summary
    print(f"\n{'='*60}")
    print("SESSION LOGS SAVED TO: data/sessions/")
    for i in range(len(SESSIONS)):
        sid = f"eval-session-{i+1}"
        log = get_session_log(sid)
        print(f"  Session {i+1}: {len(log)} turns logged ✅")