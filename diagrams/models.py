from django.db import models


class Diagram(models.Model):
    external_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    database_type = models.CharField(max_length=32)
    database_edition = models.CharField(max_length=64, null=True, blank=True)
    revision = models.PositiveBigIntegerField(default=1)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        ordering = ["-updated_at", "external_id"]


class PositionedChild(models.Model):
    external_id = models.CharField(max_length=64)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True


class Area(PositionedChild):
    diagram = models.ForeignKey(Diagram, related_name="areas", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    x = models.FloatField()
    y = models.FloatField()
    width = models.FloatField()
    height = models.FloatField()
    color = models.CharField(max_length=64)
    display_order = models.IntegerField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["diagram", "external_id"], name="unique_area_id")]
        ordering = ["position"]


class DBTable(PositionedChild):
    diagram = models.ForeignKey(Diagram, related_name="tables", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    schema_name = models.CharField(max_length=255, null=True, blank=True)
    x = models.FloatField()
    y = models.FloatField()
    color = models.CharField(max_length=64)
    is_view = models.BooleanField(default=False)
    is_materialized_view = models.BooleanField(null=True, blank=True)
    client_created_at = models.BigIntegerField()
    width = models.FloatField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    display_order = models.IntegerField(null=True, blank=True)
    expanded = models.BooleanField(null=True, blank=True)
    parent_area = models.ForeignKey(Area, null=True, blank=True, related_name="tables", on_delete=models.SET_NULL)
    check_constraints_defined = models.BooleanField(default=False)
    check_constraints_null = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["diagram", "external_id"], name="unique_table_id")]
        ordering = ["position"]


class DBField(PositionedChild):
    table = models.ForeignKey(DBTable, related_name="fields", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    type_id = models.CharField(max_length=255)
    type_name = models.CharField(max_length=255)
    primary_key = models.BooleanField(default=False)
    unique = models.BooleanField(default=False)
    nullable = models.BooleanField(default=False)
    increment = models.BooleanField(null=True, blank=True)
    is_array = models.BooleanField(null=True, blank=True)
    client_created_at = models.BigIntegerField()
    character_maximum_length = models.CharField(max_length=64, null=True, blank=True)
    precision = models.IntegerField(null=True, blank=True)
    scale = models.IntegerField(null=True, blank=True)
    default_value = models.TextField(null=True, blank=True)
    collation = models.CharField(max_length=255, null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    check_expression = models.TextField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["table", "external_id"], name="unique_field_id")]
        ordering = ["position"]


class DBIndex(PositionedChild):
    table = models.ForeignKey(DBTable, related_name="indexes", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    unique = models.BooleanField(default=False)
    client_created_at = models.BigIntegerField()
    index_type = models.CharField(max_length=32, null=True, blank=True)
    is_primary_key = models.BooleanField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["table", "external_id"], name="unique_index_id")]
        ordering = ["position"]


class IndexField(models.Model):
    index = models.ForeignKey(DBIndex, related_name="index_fields", on_delete=models.CASCADE)
    field = models.ForeignKey(DBField, related_name="index_memberships", on_delete=models.CASCADE)
    position = models.PositiveIntegerField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["index", "field"], name="unique_index_field")]
        ordering = ["position"]


class CheckConstraint(PositionedChild):
    table = models.ForeignKey(DBTable, related_name="check_constraints", on_delete=models.CASCADE)
    expression = models.TextField()
    client_created_at = models.BigIntegerField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["table", "external_id"], name="unique_check_id")]
        ordering = ["position"]


class Relationship(PositionedChild):
    diagram = models.ForeignKey(Diagram, related_name="relationships", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    source_schema = models.CharField(max_length=255, null=True, blank=True)
    source_table = models.ForeignKey(DBTable, related_name="source_relationships", on_delete=models.CASCADE)
    target_schema = models.CharField(max_length=255, null=True, blank=True)
    target_table = models.ForeignKey(DBTable, related_name="target_relationships", on_delete=models.CASCADE)
    source_field = models.ForeignKey(DBField, related_name="source_relationships", on_delete=models.CASCADE)
    target_field = models.ForeignKey(DBField, related_name="target_relationships", on_delete=models.CASCADE)
    source_cardinality = models.CharField(max_length=8)
    target_cardinality = models.CharField(max_length=8)
    client_created_at = models.BigIntegerField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["diagram", "external_id"], name="unique_relationship_id")]
        ordering = ["position"]


class Dependency(PositionedChild):
    diagram = models.ForeignKey(Diagram, related_name="dependencies", on_delete=models.CASCADE)
    schema_name = models.CharField(max_length=255, null=True, blank=True)
    table = models.ForeignKey(DBTable, related_name="dependencies", on_delete=models.CASCADE)
    dependent_schema = models.CharField(max_length=255, null=True, blank=True)
    dependent_table = models.ForeignKey(DBTable, related_name="dependent_on", on_delete=models.CASCADE)
    client_created_at = models.BigIntegerField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["diagram", "external_id"], name="unique_dependency_id")]
        ordering = ["position"]


class Note(PositionedChild):
    diagram = models.ForeignKey(Diagram, related_name="notes", on_delete=models.CASCADE)
    content = models.TextField()
    x = models.FloatField()
    y = models.FloatField()
    width = models.FloatField()
    height = models.FloatField()
    color = models.CharField(max_length=64)
    display_order = models.IntegerField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["diagram", "external_id"], name="unique_note_id")]
        ordering = ["position"]


class CustomType(PositionedChild):
    diagram = models.ForeignKey(Diagram, related_name="custom_types", on_delete=models.CASCADE)
    schema_name = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255)
    kind = models.CharField(max_length=16)
    display_order = models.IntegerField(null=True, blank=True)
    values_defined = models.BooleanField(default=False)
    values_null = models.BooleanField(default=False)
    fields_defined = models.BooleanField(default=False)
    fields_null = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["diagram", "external_id"], name="unique_custom_type_id")]
        ordering = ["position"]


class CustomTypeValue(models.Model):
    custom_type = models.ForeignKey(CustomType, related_name="values", on_delete=models.CASCADE)
    value = models.TextField()
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ["position"]


class CustomTypeField(models.Model):
    custom_type = models.ForeignKey(CustomType, related_name="fields", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    type_name = models.CharField(max_length=255)
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ["position"]


class DiagramFilter(models.Model):
    diagram = models.OneToOneField(Diagram, related_name="diagram_filter", on_delete=models.CASCADE)
    schema_ids_defined = models.BooleanField(default=False)
    schema_ids = models.JSONField(default=list)
    table_ids_defined = models.BooleanField(default=False)
    table_ids = models.JSONField(default=list)
