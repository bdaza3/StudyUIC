from fastapi.testclient import TestClient

from app.backend.main import app
from app.backend.services.rag_retrieval import RetrievalResult

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "study-uic-api"


def test_rag_search_returns_retrieved_courses(monkeypatch) -> None:
    async def fake_retrieve(self, query):
        return [RetrievalResult(
            document_id="document-1",
            source_type="course",
            source_id="course-1",
            document_text="CS 361 course record",
            metadata={"course_code": "CS 361", "department": "CS"},
            similarity_score=0.9,
            embedding_model="text-embedding-3-small",
            embedding_version="1",
        )]

    monkeypatch.setattr("app.backend.routes.rag.RagRetriever.retrieve", fake_retrieve)
    response = client.post(
        "/api/v1/rag/search",
        json={"question": "Which course covers computer architecture?", "top_k": 1},
    )

    assert response.status_code == 200
    assert response.json()["results"][0]["metadata"]["course_code"] == "CS 361"


def test_concierge_plan_scaffold_detects_group_intent():
    response = client.post(
        "/api/v1/concierge/plan",
        json={"message": "Set up a Python study block for Tuesday afternoon."},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "planned",
        "mode": "group_match",
        "message": "Set up a Python study block for Tuesday afternoon.",
        "provider": "fallback",
        "intent": {
            "task": "plan_group",
            "subject": None,
            "location_hint": None,
            "time_hint": None,
            "duration_minutes": None,
            "constraints": ["Set up a Python study block for Tuesday afternoon."],
        },
        "next_stage": [
            "Connect semantic spot retrieval through Supabase pgvector",
            "Add calendar-aware conflict resolution and beacon creation",
        ],
    }


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
