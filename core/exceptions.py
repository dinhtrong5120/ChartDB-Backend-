from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class ConflictError(APIException):
    status_code = 409
    default_code = "conflict"
    default_detail = "The resource has changed."


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    code = getattr(exc, "default_code", "error")
    details = response.data
    message = str(getattr(exc, "detail", "Request failed"))
    if isinstance(details, dict) and "detail" in details:
        message = str(details["detail"])
    response.data = {"code": code, "message": message, "details": details}
    return response

