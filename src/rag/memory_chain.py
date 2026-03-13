# src/rag/memory_chain.py

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from dotenv import load_dotenv
load_dotenv()
import os

from src.rag.retriever import ProductRetriever
from src.rag.intent import detect_intent, is_off_topic, OFF_TOPIC_REPLY
from src.rag.requirement_collector import (
    update_requirements, get_next_question,
    build_search_query, is_followup_question,
    extract_features_from_followup
)
from src.rag.rag_chain import build_rag_chain

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ALWAYS_DIRECT = {"warranty_query", "spec_compare", "price_query","load_capacity", "dimension_query" }

DIRECT_TO_RAG = {
    "warranty_query", "spec_compare", "price_query",
    "general_info", "unknown"
    # ❌ load_capacity and dimension_query REMOVED — these are mid-collection answers
}

_sessions: dict = {}

def get_session(session_id: str) -> dict:
    if session_id not in _sessions:
        _sessions[session_id] = {
            "history": [],
            "requirements": {}
        }
    return _sessions[session_id]


# Always bypass collection, even mid-collection
ALWAYS_DIRECT = {"warranty_query", "spec_compare", "price_query"}

def chat(session_id: str, user_input: str) -> dict:
    session = get_session(session_id)
    reqs = session["requirements"]
    memory = session["history"]
    intent = detect_intent(user_input)
    is_mid_collection = any(reqs.values())

    print(f"   [DEBUG] intent={intent} | is_mid={is_mid_collection} | reqs={reqs}")

    # 1 — Off-topic always blocked
    if is_off_topic(intent):
        return {"answer": OFF_TOPIC_REPLY, "intent": intent, "matched_products": [], "session_id": session_id}

    # 2 — ✅ These ALWAYS go to RAG, even mid-collection
    if intent in ALWAYS_DIRECT:
        return _run_rag(session_id, user_input, intent, memory, session)

    # 3 — Mid-collection: feed answer into requirements
    if is_mid_collection:
        reqs = update_requirements(reqs, user_input)
        reqs = extract_features_from_followup(user_input, reqs)
        session["requirements"] = reqs

        next_question = get_next_question(reqs)
        if next_question:
            memory.append(HumanMessage(content=user_input))
            memory.append(AIMessage(content=next_question))
            session["history"] = memory[-12:]
            return {
                "answer": next_question,
                "intent": "collecting_requirements",
                "requirements_so_far": reqs,
                "matched_products": [],
                "session_id": session_id
            }
        search_query = build_search_query(reqs)
        session["requirements"] = {}
        return _run_rag(session_id, search_query, intent, memory, session)

    # 4 — Other direct intents (not mid-collection)
    if intent in DIRECT_TO_RAG:
        return _run_rag(session_id, user_input, intent, memory, session)

    # 5 — Follow-up with history
    has_history = len(memory) > 0
    if has_history and is_followup_question(user_input):
        reqs = extract_features_from_followup(user_input, reqs)
        session["requirements"] = reqs
        if not reqs.get("load_kg"):
            next_q = get_next_question(reqs)
            if next_q:
                memory.append(HumanMessage(content=user_input))
                memory.append(AIMessage(content=next_q))
                session["history"] = memory[-12:]
                return {"answer": next_q, "intent": "collecting_requirements", "requirements_so_far": reqs, "matched_products": [], "session_id": session_id}
        return _run_rag(session_id, user_input, intent, memory, session)

    # 6 — Fresh collection
    reqs = update_requirements(reqs, user_input)
    session["requirements"] = reqs

    next_question = get_next_question(reqs)
    if next_question:
        memory.append(HumanMessage(content=user_input))
        memory.append(AIMessage(content=next_question))
        session["history"] = memory[-12:]
        return {"answer": next_question, "intent": "collecting_requirements", "requirements_so_far": reqs, "matched_products": [], "session_id": session_id}

    search_query = build_search_query(reqs)
    session["requirements"] = {}
    return _run_rag(session_id, search_query, intent, memory, session)

def _run_rag(session_id: str, query: str, intent: str, memory: list, session: dict) -> dict:
    enriched_query = query
    if memory:
        last_ai = next(
            (m.content for m in reversed(memory) if isinstance(m, AIMessage)), None
        )
        if last_ai:
            enriched_query = f"{query} (context: {last_ai[:300]})"

    chain = build_rag_chain()
    result = chain.invoke({
        "input": enriched_query,
        "chat_history": memory
    })

    memory.append(HumanMessage(content=query))
    memory.append(AIMessage(content=result["answer"]))
    session["history"] = memory[-12:]

    matched = [
        {"sku": doc.metadata.get("sku", ""), "name": doc.metadata.get("name", "")}
        for doc in result.get("context", [])
    ]

    return {
        "answer": result["answer"],
        "intent": intent,
        "matched_products": matched,
        "search_query_used": enriched_query,
        "session_id": session_id
    }


if __name__ == "__main__":
    sid = "test-001"
    for q in [
        "I need something for a tool box",
        "around 100kg",
        "500mm",
        "locking",
        "does it come with warranty?",
    ]:
        print(f"\n👤 {q}")
        r = chat(sid, q)
        print(f"🤖 [{r['intent']}]: {r['answer']}")
        if r.get("matched_products"):
            print(f"   📦 {[p['sku'] for p in r['matched_products']]}")