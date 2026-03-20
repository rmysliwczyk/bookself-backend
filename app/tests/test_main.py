from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_status_endpoint_returns_200_ok():
    response = client.get("/status")
    assert response.status_code == 200

