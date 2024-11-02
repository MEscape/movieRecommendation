from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError, APIException
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        response_data = {
            "status_code": response.status_code,
            "detail": response.data["detail"] if isinstance(response.data, dict) and "detail" in response.data else response.data,
        }

        if hasattr(exc, 'default_code'):
            response_data["code"] = exc.default_code
        return Response(response_data, status=response.status_code)

    if isinstance(exc, ValidationError):
        return Response({
            "status_code": 400,
            "detail": exc.detail,
            "code": "validation_error"
        }, status=400)

    if isinstance(exc, APIException):
        return Response({
            "status_code": exc.status_code,
            "detail": str(exc.detail),
            "code": exc.default_code,
        }, status=exc.status_code)

    return Response({
        "status_code": 500,
        "detail": str(exc)
    }, status=500)
