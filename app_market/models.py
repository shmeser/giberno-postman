import uuid as uuid

import pytz
from dateutil.rrule import MONTHLY, WEEKLY, DAILY
from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex

from app_feedback.models import Review, Like
from app_geo.models import Country, City
from app_market.enums import Currency, TransactionType, TransactionStatus, VacancyEmployment, WorkExperience, \
    ShiftAppealStatus, AppealCancelReason, ManagerAppealCancelReason, JobStatus, SecurityPassRefuseReason, \
    FireByManagerReason, ManagerAppealRefuseReason, AppealCompleteReason, AchievementType, OrderType, OrderStatus, \
    TransactionKind
from app_media.models import MediaModel
from app_users.enums import REQUIRED_DOCS_FOR_CHOICES
from app_users.models import UserProfile
from appcraft_nalog_sdk.models import NalogIncomeRequestModel
from backend.models import BaseModel
from backend.utils import choices
from giberno import settings


class Category(BaseModel):
    title = models.CharField(max_length=128, null=True, blank=True)
    description = models.CharField(max_length=2048, null=True, blank=True)

    def __str__(self):
        return f'{self.title}'

    class Meta:
        db_table = 'app_market__categories'
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Structure(BaseModel):
    title = models.CharField(max_length=128, null=True, blank=True)
    description = models.CharField(max_length=2048, null=True, blank=True)

    def __str__(self):
        return f'{self.title}'

    class Meta:
        db_table = 'app_market__structures'
        verbose_name = 'Бизнес-регион'
        verbose_name_plural = 'Бизнес-регионы'


class Distributor(BaseModel):
    title = models.CharField(max_length=128, null=True, blank=True)
    description = models.CharField(max_length=2048, null=True, blank=True)
    required_docs = ArrayField(models.PositiveIntegerField(choices=REQUIRED_DOCS_FOR_CHOICES), null=True, blank=True)

    categories = models.ManyToManyField(Category, through='DistributorCategory', related_name='distributors')

    rating = models.FloatField(default=0, verbose_name='Рейтинг торговой сети')
    rates_count = models.PositiveIntegerField(default=0, verbose_name='Количество оценок торговой сети')

    media = GenericRelation(MediaModel, object_id_field='owner_id', content_type_field='owner_ct')

    reviews = GenericRelation(Review, object_id_field='target_id', content_type_field='target_ct')

    def __str__(self):
        return f'{self.title}'

    class Meta:
        db_table = 'app_market__distributors'
        verbose_name = 'Торговая сеть'
        verbose_name_plural = 'Торговые сети'


class DistributorStructure(BaseModel):
    distributor = models.ForeignKey(Distributor, on_delete=models.CASCADE)
    structure = models.ForeignKey(Structure, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.distributor.title} - {self.structure.title}'

    class Meta:
        db_table = 'app_market__distributor_structure'
        verbose_name = 'Бизнес-регион торговой сети'
        verbose_name_plural = 'Бизнес-регионы торговых сетей'


class DistributorCategory(BaseModel):
    distributor = models.ForeignKey(Distributor, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.distributor.title} - {self.category.title}'

    class Meta:
        db_table = 'app_market__distributor_category'
        verbose_name = 'Категория торговой сети'
        verbose_name_plural = 'Категории торговых сетей'


