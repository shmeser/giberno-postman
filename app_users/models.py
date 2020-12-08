import uuid as uuid

from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models

from app_users.enums import Gender, Status, AccountType
from backend.models import BaseModel
from backend.utils import choices


class UserProfile(AbstractUser, BaseModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    username = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True, blank=True)
    phone = models.CharField(max_length=16, blank=True)

    first_name = models.CharField(max_length=255, null=True, blank=True)
    middle_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)

    gender = models.IntegerField(
        choices=choices(Gender),
        default=None,
        blank=True,
        null=True
    )

    birth_date = models.DateTimeField(blank=True, null=True)

    account_type = models.IntegerField(choices=choices(AccountType), default=AccountType.ADMIN)
    status = models.IntegerField(choices=choices(Status), default=Status.ACTIVE)

    # country = models.ManyToManyField(Country, null=True, blank=True, related_name='countries')
    # language = models.ManyToManyField(Language, null=True, blank=True, related_name='languages')

    def __str__(self):
        return f'ID:{self.id} - {self.username} {self.first_name} {self.middle_name} {self.middle_name}'

    class Meta:
        db_table = 'app_users__profiles'
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'
