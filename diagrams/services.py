from django.db import transaction
from django.utils import timezone

from .models import (
    Area,
    CheckConstraint,
    CustomType,
    CustomTypeField,
    CustomTypeValue,
    DBField,
    DBIndex,
    DBTable,
    Dependency,
    Diagram,
    DiagramFilter,
    IndexField,
    Note,
    Relationship,
)


def _present(data, key):
    return key in data


def replace_aggregate(diagram: Diagram, data: dict):
    """Replace a normalized aggregate. Caller must hold an atomic transaction."""
    diagram.name = data["name"]
    diagram.database_type = data["databaseType"]
    diagram.database_edition = data.get("databaseEdition")
    diagram.updated_at = timezone.now()
    diagram.save(update_fields=["name", "database_type", "database_edition", "updated_at", "revision"])

    diagram.areas.all().delete()
    diagram.tables.all().delete()
    diagram.relationships.all().delete()
    diagram.dependencies.all().delete()
    diagram.notes.all().delete()
    diagram.custom_types.all().delete()
    DiagramFilter.objects.filter(diagram=diagram).delete()

    area_map = {}
    for position, item in enumerate(data.get("areas", [])):
        area_map[item["id"]] = Area.objects.create(
            diagram=diagram, external_id=item["id"], position=position,
            name=item["name"], x=item["x"], y=item["y"], width=item["width"],
            height=item["height"], color=item["color"], display_order=item.get("order"),
        )

    table_map, field_map = {}, {}
    for position, item in enumerate(data.get("tables", [])):
        checks = item.get("checkConstraints")
        table = DBTable.objects.create(
            diagram=diagram, external_id=item["id"], position=position, name=item["name"],
            schema_name=item.get("schema"), x=item["x"], y=item["y"], color=item["color"],
            is_view=item["isView"], is_materialized_view=item.get("isMaterializedView"),
            client_created_at=item["createdAt"], width=item.get("width"), comments=item.get("comments"),
            display_order=item.get("order"), expanded=item.get("expanded"),
            parent_area=area_map.get(item.get("parentAreaId")),
            check_constraints_defined=_present(item, "checkConstraints"),
            check_constraints_null=_present(item, "checkConstraints") and checks is None,
        )
        table_map[item["id"]] = table
        own_fields = {}
        for field_position, field_data in enumerate(item["fields"]):
            field = DBField.objects.create(
                table=table, external_id=field_data["id"], position=field_position,
                name=field_data["name"], type_id=field_data["type"]["id"],
                type_name=field_data["type"]["name"], primary_key=field_data["primaryKey"],
                unique=field_data["unique"], nullable=field_data["nullable"],
                increment=field_data.get("increment"), is_array=field_data.get("isArray"),
                client_created_at=field_data["createdAt"],
                character_maximum_length=field_data.get("characterMaximumLength"),
                precision=field_data.get("precision"), scale=field_data.get("scale"),
                default_value=field_data.get("default"), collation=field_data.get("collation"),
                comments=field_data.get("comments"), check_expression=field_data.get("check"),
            )
            own_fields[field_data["id"]] = field
            field_map[field_data["id"]] = field
        for index_position, index_data in enumerate(item["indexes"]):
            index = DBIndex.objects.create(
                table=table, external_id=index_data["id"], position=index_position,
                name=index_data["name"], unique=index_data["unique"],
                client_created_at=index_data["createdAt"], index_type=index_data.get("type"),
                is_primary_key=index_data.get("isPrimaryKey"), comments=index_data.get("comments"),
            )
            IndexField.objects.bulk_create([
                IndexField(index=index, field=own_fields[field_id], position=field_position)
                for field_position, field_id in enumerate(index_data["fieldIds"])
            ])
        for check_position, check in enumerate(checks or []):
            CheckConstraint.objects.create(
                table=table, external_id=check["id"], position=check_position,
                expression=check["expression"], client_created_at=check["createdAt"],
            )

    for position, item in enumerate(data.get("relationships", [])):
        Relationship.objects.create(
            diagram=diagram, external_id=item["id"], position=position, name=item["name"],
            source_schema=item.get("sourceSchema"), source_table=table_map[item["sourceTableId"]],
            target_schema=item.get("targetSchema"), target_table=table_map[item["targetTableId"]],
            source_field=field_map[item["sourceFieldId"]], target_field=field_map[item["targetFieldId"]],
            source_cardinality=item["sourceCardinality"], target_cardinality=item["targetCardinality"],
            client_created_at=item["createdAt"],
        )
    for position, item in enumerate(data.get("dependencies", [])):
        Dependency.objects.create(
            diagram=diagram, external_id=item["id"], position=position,
            schema_name=item.get("schema"), table=table_map[item["tableId"]],
            dependent_schema=item.get("dependentSchema"),
            dependent_table=table_map[item["dependentTableId"]], client_created_at=item["createdAt"],
        )
    for position, item in enumerate(data.get("notes", [])):
        Note.objects.create(
            diagram=diagram, external_id=item["id"], position=position, content=item["content"],
            x=item["x"], y=item["y"], width=item["width"], height=item["height"],
            color=item["color"], display_order=item.get("order"),
        )
    for position, item in enumerate(data.get("customTypes", [])):
        values, fields = item.get("values"), item.get("fields")
        custom_type = CustomType.objects.create(
            diagram=diagram, external_id=item["id"], position=position,
            schema_name=item.get("schema"), name=item["name"], kind=item["kind"],
            display_order=item.get("order"), values_defined=_present(item, "values"),
            values_null=_present(item, "values") and values is None,
            fields_defined=_present(item, "fields"), fields_null=_present(item, "fields") and fields is None,
        )
        CustomTypeValue.objects.bulk_create([
            CustomTypeValue(custom_type=custom_type, value=value, position=i)
            for i, value in enumerate(values or [])
        ])
        CustomTypeField.objects.bulk_create([
            CustomTypeField(custom_type=custom_type, name=field["field"], type_name=field["type"], position=i)
            for i, field in enumerate(fields or [])
        ])

    if "filter" in data:
        filter_data = data["filter"]
        DiagramFilter.objects.create(
            diagram=diagram,
            schema_ids_defined="schemaIds" in filter_data,
            schema_ids=filter_data.get("schemaIds", []),
            table_ids_defined="tableIds" in filter_data,
            table_ids=filter_data.get("tableIds", []),
        )