class Organization(BaseModel):
    type = models.CharField(max_length=50, null=True, blank=True)
    title = models.CharField(max_length=512, null=True, blank=True)
    short_name = models.CharField(max_length=512, null=True, blank=True)
    full_name = models.CharField(max_length=512, null=True, blank=True)
    legal_inn = models.CharField(max_length=12, null=True, blank=True)
    legal_kpp = models.CharField(max_length=12, null=True, blank=True)
    legal_ogrn = models.CharField(max_length=20, null=True, blank=True)
    legal_ogrn_date = models.DateTimeField(null=True, blank=True)
    legal_form = models.CharField(max_length=50, null=True, blank=True)
    legal_form_id = models.PositiveIntegerField(null=True, blank=True)
    address_legal = models.CharField(max_length=512, null=True, blank=True)
    address_post = models.CharField(max_length=512, null=True, blank=True)

    bank_inn = models.CharField(max_length=12, null=True, blank=True)
    bank_kpp = models.CharField(max_length=12, null=True, blank=True)
    bank_bik = models.CharField(max_length=128, null=True, blank=True)
    bank_account = models.CharField(max_length=128, null=True, blank=True)
    bank_korr_account = models.CharField(max_length=128, null=True, blank=True)
    bank_name = models.CharField(max_length=128, null=True, blank=True)

    distributor = models.ForeignKey(Distributor, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f'{self.title}'

    class Meta:
        db_table = 'app_market__organizations'
        verbose_name = 'Организация'
        verbose_name_plural = 'Организации'


class Shop(BaseModel):
    distributor = models.ForeignKey(Distributor, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=1024, null=True, blank=True)
    description = models.CharField(max_length=2048, null=True, blank=True)

    location = models.PointField(srid=settings.SRID, blank=True, null=True, verbose_name='Геопозиция')
    city = models.ForeignKey(City, blank=True, null=True, on_delete=models.SET_NULL)
    address = models.CharField(max_length=1024, null=True, blank=True, verbose_name='Адрес')

    rating = models.FloatField(default=0, verbose_name='Рейтинг магазина')
    rates_count = models.PositiveIntegerField(default=0, verbose_name='Количество оценок магазина')

    media = GenericRelation(MediaModel, object_id_field='owner_id', content_type_field='owner_ct')
    reviews = GenericRelation(Review, object_id_field='target_id', content_type_field='target_ct')

    chats = GenericRelation('app_chats.Chat', object_id_field='target_id', content_type_field='target_ct',
                            related_query_name='generic_target')

    time_start = models.TimeField(null=True, blank=True, verbose_name='Время открытия магазина')
    time_end = models.TimeField(null=True, blank=True, verbose_name='Время закрытия магазина')

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
        models.PositiveIntegerField(choices=choices(WorkExperience), default=WorkExperience.NO),
        null=True, blank=True, verbose_name='Требуемый опыт'
    )

    required_docs = ArrayField(
        models.PositiveIntegerField(choices=REQUIRED_DOCS_FOR_CHOICES), verbose_name='Документы', null=True, blank=True
    )

    features = models.CharField(max_length=1024, null=True, blank=True, verbose_name='Бонусы и привилегии')

    price = models.PositiveIntegerField(null=True, blank=True, verbose_name='Ставка за час')
    currency = models.PositiveIntegerField(choices=choices(Currency), default=Currency.RUB, verbose_name='Валюта')

    employment = models.PositiveIntegerField(
        choices=choices(VacancyEmployment), default=VacancyEmployment.PARTIAL, verbose_name='Занятость'
    )

    radius = models.PositiveIntegerField(null=True, blank=True, verbose_name='Максимальное расстояние от места работы')

    timezone = models.CharField(
        max_length=512, null=True, blank=True, default='UTC', choices=[(tz, tz) for tz in pytz.all_timezones],
        verbose_name='Часовой пояс вакансии'
    )

    rating = models.FloatField(default=0, verbose_name='Рейтинг')
    rates_count = models.PositiveIntegerField(default=0, verbose_name='Количество оценок')
    views_count = models.PositiveIntegerField(default=0, verbose_name='Количество просмотров')

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)

    media = GenericRelation(MediaModel, object_id_field='owner_id', content_type_field='owner_ct')
    reviews = GenericRelation(Review, object_id_field='target_id', content_type_field='target_ct')
    likes = GenericRelation(Like, object_id_field='target_id', content_type_field='target_ct')

    chats = GenericRelation('app_chats.Chat', object_id_field='target_id', content_type_field='target_ct',
                            related_query_name='generic_target')
    profession = models.ForeignKey('Profession', on_delete=models.SET_NULL, verbose_name='Профессия', null=True,
                                   blank=True)

    def __str__(self):
        return f'{self.title}'

    def increment_views_count(self):
        self.views_count += 1
        self.save()

    class Meta:
        db_table = 'app_market__vacancies'
        verbose_name = 'Вакансия'
        verbose_name_plural = 'Вакансии'

        indexes = [
            GinIndex(
                name="app_market__vacancies__title",
                fields=("title",),
                opclasses=("gin_trgm_ops",)
            ),
        ]


FREQUENCY_CHOICES = [
    (DAILY, "Ежедневно"),
    (WEEKLY, "Еженедельно"),
    (MONTHLY, "Ежемесячно")
]


