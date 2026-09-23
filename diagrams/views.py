from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import ConflictError

from .models import Diagram
from .serializers import DiagramAggregateSerializer, DiagramSummarySerializer
from .services import aggregate_to_dict, create_aggregate, replace_aggregate, summary_to_dict


def diagram_queryset():
    return Diagram.objects.prefetch_related(
        "areas", "tables__fields", "tables__indexes__index_fields__field",
        "tables__check_constraints", "relationships", "dependencies", "notes",
        "custom_types__values", "custom_types__fields",
    )


class DiagramListCreateView(APIView):
    @extend_schema(responses=DiagramSummarySerializer(many=True))
    def get(self, request):
        return Response([summary_to_dict(diagram) for diagram in Diagram.objects.all()])

    @extend_schema(request=DiagramAggregateSerializer, responses={201: DiagramAggregateSerializer})
    def post(self, request):
        serializer = DiagramAggregateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if "revision" in serializer.validated_data:
            raise ValidationError({"revision": "Do not send revision when creating a diagram."})
        try:
            diagram = create_aggregate(serializer.validated_data)
        except IntegrityError as exc:
            raise ConflictError("A diagram or child with this ID already exists.") from exc
        return Response(aggregate_to_dict(diagram), status=status.HTTP_201_CREATED)


class DiagramDetailView(APIView):
    @extend_schema(responses=DiagramAggregateSerializer)
    def get(self, request, diagram_id):
        diagram = get_object_or_404(diagram_queryset(), external_id=diagram_id)
        return Response(aggregate_to_dict(diagram))

    @extend_schema(request=DiagramAggregateSerializer, responses=DiagramAggregateSerializer)
    def put(self, request, diagram_id):
        serializer = DiagramAggregateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if data["id"] != diagram_id:
            raise ValidationError({"id": "Body ID must match URL ID."})
        if "revision" not in data:
            raise ValidationError({"revision": "This field is required when saving."})
        with transaction.atomic():
            diagram = get_object_or_404(Diagram.objects.select_for_update(), external_id=diagram_id)
            if data["revision"] != diagram.revision:
                raise ConflictError(
                    f"Revision {data['revision']} is stale; current revision is {diagram.revision}."
                )
            diagram.revision += 1
            replace_aggregate(diagram, data)
        diagram = get_object_or_404(diagram_queryset(), external_id=diagram_id)
        return Response(aggregate_to_dict(diagram))

    @extend_schema(request={"application/json": {"type": "object", "required": ["revision"], "properties": {"revision": {"type": "integer"}}}}, responses={204: None})
    def delete(self, request, diagram_id):
        revision = request.data.get("revision") if isinstance(request.data, dict) else None
        if not isinstance(revision, int):
            raise ValidationError({"revision": "An integer revision is required."})
        with transaction.atomic():
            diagram = get_object_or_404(Diagram.objects.select_for_update(), external_id=diagram_id)
            if revision != diagram.revision:
                raise ConflictError(
                    f"Revision {revision} is stale; current revision is {diagram.revision}."
                )
            diagram.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

