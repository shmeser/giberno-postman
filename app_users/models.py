import uuid as uuid

from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField

from app_geo.models import Language, Country, City
from app_media.models import MediaModel
from app_users.enums import Gender, Status, AccountType, LanguageProficiency, NotificationType, NotificationAction, \
    Education, DocumentType, NotificationIcon
from backend.models import BaseModel
from backend.utils import choices
from giberno import settings


class UserProfile(AbstractUser, BaseModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    username = models.CharField(unique=True, max_length=255, null=True, blank=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=16, blank=True, null=True)
    show_phone = models.BooleanField(default=False, verbose_name='Показывать номер телефона')

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
    nationalities = models.ManyToManyField(Country, through='UserNationality', blank=True, related_name='nationalities')
    cities = models.ManyToManyField(City, through='UserCity', blank=True, related_name='cities')

    reg_reference = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        verbose_name='Приглашение на регистрацию от', on_delete=models.SET_NULL
    )
    reg_reference_code = models.CharField(max_length=255, null=True, blank=True, verbose_name='')

    terms_accepted = models.BooleanField(default=False, verbose_name='Правила использования приняты')
    policy_accepted = models.BooleanField(default=False, verbose_name='Политика конфиденциальности принята')
    agreement_accepted = models.BooleanField(default=False, verbose_name='Пользовательское соглашение принято')

    verified = models.BooleanField(default=False, verbose_name='Профиль проверен')
    bonus_balance = models.PositiveIntegerField(default=0, verbose_name='Очки славы')
    favourite_vacancies_count = models.PositiveIntegerField(default=0, verbose_name='Количество избранных вакансий')

    media = GenericRelation(MediaModel, object_id_field='owner_id', content_type_field='owner_ct')

    fb_link = models.CharField(max_length=255, null=True, blank=True, verbose_name='Ссылка на профиль в Facebook')
    vk_link = models.CharField(max_length=255, null=True, blank=True, verbose_name='Ссылка на профиль в ВКонтанте')
    instagram_link = models.CharField(
        max_length=255, null=True, blank=True, verbose_name='Ссылка на профиль в Intsagram'
    )

    education = models.PositiveIntegerField(choices=choices(Education), null=True, blank=True,
                                            verbose_name='Образование')

    # использовано в формате app_label.ModelName из - за циркулярного импорта
    distributors = models.ManyToManyField(to='app_market.Distributor', blank=True, verbose_name='Торговая сеть',
                                          related_name='distributors')

    location = models.PointField(srid=settings.SRID, blank=True, null=True, verbose_name='Геопозиция')

    @property
    def is_manager(self):
        return self.account_type == AccountType.MANAGER

    @property
    def is_security(self):
        return self.account_type == AccountType.SECURITY

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


class UserCity(BaseModel):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.CASCADE)

    class Meta:
        db_table = 'app_users__profile_city'
        verbose_name = 'Город пользователя'
        verbose_name_plural = 'Города пользователей'


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
    is_for_reg = models.BooleanField(default=False, verbose_name='Использовался для регистрации')

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


class Notification(BaseModel):
    user = models.ForeignKey(UserProfile, null=True, blank=True, on_delete=models.SET_NULL)

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    subject_id = models.IntegerField(blank=True, null=True, verbose_name='ID сущности в уведомлении')
    title = models.CharField(max_length=255, blank=True, null=True, verbose_name='Заголовок')
    message = models.CharField(max_length=255, blank=True, null=True, verbose_name='Сообщение')

    type = models.IntegerField(
        choices=choices(NotificationType), default=NotificationType.SYSTEM, verbose_name='Тип отправителя уведомления'
    )

    action = models.IntegerField(
        choices=choices(NotificationAction), default=NotificationAction.APP, verbose_name='Открываемый экран'
    )
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='Время прочтения')

    push_tokens_android = ArrayField(models.CharField(max_length=1024), blank=True, null=True)
    push_tokens_ios = ArrayField(models.CharField(max_length=1024), blank=True, null=True)

    icon_type = models.IntegerField(
        choices=choices(NotificationIcon), default=NotificationIcon.DEFAULT, verbose_name='Тип иконки'
    )

    def __str__(self):
        return f'{self.title}'

    class Meta:
        db_table = 'app_users__notifications'
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'


class NotificationsSettings(BaseModel):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, unique=True)
    enabled_types = ArrayField(models.IntegerField(choices=choices(NotificationType)), blank=True, null=True)

    def __str__(self):
        return f'{self.user.username}'

    class Meta:
        db_table = 'app_users__notifications_settings'
        verbose_name = 'Настройки уведомлений пользователя'
        verbose_name_plural = 'Настройки уведомлений пользователей'


class UserCareer(BaseModel):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    work_place = models.CharField(max_length=128, blank=True, null=True)
    position = models.CharField(max_length=128, blank=True, null=True)

    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)

    year_start = models.PositiveIntegerField(null=True, blank=True)
    year_end = models.PositiveIntegerField(null=True, blank=True)

    is_working_now = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name} - {self.work_place} {self.position}'

    class Meta:
        db_table = 'app_users__profile_career'
        verbose_name = 'Карьера пользователя'
        verbose_name_plural = 'Картера пользователей'


class Document(BaseModel):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    type = models.IntegerField(choices=choices(DocumentType), default=DocumentType.OTHER)
    series = models.CharField(max_length=128, blank=True, null=True, verbose_name='Серия')
    number = models.CharField(max_length=128, blank=True, null=True, verbose_name='Номер')
    category = models.CharField(max_length=128, blank=True, null=True, verbose_name='Категория')
    department_code = models.CharField(max_length=128, blank=True, null=True, verbose_name='Код подразделения')
    issue_place = models.CharField(max_length=128, blank=True, null=True, verbose_name='Место выдачи')
    issue_date = models.DateTimeField(null=True, blank=True, verbose_name='Дата выдачи')
    expiration_date = models.DateTimeField(null=True, blank=True, verbose_name='Действителен до')

    media = GenericRelation(MediaModel, object_id_field='owner_id', content_type_field='owner_ct')

    def __str__(self):
        return f'{self.user.username}'

    class Meta:
        db_table = 'app_users__documents'
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'
