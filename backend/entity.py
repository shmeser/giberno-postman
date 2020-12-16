from enum import Enum


class BaseEntity:
    def __init__(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_kwargs(self):
        return {}


class Pagination(BaseEntity):
    limit: int
    offset: int

    def __init__(self, **kwargs):
        self.limit = 10
        self.offset = 0
        super().__init__(**kwargs)


class Error(BaseEntity):
    code: str
    detail: str

    def __init__(self, error_enum: Enum = None, **kwargs):
        self.code = error_enum.name if error_enum else ''
        self.detail = error_enum.value if error_enum else ''
        super().__init__(**kwargs)

    def __iter__(self):
        for attr in dir(self):
            if not attr.startswith(('__', 'get_')):
                yield attr, getattr(self, attr, '')


class File(BaseEntity):
    def __init__(self, **kwargs):
        self.owner_id = None
        self.owner_content_type_id = None
        self.owner_content_type = None

        self.title = None

        self.mime_type = None

        self.file = None
        self.preview = None
        self.format = None
        self.type = None

        self.width = None
        self.height = None
        self.duration = None
        self.size = None

        super().__init__(**kwargs)

    def __iter__(self):
        for attr in dir(self):
            if not attr.startswith(('__', 'get_')):
                yield attr, getattr(self, attr, '')
