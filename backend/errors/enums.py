from enum import IntEnum


class RESTErrors(IntEnum):
    NOT_AUTHORIZED = 401
    BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500
    ACCESS_DENIED = 403
    NOT_FOUND = 404


class SocketErrors(IntEnum):
    USER_NOT_FOUND = 1004
