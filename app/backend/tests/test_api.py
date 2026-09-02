from fastapi.testclient import TestClient

from app.backend.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "study-uic-api"


def test_issues_crud_flow():
    create_response = client.post(
        "/api/v1/issues/",
        json={
            "title": "Campus Wi-Fi issue",
            "description": "The Wi-Fi in the library is failing for students near the west side.",
            "category": "facility",
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["title"] == "Campus Wi-Fi issue"
    assert created["status"] == "open"
    issue_id = created["id"]

    list_response = client.get("/api/v1/issues/")
    assert list_response.status_code == 200
    assert any(item["id"] == issue_id for item in list_response.json())

    patch_response = client.patch(
        f"/api/v1/issues/{issue_id}",
        json={"status": "in_review", "description": "Updated description after review."},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "in_review"

    get_response = client.get(f"/api/v1/issues/{issue_id}")
    assert get_response.status_code == 200
    assert get_response.json()["description"] == "Updated description after review."
