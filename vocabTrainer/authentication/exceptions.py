from rest_framework.exceptions import APIException

class EmailAlreadyExistsException(APIException):
    status_code = 400
    default_code = "email_exists"

    def __init__(self, detail=None):
        if detail is None:
            detail = "Ein Nutzer mit dieser Email existiert bereits."
        super().__init__(detail=detail)

class UsernameAlreadyExistsException(APIException):
    status_code = 400
    default_code = "username_exists"

    def __init__(self, detail=None):
        if detail is None:
            detail = "Ein Nutzer mit diesem Nutzernamen existiert bereits."
        super().__init__(detail=detail)

class UserNotFoundException(APIException):
    status_code = 404
    default_code = "user_not_found"

    def __init__(self, detail=None):
        if detail is None:
            detail = "Der eingegebene Nutzer existiert nicht."
        super().__init__(detail=detail)

class InactiveUserException(APIException):
    status_code = 403
    default_code = "user_inactive"

    def __init__(self, detail=None):
        if detail is None:
            detail = "Der eingegebene Nutzer ist inaktiv."
        super().__init__(detail=detail)
