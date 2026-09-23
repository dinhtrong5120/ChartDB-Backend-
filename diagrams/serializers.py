from rest_framework import serializers

DATABASE_TYPES = [
    "generic",
    "postgresql",
    "mysql",
    "sql_server",
    "mariadb",
    "sqlite",
    "clickhouse",
    "cockroachdb",
    "oracle",
]
DATABASE_EDITIONS = [
    "supabase",
    "timescale",
    "mysql_5_7",
    "sql_server_2016_and_below",
    "cloudflare_d1",
]
INDEX_TYPES = [
    "btree",
    "hash",
    "gist",
    "gin",
    "spgist",
    "brin",
    "nonclustered",
    "clustered",
    "xml",
    "fulltext",
    "spatial",
    "index",
]
CARDINALITIES = ["one", "many"]


class NullableMixin:
    def optional(self, field):
        field.required = False
        field.allow_null = True
        return field


class DataTypeSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=255)
    name = serializers.CharField(max_length=255)


class FieldSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=255)
    type = DataTypeSerializer()
    primaryKey = serializers.BooleanField()
    unique = serializers.BooleanField()
    nullable = serializers.BooleanField()
    increment = serializers.BooleanField(required=False, allow_null=True)
    isArray = serializers.BooleanField(required=False, allow_null=True)
    createdAt = serializers.IntegerField()
    characterMaximumLength = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    precision = serializers.IntegerField(required=False, allow_null=True)
    scale = serializers.IntegerField(required=False, allow_null=True)
    default = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    collation = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    comments = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    check = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class IndexSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=255, allow_blank=True)
    unique = serializers.BooleanField()
    fieldIds = serializers.ListField(child=serializers.CharField(max_length=64))
    createdAt = serializers.IntegerField()
    type = serializers.ChoiceField(choices=INDEX_TYPES, required=False, allow_null=True)
    isPrimaryKey = serializers.BooleanField(required=False, allow_null=True)
    comments = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class CheckConstraintSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=64)
    expression = serializers.CharField()
    createdAt = serializers.IntegerField()


class TableSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=255)
    schema = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    x = serializers.FloatField()
    y = serializers.FloatField()
    fields = FieldSerializer(many=True)
    indexes = IndexSerializer(many=True)
    checkConstraints = CheckConstraintSerializer(many=True, required=False, allow_null=True)
    color = serializers.CharField(max_length=64)
    isView = serializers.BooleanField()
    isMaterializedView = serializers.BooleanField(required=False, allow_null=True)
    createdAt = serializers.IntegerField()
    width = serializers.FloatField(required=False, allow_null=True)
    comments = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    order = serializers.IntegerField(required=False, allow_null=True)
    expanded = serializers.BooleanField(required=False, allow_null=True)
    parentAreaId = serializers.CharField(
        max_length=64, required=False, allow_null=True, allow_blank=True
    )


class RelationshipSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=255, allow_blank=True)
    sourceSchema = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    sourceTableId = serializers.CharField(max_length=64)
    targetSchema = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    targetTableId = serializers.CharField(max_length=64)
    sourceFieldId = serializers.CharField(max_length=64)
    targetFieldId = serializers.CharField(max_length=64)
    sourceCardinality = serializers.ChoiceField(choices=CARDINALITIES)
    targetCardinality = serializers.ChoiceField(choices=CARDINALITIES)
    createdAt = serializers.IntegerField()


class DependencySerializer(serializers.Serializer):
    id = serializers.CharField(max_length=64)
    schema = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    tableId = serializers.CharField(max_length=64)
    dependentSchema = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    dependentTableId = serializers.CharField(max_length=64)
    createdAt = serializers.IntegerField()


class AreaSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=255)
    x = serializers.FloatField()
    y = serializers.FloatField()
    width = serializers.FloatField()
    height = serializers.FloatField()
    color = serializers.CharField(max_length=64)
    order = serializers.IntegerField(required=False, allow_null=True)


class NoteSerializer(AreaSerializer):
    content = serializers.CharField(allow_blank=True)
    name = None


class CustomTypeFieldSerializer(serializers.Serializer):
    field = serializers.CharField(max_length=255)
    type = serializers.CharField(max_length=255)


class CustomTypeSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=64)
    schema = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    name = serializers.CharField(max_length=255)
    kind = serializers.ChoiceField(choices=["enum", "composite"])
    values = serializers.ListField(child=serializers.CharField(), required=False, allow_null=True)
    fields = CustomTypeFieldSerializer(many=True, required=False, allow_null=True)
    order = serializers.IntegerField(required=False, allow_null=True)


