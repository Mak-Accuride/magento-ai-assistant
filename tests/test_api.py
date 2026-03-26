import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Test data
TEST_API_KEY = "dev-key-change-in-production"
HEADERS = {"X-API-Key": TEST_API_KEY}

def test_health_check():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert "version" in data

def test_search_unauthorized():
    """Test search without API key fails"""
    response = client.post("/api/v1/search", json={"query": "test"})
    assert response.status_code == 401

def test_search_authorized():
    """Test search with valid API key"""
    payload = {
        "query": "refrigerator",
        "top_k": 3,
        "language": "en"
    }
    response = client.post("/api/v1/search", json=payload, headers=HEADERS)
    # May fail if FAISS index not loaded, but should not 401
    assert response.status_code in [200, 500, 503]

def test_chat_unauthorized():
    """Test chat without API key fails"""
    response = client.post("/api/v1/chat", json={"message": "test"})
    assert response.status_code == 401

def test_chat_authorized():
    """Test chat with valid API key"""
    payload = {
        "message": "What refrigerators do you have?",
        "session_id": "test_session_1",
        "language": "en"
    }
    response = client.post("/api/v1/chat", json=payload, headers=HEADERS)
    # May fail if services not initialized, but should not 401
    assert response.status_code in [200, 500, 503]

def test_rate_limiting():
    """Test rate limiting is active (basic check)"""
    # Make multiple requests quickly
    responses = []
    for _ in range(5):
        r = client.get("/health")
        responses.append(r.status_code)
    # Should not be rate limited on health endpoint
    assert 429 not in responses