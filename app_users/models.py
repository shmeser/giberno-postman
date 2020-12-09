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
    email = models.EmailField(unique=True, blank=True, null=True)
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

    reg_reference = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        verbose_name='Приглашение на регистрацию от', on_delete=models.SET_NULL
    )
    reg_reference_code = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f'ID:{self.id} - {self.username} {self.first_name} {self.middle_name} {self.middle_name}'

    class Meta:
        db_table = 'app_users__profiles'
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'


class SocialModel(BaseModel):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True)
    type = models.CharField(max_length=255)
    phone = models.CharField(max_length=255, blank=False, null=True)
    email = models.CharField(max_length=255, blank=False, null=True)
    social_id = models.CharField(max_length=255, blank=False, null=True)
    access_token = models.CharField(max_length=2048, blank=False, null=True)
    access_token_expiration = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.social_id} - {self.type}'

    class Meta:
        db_table = 'app_users__socials'
        verbose_name = 'Способ авторизации пользователя'
        verbose_name_plural = 'Способы авторизаций пользователей'


class JwtToken(BaseModel):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=False, blank=False)
    access_token = models.CharField(max_length=255, blank=False, null=False)
    refresh_token = models.CharField(max_length=255, blank=False, null=False)

    app_version = models.CharField(max_length=128, blank=True, null=True)
    platform_name = models.CharField(max_length=128, blank=True, null=True)
    vendor = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        return self.access_token

    class Meta:
        db_table = 'app_users__jwt_tokens'
        verbose_name = 'JWT токен'
        verbose_name_plural = 'JWT токены'