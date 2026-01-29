# src/rag/chat_eval.py

from src.rag.chat_chain import ChatService

if __name__ == "__main__":
    chat = ChatService(session_id="test-session")

    queries = [
        "What is the load rating of DZ4501?",
        "How do I install a DZ4501 full extension slide?",
        "Tell me about Accuride company history",
        "This product, can I use it for kitchen drawers?",
        "Random off-topic question"
    ]

    for q in queries:
        print("Q:", q)
        print("A:", chat.chat(q))
        print("-" * 50)