class Shift(BaseModel):
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)

    price = models.PositiveIntegerField(null=True, blank=True, verbose_name='Ставка за час')
    currency = models.PositiveIntegerField(choices=choices(Currency), default=Currency.RUB, verbose_name='Валюта')

    max_employees_count = models.PositiveIntegerField(default=1, verbose_name='Максимальное число работников')

    min_employee_rating = models.FloatField(
        null=True, blank=True, verbose_name='Минимальный рейтинг работника для автоконтроля'
    )
    auto_control_threshold_minutes = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Минут до начала смены для автоконтроля'
    )

    time_start = models.TimeField(null=True, blank=True, verbose_name='Время начала смены')
    time_end = models.TimeField(null=True, blank=True, verbose_name='Время окончания смены')

    # ## RRULE расписание ## #
    # TODO если понадобятся сезонные смены, то использовать date_start date_end
    date_start = models.DateField(null=True, blank=True, verbose_name='Дата начала расписания')
    date_end = models.DateField(null=True, blank=True, verbose_name='Дата окончания расписания')

    frequency = models.PositiveIntegerField(
        choices=FREQUENCY_CHOICES, null=True, blank=True, verbose_name='Интервал выполнения проверки'
    )
    # by_weekday - массив 0-6, где 0-понедельник
    by_weekday = ArrayField(models.PositiveIntegerField(), size=7, blank=True, null=True, verbose_name='Дни недели')
    by_monthday = ArrayField(models.PositiveIntegerField(), size=31, blank=True, null=True, verbose_name='Дни месяца')
    by_month = ArrayField(models.PositiveIntegerField(), size=12, blank=True, null=True, verbose_name='Месяцы')

    # ## RRULE ## #

    def __str__(self):
        return f'{self.id}'

    class Meta:
        db_table = 'app_market__shifts'
        verbose_name = 'Рабочая смена'
        verbose_name_plural = 'Рабочие смены'


class ShiftAppeal(BaseModel):
    applier = models.ForeignKey(to=UserProfile, on_delete=models.CASCADE, related_name='appeals')
    shift = models.ForeignKey(to=Shift, on_delete=models.CASCADE, related_name='appeals')
    shift_active_date = models.DateTimeField(null=True, blank=True)
    status = models.PositiveIntegerField(choices=choices(ShiftAppealStatus), default=ShiftAppealStatus.INITIAL)

    cancel_reason = models.PositiveIntegerField(
        null=True, blank=True, choices=choices(AppealCancelReason), verbose_name='Причина отмены самозанятым')
    reason_text = models.CharField(max_length=255, null=True, blank=True, verbose_name='Текст причины отмены')

    complete_reason = models.PositiveIntegerField(null=True, blank=True, choices=choices(AppealCompleteReason),
                                                  verbose_name='Причина завершения смены')
    complete_reason_text = models.CharField(max_length=255, null=True, blank=True,
                                            verbose_name='Текст причины завершения')

    manager_cancel_reason = models.PositiveIntegerField(
        null=True, blank=True, choices=choices(ManagerAppealCancelReason), verbose_name='Причина отмены менеджером')
    cancel_reason_text = models.CharField(max_length=255, null=True, blank=True, verbose_name='Текст причины')

    manager_fire_reason = models.PositiveIntegerField(
        null=True, blank=True, choices=choices(FireByManagerReason), verbose_name='Причина увольнения менеджером')

    fire_reason_text = models.CharField(max_length=255, null=True, blank=True,
                                        verbose_name='Текст причины увольнения менеджером')

    fire_at = models.DateTimeField(null=True, blank=True, verbose_name='Время увольнения')

    manager_refuse_reason = models.PositiveIntegerField(
        null=True, blank=True, choices=choices(ManagerAppealRefuseReason), verbose_name='Причина отклонения отклика')

    refuse_reason_text = models.CharField(max_length=255, null=True, blank=True,
                                          verbose_name='Текст причины отклонения отклика')

    # сделано отдельными полями (а не берется из смены) чтоб иметь возможность вычисления верного временного
    # диапазона, когда рабочая смена начинается в один день, а заканчивается в другой
    time_start = models.DateTimeField(null=True, blank=True, verbose_name='Время начала смены')
    time_end = models.DateTimeField(null=True, blank=True, verbose_name='Время окончания смены')

    security_qr_scan_time = models.DateTimeField(null=True, blank=True,
                                                 verbose_name='Время сканирования QR кода охранником')
    manager_qr_scan_time = models.DateTimeField(null=True, blank=True,
                                                verbose_name='Время сканирования QR кода менеджером')

    security_pass_refuse_reason = models.PositiveIntegerField(
        null=True, blank=True, choices=choices(SecurityPassRefuseReason),
        verbose_name='Причина отказа в пропуске охранником')
    security_pass_refuse_reason_text = models.CharField(max_length=255, null=True, blank=True,
                                                        verbose_name='Текст причины отказа в пропуске охранником')

    started_real_time = models.DateTimeField(null=True, blank=True, verbose_name='Фактическое время начала смены')
    completed_real_time = models.DateTimeField(null=True, blank=True, verbose_name='Фактическое время окончания смены')

    job_status = models.PositiveIntegerField(choices=choices(JobStatus), null=True, blank=True, default=None,
                                             verbose_name='Статус работы')

    qr_text = models.CharField(max_length=150, null=True, blank=True)
    notify_leaving = models.BooleanField(default=True)

    class Meta:
        db_table = 'app_market__shifts_appeals'
        verbose_name = 'Отклик на рабочую смену'
        verbose_name_plural = 'Отклики на рабочие смены'


