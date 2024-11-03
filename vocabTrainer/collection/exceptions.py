from rest_framework.exceptions import APIException


class CollectionNotFoundException(APIException):
    status_code = 404
    default_code = "colection_not_found"

    def __init__(self, detail=None):
        if detail is None:
            detail = "Die Sammlung wurde nicht gefunden."
        super().__init__(detail=detail)

class WordCombinationAlreadyExistsException(APIException):
    status_code = 409
    default_detail = "This word combination already exists in the collection."
    default_code = "word_combination_already_exists"

    def __init__(self, combination_id=None):
        if combination_id:
            detail = f"Combination with ID {combination_id} already exists in the collection."
        else:
            detail = self.default_detail
        super().__init__(detail=detail)