import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["college"] == "Vidyavardhaka College of Engineering"
    assert "indexed_chunks" in data

def test_chat_sync_endpoint():
    response = client.post(
        "/api/chat",
        json={"query": "Tell me about admissions at VVCE"},
        headers={"X-Forwarded-For": "10.0.0.1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "sufficient_evidence" in data

def test_evaluation_run_endpoint():
    response = client.post("/api/eval/run")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "metrics" in data["summary"]
    assert "retrieval_hit_at_3" in data["summary"]["metrics"]
    assert "refusal_specificity_out_of_scope" in data["summary"]["metrics"]