class ShiftAppealInsurance(BaseModel):
    number = models.CharField(max_length=255, null=True, blank=True, verbose_name='Номер полиса')
    appeal = models.ForeignKey(to=ShiftAppeal, on_delete=models.CASCADE, related_name='insurance')
    # Страховщик
    insurer = models.TextField(max_length=4096, null=True, blank=True, verbose_name='Страховщик')
    # Страхователь
    insured_birth_date = models.DateTimeField(null=True, blank=True)
    insured_passport = models.CharField(max_length=255, null=True, blank=True)
    insured_phone = models.CharField(max_length=255, null=True, blank=True)
    insured_email = models.CharField(max_length=255, null=True, blank=True)
    insured_reg_address = models.CharField(max_length=255, null=True, blank=True)
    insured_address = models.CharField(max_length=255, null=True, blank=True)
    # выгодоприобретатель
    beneficiary = models.CharField(max_length=255, null=True, blank=True, verbose_name='Выгодоприобретатель')
    # Период действия
    time_start = models.DateTimeField(null=True, blank=True, verbose_name='Начало страхового периода')
    time_end = models.DateTimeField(null=True, blank=True, verbose_name='Окончание страхового периода')
    # Территория страхования
    address = models.CharField(max_length=255, null=True, blank=True, verbose_name='Территория страхования')
    # Валюта страхования
    currency = models.PositiveIntegerField(choices=choices(Currency), default=Currency.RUB, verbose_name='Валюта')
    # Страховая премия
    insurance_premium = models.PositiveIntegerField(null=True, blank=True, verbose_name='Страховая премия')

    insurance_payment_expiration = models.DateTimeField(null=True, blank=True,
                                                        verbose_name='Срок оплаты страховой премии')
    # Застрахованные лица
    insured_description = models.TextField(max_length=4096, null=True, blank=True, verbose_name='Застрахованные лица')
    # Виды покрываемых рисков
    risks = ArrayField(models.JSONField(null=True, blank=True), size=10, null=True, blank=True, verbose_name='Риски')
    risks_description = models.TextField(max_length=4096, null=True, blank=True, verbose_name='Доп. описание рисков')

    # Особые условия
    special_conditions = models.TextField(max_length=4096, null=True, blank=True, verbose_name='Особые условия')
    # Номер доверенности
    insurer_proxy_number = models.CharField(max_length=255, null=True, blank=True,
                                            verbose_name='Номер доверенности представителя страховщика')
    # Подпись страховщика
    insurer_sign = models.CharField(max_length=255, null=True, blank=True, verbose_name='Подпись страховщика')
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.id}'

    class Meta:
        db_table = 'app_market__shift_appeal_insurance'
        verbose_name = 'Страховка на период рабочей смены'
        verbose_name_plural = 'Страховки на период рабочих смен'


