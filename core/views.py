from django.db import connection
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView


class LiveView(APIView):
    @extend_schema(responses=inline_serializer("Health", {"status": serializers.CharField()}))
    def get(self, request):
        return Response({"status": "ok"})


class ReadyView(APIView):
    @extend_schema(responses=inline_serializer("Readiness", {"status": serializers.CharField()}))
    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return Response({"status": "ready"})
