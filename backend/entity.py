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
