# src/rag/memory.py

from langchain.memory import ConversationBufferMemory

def build_memory(session_id: str):
    """
    Creates conversational memory per session.
    """
    return ConversationBufferMemory(
        memory_key="chat_history",
        input_key="input",
        return_messages=True,
    )
