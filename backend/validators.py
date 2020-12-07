from backend.errors.enums import Errors
from backend.errors.http_exception import HttpException


class ValidatePhotosCount:
    """
    проверка на кол-во переданных фотографий.
    """
    def __init__(self, max_photos_count):
        self.max = max_photos_count

    def __call__(self, photos_count):
        if len(photos_count) > self.max or not photos_count:
            raise HttpException(detail=Errors.BAD_REQUEST.name,
                                status_code=Errors.BAD_REQUEST)
