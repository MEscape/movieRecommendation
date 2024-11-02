from rest_framework.exceptions import APIException

class WordCombinationFormatException(APIException):
    status_code = 400
    default_code = "word_combination_format"

    def __init__(self, detail=None):
        if detail is None:
            detail = "Wort-Kombination hat eine falsche Struktur."
        super().__init__(detail=detail)

class WordCombinationExistsException(APIException):
    status_code = 400
    default_code = "word_combination_exists"

    def __init__(self, detail=None):
        if detail is None:
            detail = "Die Wort-Kombination existiert bereits."
        super().__init__(detail=detail)

class WordCombinationNotFoundException(APIException):
    status_code = 404
    default_code = "word_combination_not_found"

    def __init__(self, detail=None):
        if detail is None:
            detail = "Die Wort-Kombination wurde nicht gefunden."
        super().__init__(detail=detail)

class WordCombinationIntegrityException(APIException):
    status_code = 409
    default_code = "word_combination_integrity_error"

    def __init__(self, detail=None):
        if detail is None:
            detail = "Ein Integritätsfehler ist aufgetreten. Die Wort-Kombination konnte nicht gelöscht oder aktualisiert werden."
        super().__init__(detail=detail)