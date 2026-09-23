import copy

import pytest
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from diagrams.models import DBTable, Diagram, DiagramFilter, Relationship
from diagrams.serializers import DiagramAggregateSerializer
from diagrams.services import replace_aggregate


@pytest.mark.django_db
def test_full_round_trip_and_order(diagram_payload):
    client = APIClient()
    created = client.post("/api/v1/diagrams", diagram_payload, format="json")
    assert created.status_code == 201, created.data
    assert created.data["revision"] == 1
    assert [table["id"] for table in created.data["tables"]] == ["users", "posts"]
    assert created.data["tables"][0]["indexes"][0]["fieldIds"] == ["user_id"]
    assert created.data["filter"] == {"schemaIds": [], "tableIds": ["users", "posts"]}

    fetched = client.get("/api/v1/diagrams/workspace001")
    assert fetched.status_code == 200
    assert fetched.data == created.data


@pytest.mark.django_db
def test_put_revision_conflict_and_atomicity(diagram_payload):
    client = APIClient()
    created = client.post("/api/v1/diagrams", diagram_payload, format="json").data
    update = copy.deepcopy(created)
    update["name"] = "Saved once"
    first = client.put("/api/v1/diagrams/workspace001", update, format="json")
    assert first.status_code == 200
    assert first.data["revision"] == 2

    update["name"] = "Stale write"
    stale = client.put("/api/v1/diagrams/workspace001", update, format="json")
    assert stale.status_code == 409
    assert stale.data["code"] == "conflict"
    assert Diagram.objects.get(external_id="workspace001").name == "Saved once"


@pytest.mark.django_db
def test_relationship_field_must_belong_to_selected_table(diagram_payload):
    client = APIClient()
    bad = copy.deepcopy(diagram_payload)
    bad["relationships"][0]["sourceFieldId"] = "owner_id"
    response = client.post("/api/v1/diagrams", bad, format="json")
    assert response.status_code == 400
    assert Diagram.objects.count() == 0


@pytest.mark.django_db
def test_delete_requires_current_revision(diagram_payload):
    client = APIClient()
    client.post("/api/v1/diagrams", diagram_payload, format="json")
    assert (
        client.delete("/api/v1/diagrams/workspace001", {"revision": 2}, format="json").status_code
        == 409
    )
    assert (
        client.delete("/api/v1/diagrams/workspace001", {"revision": 1}, format="json").status_code
        == 204
    )
    assert Diagram.objects.count() == 0
    assert DBTable.objects.count() == 0
    assert Relationship.objects.count() == 0
    assert DiagramFilter.objects.count() == 0


@pytest.mark.django_db
def test_sync_removes_children_missing_from_aggregate(diagram_payload):
    client = APIClient()
    current = client.post("/api/v1/diagrams", diagram_payload, format="json").data
    current["tables"] = current["tables"][:1]
    current["relationships"] = []
    current["dependencies"] = []

    response = client.put("/api/v1/diagrams/workspace001", current, format="json")

    assert response.status_code == 200
    assert [table["id"] for table in response.data["tables"]] == ["users"]
    assert response.data["relationships"] == []
    assert DBTable.objects.count() == 1


@pytest.mark.django_db
def test_mid_replace_database_error_rolls_back(diagram_payload, monkeypatch):
    client = APIClient()
    current = client.post("/api/v1/diagrams", diagram_payload, format="json").data
    current["name"] = "Must roll back"
    serializer = DiagramAggregateSerializer(data=current)
    serializer.is_valid(raise_exception=True)
    diagram = Diagram.objects.get(external_id="workspace001")

    def fail_create(**kwargs):
        raise IntegrityError("forced test failure")

    monkeypatch.setattr(DBTable.objects, "create", fail_create)
    with pytest.raises(IntegrityError), transaction.atomic():
        replace_aggregate(diagram, serializer.validated_data)

    diagram.refresh_from_db()
    assert diagram.name == "Shop"
    assert diagram.tables.count() == 2


@pytest.mark.django_db
def test_child_ids_are_unique_across_the_diagram(diagram_payload):
    duplicate = copy.deepcopy(diagram_payload)
    duplicate["tables"][1]["fields"][0]["id"] = "users_pk"

    response = APIClient().post("/api/v1/diagrams", duplicate, format="json")

    assert response.status_code == 400
    assert "childIds" in response.data["details"]