class DiagramFilterSerializer(serializers.Serializer):
    schemaIds = serializers.ListField(child=serializers.CharField(), required=False)
    tableIds = serializers.ListField(child=serializers.CharField(), required=False)


class DiagramAggregateSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=255)
    databaseType = serializers.ChoiceField(choices=DATABASE_TYPES)
    databaseEdition = serializers.ChoiceField(
        choices=DATABASE_EDITIONS, required=False, allow_null=True
    )
    tables = TableSerializer(many=True, required=False)
    relationships = RelationshipSerializer(many=True, required=False)
    dependencies = DependencySerializer(many=True, required=False)
    areas = AreaSerializer(many=True, required=False)
    customTypes = CustomTypeSerializer(many=True, required=False)
    notes = NoteSerializer(many=True, required=False)
    filter = DiagramFilterSerializer(required=False)
    createdAt = serializers.DateTimeField(required=False)
    updatedAt = serializers.DateTimeField(required=False)
    revision = serializers.IntegerField(min_value=1, required=False)

    def validate(self, data):
        all_child_ids = []
        for collection in (
            "tables",
            "areas",
            "relationships",
            "dependencies",
            "customTypes",
            "notes",
        ):
            all_child_ids.extend(item["id"] for item in data.get(collection, []))
        for table in data.get("tables", []):
            all_child_ids.extend(field["id"] for field in table["fields"])
            all_child_ids.extend(index["id"] for index in table["indexes"])
            all_child_ids.extend(check["id"] for check in table.get("checkConstraints") or [])
        if len(all_child_ids) != len(set(all_child_ids)):
            raise serializers.ValidationError(
                {"childIds": "Every child id must be unique within the diagram."}
            )

        self._unique(data.get("tables", []), "id", "tables")
        self._unique(data.get("areas", []), "id", "areas")
        self._unique(data.get("relationships", []), "id", "relationships")
        self._unique(data.get("dependencies", []), "id", "dependencies")
        self._unique(data.get("customTypes", []), "id", "customTypes")
        self._unique(data.get("notes", []), "id", "notes")

        areas = {item["id"] for item in data.get("areas", [])}
        tables = {item["id"]: item for item in data.get("tables", [])}
        fields = {}
        for table in data.get("tables", []):
            self._unique(table["fields"], "id", f"table {table['id']} fields")
            self._unique(table["indexes"], "id", f"table {table['id']} indexes")
            for field in table["fields"]:
                if field["id"] in fields:
                    raise serializers.ValidationError(
                        {"fields": f"Duplicate field id {field['id']} across diagram"}
                    )
                fields[field["id"]] = table["id"]
            parent = table.get("parentAreaId")
            if parent and parent not in areas:
                raise serializers.ValidationError({"parentAreaId": f"Unknown area {parent}"})
            own_fields = {field["id"] for field in table["fields"]}
            for index in table["indexes"]:
                if len(index["fieldIds"]) != len(set(index["fieldIds"])):
                    raise serializers.ValidationError(
                        {"fieldIds": "An index cannot contain a field twice"}
                    )
                if not set(index["fieldIds"]).issubset(own_fields):
                    raise serializers.ValidationError(
                        {"fieldIds": f"Index {index['id']} references another table"}
                    )

        for rel in data.get("relationships", []):
            source, target = rel["sourceTableId"], rel["targetTableId"]
            if source not in tables or target not in tables:
                raise serializers.ValidationError(
                    {"relationships": f"Relationship {rel['id']} references an unknown table"}
                )
            if (
                fields.get(rel["sourceFieldId"]) != source
                or fields.get(rel["targetFieldId"]) != target
            ):
                raise serializers.ValidationError(
                    {"relationships": f"Relationship {rel['id']} field/table mismatch"}
                )

        for dep in data.get("dependencies", []):
            if dep["tableId"] not in tables or dep["dependentTableId"] not in tables:
                raise serializers.ValidationError(
                    {"dependencies": f"Dependency {dep['id']} references an unknown table"}
                )
        return data

    @staticmethod
    def _unique(items, key, label):
        values = [item[key] for item in items]
        if len(values) != len(set(values)):
            raise serializers.ValidationError({label: f"Duplicate {key}"})


class DiagramSummarySerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    databaseType = serializers.CharField()
    databaseEdition = serializers.CharField(allow_null=True)
    createdAt = serializers.DateTimeField()
    updatedAt = serializers.DateTimeField()
    revision = serializers.IntegerField()
