from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .services import SourceDatabaseUnavailable, inspect_mysql


class IntrospectionUnavailable(APIException):
    status_code = 503
    default_code = "source_database_unavailable"


class SourceDatabaseIntrospectionView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "introspection"

    @extend_schema(request=None, responses={200: dict})
    def post(self, request):
        try:
            return Response(inspect_mysql())
        except SourceDatabaseUnavailable as exc:
            raise IntrospectionUnavailable(str(exc)) from exc

