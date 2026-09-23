import json
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_endpoints():
    client = APIClient()
    assert client.get("/api/v1/health/live").status_code == 200
    assert client.get("/api/v1/health/ready").status_code == 200


@pytest.mark.django_db
def test_introspection_missing_configuration_does_not_leak_password(monkeypatch):
    monkeypatch.delenv("SOURCE_DB_NAME", raising=False)
    monkeypatch.delenv("SOURCE_DB_USER", raising=False)
    monkeypatch.delenv("SOURCE_DB_PASSWORD", raising=False)
    response = APIClient().post("/api/v1/source-database/introspect", {}, format="json")
    assert response.status_code == 503
    assert response.data["code"] == "source_database_unavailable"
    assert "password" not in str(response.data).lower()


@pytest.mark.django_db
def test_ai_missing_configuration_returns_503(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    response = APIClient().post(
        "/api/v1/ai/sql-export/stream",
        {"sqlScript": "CREATE TABLE x(id INT);", "targetDatabaseType": "mysql"},
        format="json",
    )
    assert response.status_code == 503


@pytest.mark.django_db
def test_ai_sse_event_order(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    with patch("ai_gateway.views.stream_sql_export", return_value=iter(["CREATE ", "TABLE x"] )):
        response = APIClient().post(
            "/api/v1/ai/sql-export/stream",
            {"sqlScript": "table x", "targetDatabaseType": "mysql"}, format="json",
        )
        body = b"".join(response.streaming_content).decode()
    events = [block for block in body.strip().split("\n\n")]
    assert events[0].startswith("event: delta")
    assert json.loads(events[0].split("data: ", 1)[1]) == {"text": "CREATE "}
    assert events[-1].startswith("event: done")

