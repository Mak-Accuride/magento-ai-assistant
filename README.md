# 🧠 Magento AI Assistant

An intelligent multilingual assistant that connects with Magento to provide semantic product search, PDF-based enrichment, and conversational AI via FastAPI + LangChain.

---

## 🏗️ System Architecture

![Architecture](docs/architecture.png)

### Data Flow
1. **Magento API** — Fetches products and metadata.
2. **ETL / Data Ingestion** — Cleans and preprocesses Magento product data.
3. **PDF Processing** — Extracts specifications from manuals and links to SKUs.
4. **FAISS Index** — Embeds descriptions/specs for semantic search.
5. **FastAPI Backend** — Exposes `/search` and `/chat` endpoints for use by frontend or Magento store.
6. **Frontend / Chat UI** — Web-based or Magento-integrated chatbot.
7. **Redis / Cron** — Manages sync state and weekly updates.

---

## ⚙️ Core Technologies

| Layer | Tools / Frameworks |
|-------|--------------------|
| Backend API | FastAPI |
| AI / NLP | LangChain, Sentence-Transformers, XLM-RoBERTa |
| Embeddings Store | FAISS |
| Data Source | Magento REST API |
| Document Parsing | PyMuPDF |
| Deployment | Docker / AWS / Heroku |
| Optional | Redis (state/session), DeepL (translation) |

---

## 🚀 Setup Guide

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/yourusername/magento-ai-assistant.git
cd magento-ai-assistant


Week 7 — API Layer (FastAPI)

**Goal:** Build robust API endpoints for chat and search with authentication, rate limiting, and OpenAPI documentation.

**Deliverable:** Running FastAPI backend ready for Week 8 (Advanced RAG) and Week 9 (Frontend).

## 📋 Week 7 Schedule

| Day | Task Name | Hourly Task | Status |
|-----|-----------|-------------|--------|
| Mon | `fastapi-init` | Create FastAPI app with CORS and env settings | ✅ |
| Tue | `search-endpoint` | Implement POST /search (query, lang → ranked results) | ✅ |
| Wed | `chat-endpoint` | Add WebSocket or /chat endpoint for conversations | ✅ |
| Thu | `api-auth` | Secure with API key + rate limiting (slowapi) | ✅ |
| Fri | `swagger-test` | Add OpenAPI docs and test via Postman | ✅ |

## 🏗️ Architecture

```
┌─────────────────┐
│   Frontend      │  ← Week 9 (React)
│   (React)       │
└────────┬────────┘
         │ HTTP/WebSocket
         ▼
┌─────────────────┐
│   FastAPI       │  ← Week 7 (You are here)
│   ├── CORS      │
│   ├── Auth      │
│   ├── Rate Limit│
│   └── Routes    │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│ Search │ │ Chat   │
│Service │ │Service │
└────┬───┘ └────┬───┘
     │          │
     ▼          ▼
┌──────────────────────┐
│  Week 3-5 Services   │
│  • FAISS Index       │
│  • Embeddings        │
│  • RAG Chain         │
│  • Conversation Mem  │
└──────────────────────┘
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd week7_fastapi_api
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your keys:
# - OPENAI_API_KEY (from Week 4)
# - MAGENTO_API_TOKEN (from Week 1)
# - REDIS_URL (from Week 5)
```

### 3. Prepare Data Files
Ensure Week 3 FAISS index exists:
```
./data/
├── faiss_index.bin
└── product_metadata.pkl
```

### 4. Run Server
```bash
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Test Endpoints

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Search (requires API key):**
```bash
curl -X POST http://localhost:8000/api/v1/search \\
  -H "X-API-Key: dev-key-change-in-production" \\
  -H "Content-Type: application/json" \\
  -d '{"query": "refrigerator", "top_k": 5}'
```

**Chat (requires API key):**
```bash
curl -X POST http://localhost:8000/api/v1/chat \\
  -H "X-API-Key: dev-key-change-in-production" \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Which fridge has the best rating?", "session_id": "sess_123"}'
```

## 📚 API Documentation

Once running, access:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Schema:** http://localhost:8000/openapi.json

## 🔒 Security Features

- **API Key Authentication:** Header `X-API-Key` required for all endpoints except health
- **Rate Limiting:** 60 requests/minute default (via slowapi)
- **CORS:** Configured for frontend origins
- **Request ID Tracing:** All requests tagged with unique ID for debugging

## 🧪 Testing

**Run Pytest:**
```bash
pytest tests/test_api.py -v
```

**Import Postman Collection:**
Import `tests/postman_collection.json` into Postman for interactive testing.

## 📁 Project Structure

```
week7_fastapi_api/
├── main.py                    # FastAPI app entry point
├── requirements.txt           # Dependencies
├── .env.example              # Configuration template
├── app/
│   ├── api/
│   │   └── routes/           # Endpoint definitions
│   │       ├── search.py     # POST /api/v1/search
│   │       ├── chat.py       # POST /api/v1/chat + WebSocket
│   │       └── health.py     # Health checks
│   ├── core/
│   │   ├── config.py         # Pydantic settings
│   │   └── logging.py        # JSON logging
│   ├── models/
│   │   └── schemas.py        # Pydantic models
│   ├── services/
│   │   ├── index_service.py  # Service coordinator
│   │   ├── search_service.py # Vector search (Week 3)
│   │   └── chat_service.py   # Conversational RAG (Week 4-5)
│   └── dependencies/
│       └── auth.py           # Auth & rate limiting
└── tests/
    ├── test_api.py           # Pytest suite
    └── postman_collection.json
```

## 🔗 Integration with Previous Weeks

- **Week 3:** FAISS index loading, embeddings, vector search
- **Week 4:** RAG chain integration, LLM response generation
- **Week 5:** Conversation memory (Redis), intent classification

## 🎯 Success Criteria

- [x] FastAPI app runs without errors
- [x] POST /search returns ranked product results
- [x] POST /chat maintains conversation context
- [x] API key authentication blocks unauthorized requests
- [x] Rate limiting prevents abuse
- [x] OpenAPI docs are accessible and accurate
- [x] All endpoints tested via Postman

## 🚀 Next Steps

**Week 8:** Advanced RAG + Ranking (hybrid search, reranker)
**Week 9:** Frontend Integration (React chat UI)

## 📝 Notes

- **Week 6 (Multilingual)** skipped as requested—will implement after English MVP is stable
- Current embedding model: `all-MiniLM-L6-v2` (English optimized)
- Session memory stored in Redis (configurable TTL: 1 hour)
- Structured JSON logging for production observability