class Partner(BaseModel):
    distributor = models.ForeignKey(Distributor, on_delete=models.CASCADE)
    color = models.CharField(null=True, blank=True, verbose_name='Цвет', max_length=7)
    media = GenericRelation(MediaModel, object_id_field='owner_id', content_type_field='owner_ct')

    def __str__(self):
        return f'{self.distributor.title}'

    class Meta:
        db_table = 'app_market__partners'
        verbose_name = 'Партнер'
        verbose_name_plural = 'Партнеры'


class Coupon(BaseModel):
    description = models.CharField(max_length=128, null=True, blank=True, verbose_name='Описание')
    bonus_price = models.PositiveIntegerField(null=True, blank=True)
    discount = models.PositiveIntegerField(null=True, blank=True, verbose_name='Размер скидки')
    discount_terms = models.CharField(max_length=1024, null=True, blank=True, verbose_name='Условия получения')
    service_description = models.CharField(max_length=1024, null=True, blank=True, verbose_name='Описание услуги')

    partner = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'{self.id}'

    class Meta:
        db_table = 'app_market__coupons'
        verbose_name = 'Купон'
        verbose_name_plural = 'Купоны'


class Code(BaseModel):
    value = models.CharField(max_length=64, null=True, blank=True, unique=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='codes')

    def __str__(self):
        return f'{self.id}'

    class Meta:
        db_table = 'app_market__codes'
        verbose_name = 'Код купона'
        verbose_name_plural = 'Коды Купонов'


class Order(BaseModel):
    description = models.CharField(max_length=1024, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    terms_accepted = models.BooleanField(default=False)
    user = models.ForeignKey(UserProfile, blank=True, null=True, on_delete=models.SET_NULL)

    type = models.PositiveIntegerField(default=OrderType.TEST.value, choices=choices(OrderType))
    status = models.PositiveIntegerField(default=OrderStatus.CREATED.value, choices=choices(OrderStatus))

    def __str__(self):
        return f'{self.email}'

    class Meta:
        db_table = 'app_market__orders'
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'


class UserCode(BaseModel):
    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    code = models.ForeignKey(Code, on_delete=models.SET_NULL, null=True, blank=True, related_name='receivers')

    activated_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата активации')
    order = models.ForeignKey(Order, blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f'User{self.user_id} Coupon{self.code.coupon_id}'

    class Meta:
        db_table = 'app_market__code_user'
        verbose_name = 'Купон пользователя'
        verbose_name_plural = 'Купоны пользователей'


class Transaction(BaseModel):
    order = models.ForeignKey(Order, blank=True, null=True, on_delete=models.SET_NULL)

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

    # Generic Relation base from
    from_id = models.PositiveIntegerField(null=True, blank=True)
    from_ct = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL, related_name='from_ct')
    from_ct_name = models.CharField(max_length=255, blank=True, null=True)
    _from = GenericForeignKey(ct_field='from_ct', fk_field='from_id')

    # Generic Relation base to
    to_id = models.PositiveIntegerField(null=True, blank=True)
    to_ct = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.SET_NULL, related_name='to_ct'
    )
    to_ct_name = models.CharField(max_length=255, blank=True, null=True)
    _to = GenericForeignKey(ct_field='to_ct', fk_field='to_id')

    comment = models.CharField(max_length=1024)

    kind = models.PositiveIntegerField(
        null=True, blank=True, choices=choices(TransactionKind), verbose_name='Вид транзакции'
    )

    receipt = models.ForeignKey(NalogIncomeRequestModel, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f'{self.uuid}'

    class Meta:
        db_table = 'app_market__transactions'
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'


class Profession(BaseModel):
    name = models.CharField(max_length=1024, null=True, blank=True)
    description = models.CharField(max_length=1024, null=True, blank=True)

    suggested_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name='Предложена пользователем')
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='Одобрена (для предложенных)')

    def __str__(self):
        return f'{self.name}'

    class Meta:
        db_table = 'app_market__professions'
        verbose_name = 'Профессия'
        verbose_name_plural = 'Профессии'


class Position(BaseModel):
    title = models.CharField(max_length=1024, null=True, blank=True)
    description = models.CharField(max_length=1024, null=True, blank=True)

    professions = models.ManyToManyField(Profession, db_table='app_market__profession_position', null=True, blank=True)

    def __str__(self):
        return f'{self.title}'

    class Meta:
        db_table = 'app_market__positions'
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'


