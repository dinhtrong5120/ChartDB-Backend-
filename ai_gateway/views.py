import json

from django.http import StreamingHttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from diagrams.serializers import DATABASE_TYPES

from .services import AIConfigurationError, stream_sql_export, validate_ai_configuration


class SQLExportRequestSerializer(serializers.Serializer):
    sqlScript = serializers.CharField(max_length=2_000_000)
    targetDatabaseType = serializers.ChoiceField(choices=DATABASE_TYPES)


class AIUnavailable(APIException):
    status_code = 503
    default_code = "ai_unavailable"


def sse(event, payload):
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


class SQLExportStreamView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai"

    @extend_schema(request=SQLExportRequestSerializer, responses={(200, "text/event-stream"): str})
    def post(self, request):
        serializer = SQLExportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            validate_ai_configuration()
            chunks = stream_sql_export(data["targetDatabaseType"], data["sqlScript"])
        except AIConfigurationError as exc:
            raise AIUnavailable(str(exc)) from exc

        def events():
            try:
                for chunk in chunks:
                    yield sse("delta", {"text": chunk})
                yield sse("done", {})
            except Exception:
                yield sse("error", {"code": "provider_error", "message": "AI provider failed."})

        response = StreamingHttpResponse(events(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response
