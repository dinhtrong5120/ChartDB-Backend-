import pytest


@pytest.fixture
def diagram_payload():
    return {
        "id": "workspace001",
        "name": "Shop",
        "databaseType": "mysql",
        "databaseEdition": "mysql_5_7",
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-01T00:00:00Z",
        "areas": [
            {"id": "area1", "name": "Core", "x": 0, "y": 0, "width": 800, "height": 600, "color": "#fff", "order": 1}
        ],
        "tables": [
            {
                "id": "users", "name": "users", "schema": "shop", "x": 10, "y": 20,
                "color": "#abc", "isView": False, "createdAt": 1, "parentAreaId": "area1",
                "fields": [
                    {"id": "user_id", "name": "id", "type": {"id": "bigint", "name": "bigint"},
                     "primaryKey": True, "unique": True, "nullable": False, "increment": True, "createdAt": 2},
                    {"id": "user_email", "name": "email", "type": {"id": "varchar", "name": "varchar"},
                     "primaryKey": False, "unique": True, "nullable": False,
                     "characterMaximumLength": "255", "createdAt": 3},
                ],
                "indexes": [
                    {"id": "users_pk", "name": "PRIMARY", "unique": True,
                     "fieldIds": ["user_id"], "isPrimaryKey": True, "createdAt": 4}
                ],
                "checkConstraints": [],
            },
            {
                "id": "posts", "name": "posts", "x": 400, "y": 20,
                "color": "#def", "isView": False, "createdAt": 5,
                "fields": [
                    {"id": "post_id", "name": "id", "type": {"id": "bigint", "name": "bigint"},
                     "primaryKey": True, "unique": True, "nullable": False, "createdAt": 6},
                    {"id": "owner_id", "name": "owner_id", "type": {"id": "bigint", "name": "bigint"},
                     "primaryKey": False, "unique": False, "nullable": False, "createdAt": 7},
                ],
                "indexes": [],
            },
        ],
        "relationships": [
            {"id": "rel1", "name": "fk_owner", "sourceTableId": "users", "targetTableId": "posts",
             "sourceFieldId": "user_id", "targetFieldId": "owner_id", "sourceCardinality": "one",
             "targetCardinality": "many", "createdAt": 8}
        ],
        "dependencies": [
            {"id": "dep1", "tableId": "users", "dependentTableId": "posts", "createdAt": 9}
        ],
        "customTypes": [
            {"id": "status", "name": "status", "kind": "enum", "values": ["draft", "published"]}
        ],
        "notes": [
            {"id": "note1", "content": "hello", "x": 1, "y": 2, "width": 100,
             "height": 80, "color": "#eee", "order": 0}
        ],
        "filter": {"schemaIds": [], "tableIds": ["users", "posts"]},
    }

