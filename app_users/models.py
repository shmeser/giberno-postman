import uuid as uuid

from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models

from app_geo.models import Language, Country
from app_media.models import MediaModel
from app_users.enums import Gender, Status, AccountType, LanguageProficiency
from backend.models import BaseModel
from backend.utils import choices


class UserProfile(AbstractUser, BaseModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    username = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    phone = models.CharField(max_length=16, blank=True, null=True)

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

    languages = models.ManyToManyField(Language, through='UserLanguage', blank=True)
    nationalities = models.ManyToManyField(Country, through='UserNationality', blank=True)

    reg_reference = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        verbose_name='Приглашение на регистрацию от', on_delete=models.SET_NULL
    )
    reg_reference_code = models.CharField(max_length=255, null=True, blank=True)

    policy_accepted = models.BooleanField(default=False)
    agreement_accepted = models.BooleanField(default=False)

    def __str__(self):
        return f'ID:{self.id} - {self.username} {self.first_name} {self.middle_name} {self.middle_name}'

    class Meta:
        db_table = 'app_users__profiles'
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'


class UserLanguage(BaseModel):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    proficiency = models.PositiveIntegerField(
        choices=choices(LanguageProficiency), default=LanguageProficiency.BEGINNER,
        verbose_name='Уровень владения языком'
    )

    class Meta:
        db_table = 'app_users__profile_language'
        verbose_name = 'Язык пользователя'
        verbose_name_plural = 'Языки пользователей'


class UserNationality(BaseModel):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    class Meta:
        db_table = 'app_users__profile_nationality'
        verbose_name = 'Гражданство пользователя'
        verbose_name_plural = 'Гражданство пользователей'


class SocialModel(BaseModel):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True)
    type = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255, blank=False, null=True)
    last_name = models.CharField(max_length=255, blank=False, null=True)
    middle_name = models.CharField(max_length=255, blank=False, null=True)
    username = models.CharField(max_length=255, blank=False, null=True)
    phone = models.CharField(max_length=255, blank=False, null=True)
    email = models.CharField(max_length=255, blank=False, null=True)
    firebase_id = models.CharField(max_length=255, blank=False, null=True)
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
