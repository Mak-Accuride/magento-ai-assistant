# src/rag/chat_eval.py

from src.rag.chat_chain import ChatService

if __name__ == "__main__":
    chat = ChatService(session_id="test-session")

    queries = [
        "freezer",
        "energy efficient freezer",
        "does this include warranty?",
        "how to cook pasta"
    ]

    for q in queries:
        print("Q:", q)
        print("A:", chat.chat(q))
        print("-" * 50)
