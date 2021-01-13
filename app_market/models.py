import uuid as uuid

from dateutil.rrule import MONTHLY, WEEKLY, DAILY
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField

from app_market.enums import Currency, TransactionType, TransactionStatus, VacancyEmployment, WorkExperience, \
    ShiftStatus
from app_media.enums import MediaType
from app_users.models import UserProfile
from backend.models import BaseModel
from backend.utils import choices
from giberno import settings

FREQUENCY_CHOICES = (
    (DAILY, "Ежедневно"),
    (WEEKLY, "Еженедельно"),
    (MONTHLY, "Ежемесячно")
)

REQUIRED_DOCS = (
    ('Пасспорт', MediaType.PASSPORT),
    ('ИНН', MediaType.INN),
    ('СНИЛС', MediaType.SNILS),
    ('Медкнижка', MediaType.MEDICAL_BOOK),
    ('Водительское удостоверение', MediaType.DRIVER_LICENCE),
)


class Distributor(BaseModel):
    title = models.CharField(max_length=128, null=True, blank=True)
    category = models.CharField(max_length=128, null=True, blank=True)
    description = models.CharField(max_length=2048, null=True, blank=True)

    required_docs = ArrayField(models.PositiveIntegerField(choices=REQUIRED_DOCS))

    def __str__(self):
        return f'{self.title}'

    class Meta:
        db_table = 'app_market__distributors'
        verbose_name = 'Торговая сеть'
        verbose_name_plural = 'Торговые сети'


class Shop(BaseModel):
    distributor = models.ForeignKey(Distributor, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=1024, null=True, blank=True)
    description = models.CharField(max_length=2048, null=True, blank=True)

    location = models.PointField(srid=settings.SRID, blank=True, null=True, verbose_name='Геопозиция')
    address = models.CharField(max_length=1024, null=True, blank=True, verbose_name='Адрес')

    is_partner = models.BooleanField(default=False, verbose_name='Является партнером')

    discount = models.PositiveIntegerField(null=True, blank=True, verbose_name='Базовый размер скидки')
    discount_multiplier = models.PositiveIntegerField(null=True, blank=True, verbose_name='Множитель размера скидки')
    discount_terms = models.CharField(max_length=1024, null=True, blank=True, verbose_name='Условия получения')
    discount_description = models.CharField(max_length=1024, null=True, blank=True, verbose_name='Описание услуги')

    def __str__(self):
        return f'{self.title}'

    class Meta:
        db_table = 'app_market__shops'
        verbose_name = 'Магазин'
        verbose_name_plural = 'Магазины'


class Vacancy(BaseModel):
    title = models.CharField(max_length=1024, null=True, blank=True)
    description = models.CharField(max_length=2048, null=True, blank=True)

    requirements = models.CharField(max_length=1024, null=True, blank=True, verbose_name='Требования')

    required_experience = ArrayField(
        models.PositiveIntegerField(choices(WorkExperience), default=WorkExperience.NO),
        null=True, blank=True, verbose_name='Требуемый опыт'
    )

    required_docs = ArrayField(models.PositiveIntegerField(choices=REQUIRED_DOCS), verbose_name='Документы')

    features = models.CharField(max_length=1024, null=True, blank=True, verbose_name='Бонусы и привилегии')

    price = models.PositiveIntegerField(null=True, blank=True, verbose_name='Ставка за час')
    currency = models.PositiveIntegerField(choices=choices(Currency), default=Currency.RUB, verbose_name='Валюта')

    employment = models.PositiveIntegerField(
        choices=choices(VacancyEmployment), default=VacancyEmployment.PARTIAL, verbose_name='Занятость'
    )

    radius = models.PositiveIntegerField(null=True, blank=True, verbose_name='Максимальное расстояние от места работы')

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.title}'

    class Meta:
        db_table = 'app_market__vacancies'
        verbose_name = 'Вакансия'
        verbose_name_plural = 'Вакансии'