@transaction.atomic
def create_aggregate(data: dict):
    now = timezone.now()
    diagram = Diagram.objects.create(
        external_id=data["id"], name=data["name"], database_type=data["databaseType"],
        database_edition=data.get("databaseEdition"), revision=1,
        created_at=data.get("createdAt") or now, updated_at=now,
    )
    replace_aggregate(diagram, data)
    return diagram


def _nullable(payload, key, value):
    if value is not None:
        payload[key] = value


def aggregate_to_dict(diagram: Diagram):
    payload = {
        "id": diagram.external_id, "name": diagram.name, "databaseType": diagram.database_type,
        "createdAt": diagram.created_at, "updatedAt": diagram.updated_at, "revision": diagram.revision,
        "tables": [], "relationships": [], "dependencies": [], "areas": [], "customTypes": [], "notes": [],
    }
    _nullable(payload, "databaseEdition", diagram.database_edition)

    for area in diagram.areas.all():
        item = {"id": area.external_id, "name": area.name, "x": area.x, "y": area.y,
                "width": area.width, "height": area.height, "color": area.color}
        _nullable(item, "order", area.display_order)
        payload["areas"].append(item)

    for table in diagram.tables.all():
        item = {
            "id": table.external_id, "name": table.name, "x": table.x, "y": table.y,
            "fields": [], "indexes": [], "color": table.color, "isView": table.is_view,
            "createdAt": table.client_created_at,
        }
        for key, value in [
            ("schema", table.schema_name), ("isMaterializedView", table.is_materialized_view),
            ("width", table.width), ("comments", table.comments), ("order", table.display_order),
            ("expanded", table.expanded), ("parentAreaId", table.parent_area.external_id if table.parent_area else None),
        ]:
            _nullable(item, key, value)
        for field in table.fields.all():
            field_item = {
                "id": field.external_id, "name": field.name,
                "type": {"id": field.type_id, "name": field.type_name},
                "primaryKey": field.primary_key, "unique": field.unique, "nullable": field.nullable,
                "createdAt": field.client_created_at,
            }
            for key, value in [
                ("increment", field.increment), ("isArray", field.is_array),
                ("characterMaximumLength", field.character_maximum_length),
                ("precision", field.precision), ("scale", field.scale), ("default", field.default_value),
                ("collation", field.collation), ("comments", field.comments), ("check", field.check_expression),
            ]:
                _nullable(field_item, key, value)
            item["fields"].append(field_item)
        for index in table.indexes.all():
            index_item = {
                "id": index.external_id, "name": index.name, "unique": index.unique,
                "fieldIds": [link.field.external_id for link in index.index_fields.all()],
                "createdAt": index.client_created_at,
            }
            for key, value in [("type", index.index_type), ("isPrimaryKey", index.is_primary_key), ("comments", index.comments)]:
                _nullable(index_item, key, value)
            item["indexes"].append(index_item)
        if table.check_constraints_defined:
            item["checkConstraints"] = None if table.check_constraints_null else [
                {"id": check.external_id, "expression": check.expression, "createdAt": check.client_created_at}
                for check in table.check_constraints.all()
            ]
        payload["tables"].append(item)

    for rel in diagram.relationships.all():
        item = {
            "id": rel.external_id, "name": rel.name, "sourceTableId": rel.source_table.external_id,
            "targetTableId": rel.target_table.external_id, "sourceFieldId": rel.source_field.external_id,
            "targetFieldId": rel.target_field.external_id, "sourceCardinality": rel.source_cardinality,
            "targetCardinality": rel.target_cardinality, "createdAt": rel.client_created_at,
        }
        _nullable(item, "sourceSchema", rel.source_schema)
        _nullable(item, "targetSchema", rel.target_schema)
        payload["relationships"].append(item)
    for dep in diagram.dependencies.all():
        item = {"id": dep.external_id, "tableId": dep.table.external_id,
                "dependentTableId": dep.dependent_table.external_id, "createdAt": dep.client_created_at}
        _nullable(item, "schema", dep.schema_name)
        _nullable(item, "dependentSchema", dep.dependent_schema)
        payload["dependencies"].append(item)
    for note in diagram.notes.all():
        item = {"id": note.external_id, "content": note.content, "x": note.x, "y": note.y,
                "width": note.width, "height": note.height, "color": note.color}
        _nullable(item, "order", note.display_order)
        payload["notes"].append(item)
    for custom_type in diagram.custom_types.all():
        item = {"id": custom_type.external_id, "name": custom_type.name, "kind": custom_type.kind}
        _nullable(item, "schema", custom_type.schema_name)
        _nullable(item, "order", custom_type.display_order)
        if custom_type.values_defined:
            item["values"] = None if custom_type.values_null else [entry.value for entry in custom_type.values.all()]
        if custom_type.fields_defined:
            item["fields"] = None if custom_type.fields_null else [
                {"field": entry.name, "type": entry.type_name} for entry in custom_type.fields.all()
            ]
        payload["customTypes"].append(item)
    try:
        filter_model = diagram.diagram_filter
    except DiagramFilter.DoesNotExist:
        filter_model = None
    if filter_model:
        filter_payload = {}
        if filter_model.schema_ids_defined:
            filter_payload["schemaIds"] = filter_model.schema_ids
        if filter_model.table_ids_defined:
            filter_payload["tableIds"] = filter_model.table_ids
        payload["filter"] = filter_payload
    return payload


def summary_to_dict(diagram: Diagram):
    return {
        "id": diagram.external_id, "name": diagram.name, "databaseType": diagram.database_type,
        "databaseEdition": diagram.database_edition, "createdAt": diagram.created_at,
        "updatedAt": diagram.updated_at, "revision": diagram.revision,
    }

