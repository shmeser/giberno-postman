from enum import IntEnum


class RESTErrors(IntEnum):
    BAD_REQUEST = 400
    NOT_AUTHORIZED = 401
    ACCESS_DENIED = 403
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500


class SocketErrors(IntEnum):
    USER_NOT_FOUND = 1004
