class BaseServerException(Exception):

    def __init__(self, detail, status_code, message):
        super().__init__(message)
        self.detail = detail
        self.status_code = status_code


class EntityDoesNotExistException(BaseServerException):

    def __init__(self):
        super().__init__(detail='entity', status_code=404, message='Entity not found')


class ForbiddenException(BaseServerException):

    def __init__(self):
        super().__init__(detail='forbidden', status_code=403, message='Permission denied')


class InternalIOException(BaseServerException):
    def __init__(self):
        super().__init__(detail='In/Out internal server exception', status_code=404,
                         message='In/Out internal server exception')
