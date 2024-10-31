# authentication/exceptions.py
from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # If the response is None, it means the error is not handled by DRF
    if response is None:
        return {
            "status": 500,  # Internal Server Error
            "message": "An unexpected error occurred.",
            "data": None,
        }

    # Customize the response data
    response.data = {
        "status": response.status_code,  # Set status to the HTTP status code
        "message": response.data.get("detail", "Something went wrong."),
        "data": None,
    }

    return response
