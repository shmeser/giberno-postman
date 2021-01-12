from backend.enums import IntEnumM


class Gender(IntEnumM):
    FEMALE = 0
    MALE = 1


class Status(IntEnumM):
    NEW = 0
    ACTIVE = 1
    BLOCKED = 2


class AccountType(IntEnumM):
    ADMIN = 0
    MANAGER = 1
    SECURITY = 2
    SELF_EMPLOYED = 3


class LanguageProficiency(IntEnumM):
    BEGINNER = 0
    ELEMENTARY = 1
    INTERMEDIATE = 2
    UPPER_INTERMEDIATE = 3
    ADVANCED = 4
    PROFICIENCY = 5
