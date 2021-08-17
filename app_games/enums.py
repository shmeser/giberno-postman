from backend.enums import IntEnumM


class Grade(IntEnumM):
    DEFAULT = 1
    EPIC = 2
    LEGENDARY = 3


class TaskPeriod(IntEnumM):
    DAILY = 1
    WEEKLY = 2
    SUPER = 3


class TaskType(IntEnumM):
    COMMON = 1
    PROMOTION = 2


class TaskKind(IntEnumM):
    # Вид задачи
    OPEN_APP = 1
    COMPLETE_SHIFT = 2
