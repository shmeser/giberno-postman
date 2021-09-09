from django.db import models


class NalogUserStatus(models.IntegerChoices):
    NOT_SELF_EMPLOYED = 0, 'Пользователь не является самозанятым'
    NOT_ATTACHED_TO_A_PARTNER = 1, 'Пользователь является самозанятым, но не привязан к партнеру'
    ATTACHED_TO_A_PARTNER = 2, 'Пользователь самозанятый и привязан к партнеру'
    UNKNOWN = 3, 'Неизвестный статус, возможна ошибка в данных'