class Shift(BaseModel):
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)

    price = models.PositiveIntegerField(null=True, blank=True, verbose_name='Ставка за час')
    currency = models.PositiveIntegerField(choices=choices(Currency), default=Currency.RUB, verbose_name='Валюта')

    employees_count = models.PositiveIntegerField(default=0, verbose_name='Число работников')
    max_employees_count = models.PositiveIntegerField(default=1, verbose_name='Максимальное число работников')

    time_start = models.TimeField(null=True, blank=True, verbose_name='Время начала смены')
    time_end = models.TimeField(null=True, blank=True, verbose_name='Время окончания смены')

    date_start = models.DateField(null=True, blank=True, verbose_name='Дата начала расписания')
    date_end = models.DateField(null=True, blank=True, verbose_name='Дата окончания расписания')

    frequency = models.PositiveIntegerField(choices=FREQUENCY_CHOICES, verbose_name='Интервал выполнения')

    by_weekday = ArrayField(models.PositiveIntegerField(), size=7, blank=True, null=True, verbose_name='Дни недели')
    by_monthday = ArrayField(models.PositiveIntegerField(), size=31, blank=True, null=True, verbose_name='Дни месяца')
    by_month = ArrayField(models.PositiveIntegerField(), size=31, blank=True, null=True, verbose_name='Месяцы')

    generated_active_dates = ArrayField(models.DateField(), blank=True, null=True, verbose_name='Даты активности смены')

    def __str__(self):
        return f'{self.id}'

    def save(self, *args, **kwargs):
        # TODO добавить генерацию списка активных дат
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'app_market__shifts'
        verbose_name = 'Рабочая смена'
        verbose_name_plural = 'Рабочие смены'


class UserShift(BaseModel):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)

    real_time_start = models.DateTimeField(null=True, blank=True)
    real_time_end = models.DateTimeField(null=True, blank=True)

    status = models.PositiveIntegerField(choices=choices(ShiftStatus), default=ShiftStatus.INITIAL)

    qr_code = models.TextField(null=True, blank=True, verbose_name='QR код')
    qr_code_gen_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.id}'

    class Meta:
        db_table = 'app_market__shift_user'
        verbose_name = 'Смена пользователя'
        verbose_name_plural = 'Смены пользователей'


class Coupon(BaseModel):
    code = models.CharField(max_length=64, null=True, blank=True, unique=True)
    date = models.DateTimeField(null=True, blank=True, verbose_name='Дата получения пользователем')

    discount_amount = models.PositiveIntegerField(null=True, blank=True, verbose_name='Размер скидки')
    discount_terms = models.CharField(max_length=1024, null=True, blank=True, verbose_name='Условия получения')
    discount_description = models.CharField(max_length=1024, null=True, blank=True, verbose_name='Описание услуги')

    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    shop = models.ForeignKey(Shop, on_delete=models.SET_NULL, null=True, blank=True)
    distributor = models.ForeignKey(Distributor, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'{self.code}'

    class Meta:
        db_table = 'app_market__coupons'
        verbose_name = 'Купон'
        verbose_name_plural = 'Купоны'


class Order(BaseModel):
    description = models.CharField(max_length=1024, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    terms_accepted = models.BooleanField(default=False)

    user = models.ForeignKey(UserProfile, blank=True, null=True, on_delete=models.SET_NULL)
    coupon = models.ForeignKey(Coupon, blank=True, null=True, on_delete=models.SET_NULL)
    transaction = models.ForeignKey('Transaction', blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f'{self.email}'

    class Meta:
        db_table = 'app_market__orders'
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'


class Transaction(BaseModel):
    amount = models.PositiveIntegerField(default=0, verbose_name='Сумма')
    exchange_rate = models.FloatField(default=1, verbose_name='Коэффициент обмена')
    type = models.PositiveIntegerField(
        choices=choices(TransactionType), default=TransactionType.TRANSFER, verbose_name='Тип транзакции'
    )
    status = models.PositiveIntegerField(
        choices=choices(TransactionStatus), default=TransactionStatus.CREATED, verbose_name='Статус транзакции'
    )

    from_currency = models.PositiveIntegerField(
        choices=choices(Currency), default=Currency.BONUS, verbose_name='Исходая валюта'
    )
    to_currency = models.PositiveIntegerField(
        choices=choices(Currency), default=Currency.BONUS, verbose_name='Целевая валюта'
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    from_id = models.PositiveIntegerField(null=True, blank=True)
    to_id = models.PositiveIntegerField(null=True, blank=True)
    from_content_type = models.CharField(max_length=1024)
    to_content_type = models.CharField(max_length=1024)

    from_content_type_id = models.PositiveIntegerField(null=True, blank=True)
    to_content_type_id = models.PositiveIntegerField(null=True, blank=True)

    comment = models.CharField(max_length=1024)

    def __str__(self):
        return f'{self.uuid}'

    class Meta:
        db_table = 'app_market__transactions'
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'
