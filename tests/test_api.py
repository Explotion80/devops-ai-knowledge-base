from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ask_empty_question():
    response = client.post("/ask", json={"question": ""})
    assert response.status_code == 422


def test_ask_missing_body():
    response = client.post("/ask")
    assert response.status_code == 422


def test_list_documents():
    response = client.get("/documents")
    assert response.status_code == 200
    assert "files" in response.json()