class UserProfession(BaseModel):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    profession = models.ForeignKey(Profession, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name} - {self.profession.name}'

    class Meta:
        db_table = 'app_market__profession_user'
        verbose_name = 'Профессия пользователя'
        verbose_name_plural = 'Профессии пользователей'


class Skill(BaseModel):
    name = models.CharField(max_length=1024, null=True, blank=True)
    description = models.CharField(max_length=1024, null=True, blank=True)

    suggested_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name='Предложена пользователем')
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='Одобрена (для предложенных)')

    def __str__(self):
        return f'{self.name}'

    class Meta:
        db_table = 'app_market__skills'
        verbose_name = 'Специальный навык'
        verbose_name_plural = 'Специальные навыки'


class UserSkill(BaseModel):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name} - {self.skill.name}'

    class Meta:
        db_table = 'app_market__skill_user'
        verbose_name = 'Специальный навык пользователя'
        verbose_name_plural = 'Специальные навыки пользователей'


class GlobalDocument(BaseModel):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    document = models.ForeignKey(
        MediaModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_global_documents'
    )

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name} - {self.document.title}'

    class Meta:
        db_table = 'app_market__user_global_document'
        verbose_name = 'Документ сервиса для пользователя'
        verbose_name_plural = 'Документы сервиса для пользователей'


class DistributorDocument(BaseModel):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    distributor = models.ForeignKey(Distributor, on_delete=models.CASCADE)
    document = models.ForeignKey(
        MediaModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_distributor_documents'
    )

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name} - {self.distributor.title} - {self.document.title}'

    class Meta:
        db_table = 'app_market__user_distributor_document'
        verbose_name = 'Документ торговой сети для пользователя'
        verbose_name_plural = 'Документы торговых сетей для пользователей'


class PartnerDocument(BaseModel):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE)
    document = models.ForeignKey(
        MediaModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_partner_documents'
    )

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name} - {self.partner.distributor.title} - {self.document.title}'

    class Meta:
        db_table = 'app_market__user_partner_document'
        verbose_name = 'Документ Магазина-Партнера для пользователя'
        verbose_name_plural = 'Документы Магазинов-Партнеров для пользователей'


class VacancyDocument(BaseModel):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE)
    document = models.ForeignKey(
        MediaModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_vacancy_documents'
    )

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name} - {self.vacancy.title} - {self.document.title}'

    class Meta:
        db_table = 'app_market__user_vacancy_document'
        verbose_name = 'Документ вакансии для пользователя'
        verbose_name_plural = 'Документы вакансий для пользователей'


class Achievement(BaseModel):
    name = models.CharField(max_length=512, blank=True, null=True)
    description = models.CharField(max_length=3072, blank=True, null=True)

    actions_min_count = models.PositiveIntegerField(
        default=1, verbose_name='Количество действий для получения достижения'
    )
    type = models.PositiveIntegerField(choices=choices(AchievementType), null=True, blank=True)

    media = GenericRelation(MediaModel, object_id_field='owner_id', content_type_field='owner_ct')

    class Meta:
        db_table = 'app_market__achievements'
        verbose_name = 'Достижение'
        verbose_name_plural = 'Достижения'


class AchievementProgress(BaseModel):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)

    actions_min_count = models.PositiveIntegerField(
        default=1, verbose_name='Количество действий для получения достижения'
    )
    achieved_count = models.PositiveIntegerField(default=0, verbose_name='Получено раз')

    started_at = models.DateTimeField(
        null=True, blank=True, verbose_name='Время начала накопления прогресса по достижению'
    )
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Время завершения прогресса по достижению')

    def __str__(self):
        return f'{self.id}'

    class Meta:
        db_table = 'app_market__achievement_progress'
        verbose_name = 'Прогресс пользователя по достижению'
        verbose_name_plural = 'Прогресс пользователей по достижениям'


class Advertisement(BaseModel):
    title = models.CharField(max_length=512, blank=True, null=True)
    description = models.CharField(max_length=3072, blank=True, null=True)
    media = GenericRelation(MediaModel, object_id_field='owner_id', content_type_field='owner_ct')

    class Meta:
        db_table = 'app_market__advertisements'
        verbose_name = 'Рекламный блок'
        verbose_name_plural = 'Рекламные блоки'
