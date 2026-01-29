# src/rag/memory.py

from langchain_core.messages import HumanMessage, AIMessage

class SimpleMemory:
    """
    Lightweight chat memory that supports multi-turn context.
    """
    def __init__(self):
        self.messages = []

    def add_user(self, text: str):
        self.messages.append(HumanMessage(content=text))

    def add_ai(self, text: str):
        self.messages.append(AIMessage(content=text))

    def get_messages(self, last_n: int = None):
        """Return last N messages, or all if None"""
        if last_n:
            return self.messages[-last_n:]
        return self.messages

    def get_formatted_context(self, last_n: int = 5):
        """
        Format messages into a single string for RAG retrieval.
        """
        msgs = self.get_messages(last_n)
        context = ""
        for m in msgs:
            role = "User" if isinstance(m, HumanMessage) else "AI"
            context += f"{role}: {m.content}\n"
        return context
