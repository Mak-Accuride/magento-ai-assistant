# src/rag/chat_chain.py

from src.rag.rag_chain import build_rag_chain
from src.rag.memory import build_memory
from src.rag.intent import classify_intent, Intent
from src.rag.clarify import needs_clarification, clarification_prompt
from src.rag.session_logger import log_turn


class ChatService:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.memory = build_memory(session_id)
        self.qa_chain = build_rag_chain()

    def chat(self, user_input: str) -> str:
        # 1. Clarification
        if needs_clarification(user_input):
            response = clarification_prompt(user_input)
            log_turn(self.session_id, user_input, response)
            return response

        # 2. Intent
        intent = classify_intent(user_input)

        if intent == Intent.OFF_TOPIC:
            response = "I can help with product-related questions. Could you rephrase?"
            log_turn(self.session_id, user_input, response)
            return response

        # 3. RAG invocation
        result = self.qa_chain.invoke({
            "input": user_input,
            "chat_history": self.memory.chat_memory.messages,
        })

        answer = result.get("answer", "I don't know")

        # 4. Save memory + log
        self.memory.save_context(
            {"input": user_input},
            {"output": answer},
        )

        log_turn(self.session_id, user_input, answer)

        return answer
