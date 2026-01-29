# src/rag/chat_chain.py
from src.rag.rag_chain import build_rag_chain
from src.rag.memory import SimpleMemory
from src.rag.intent import classify_intent, Intent
from src.rag.clarify import needs_clarification, clarification_prompt
from src.rag.session_logger import log_turn

class ChatService:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.memory = SimpleMemory()
        self.qa_chain = build_rag_chain()

    def chat(self, user_input: str) -> str:
        # 1️⃣ Clarification
        if needs_clarification(user_input):
            response = clarification_prompt(user_input)
            log_turn(self.session_id, user_input, response)
            return response

        # 2️⃣ Intent classification
        intent = classify_intent(user_input)
        if intent == Intent.OFF_TOPIC:
            response = "I can help with product-related questions. Could you rephrase?"
            log_turn(self.session_id, user_input, response)
            return response

        # 3️⃣ Multi-turn context
        context = self.memory.get_formatted_context(last_n=5)  # last 5 messages

        # 4️⃣ Call RAG chain
        result = self.qa_chain.invoke({
            "input": user_input,
            "context": context  # feed memory as context
        })

        answer = result.get("answer", "I don't know")

        # 5️⃣ Save to memory
        self.memory.add_user(user_input)
        self.memory.add_ai(answer)

        # 6️⃣ Log session
        log_turn(self.session_id, user_input, answer)

        return answer
