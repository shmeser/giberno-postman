from datetime import timedelta, datetime

import pytz
from channels.db import database_sync_to_async
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db.models import GeometryField, CharField, Window
from django.contrib.gis.db.models.functions import Distance, Envelope
from django.contrib.gis.geos import MultiPoint
from django.contrib.postgres.aggregates import BoolOr, ArrayAgg
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Value, IntegerField, Case, When, BooleanField, Q, Count, Prefetch, F, Func, \
    DateTimeField, Lookup, Field, DateField, Sum, ExpressionWrapper, Subquery, OuterRef, TimeField, Exists, Avg
from django.db.models.functions import Cast, Concat, Extract, Round, Coalesce
from django.utils.timezone import now, localtime
from pytz import timezone
from rest_framework.exceptions import PermissionDenied

from app_chats.models import ChatUser, Chat
from app_feedback.models import Review, Like
from app_geo.models import Region
from app_market.enums import ShiftWorkTime, ShiftAppealStatus, WorkExperience, VacancyEmployment, \
    JobStatus, JobStatusForClient
from app_market.models import Vacancy, Profession, Skill, Distributor, Shop, Shift, ShiftAppeal, \
    GlobalDocument, VacancyDocument, DistributorDocument
from app_market.utils import handle_date_for_appeals
from app_market.versions.v1_0.mappers import ShiftMapper
from app_media.enums import MediaType, MediaFormat
from app_media.models import MediaModel
from app_users.enums import AccountType, DocumentType
from app_users.models import UserProfile, Document
from backend.entity import Error
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exceptions import HttpException, CustomException
from backend.mixins import MasterRepository, MakeReviewMethodProviderRepository
from backend.utils import ArrayRemove, datetime_to_timestamp, timestamp_to_datetime
from giberno import settings


class DistributorsRepository(MakeReviewMethodProviderRepository):
    model = Distributor

    def __init__(self, point=None, screen_diagonal_points=None, time_zone=None, me=None) -> None:
        super().__init__()

        self.me = me
        self.point = point

        # Выражения для вычисляемых полей в annotate
        self.vacancies_expression = Count('shop__vacancy')

        # Основная часть запроса, содержащая вычисляемые поля
        self.base_query = self.model.objects.annotate(
            vacancies_count=self.vacancies_expression
        )

    def get_by_id(self, record_id):
        record = self.base_query.filter(id=record_id)
        record = self.fast_related_loading(record, self.me, self.point).first()
        if not record:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден')
        return record

    def filter_by_kwargs(self, kwargs, paginator=None, order_by: list = None):
        try:
            if order_by:
                records = self.base_query.order_by(*order_by).exclude(deleted=True).filter(**kwargs)
            else:
                records = self.base_query.exclude(deleted=True).filter(**kwargs)
        except Exception:  # no 'deleted' field
            if order_by:
                records = self.base_query.order_by(*order_by).filter(**kwargs)
            else:
                records = self.base_query.filter(**kwargs)

        return self.fast_related_loading(  # Предзагрузка связанных сущностей
            queryset=records[paginator.offset:paginator.limit] if paginator else records,
            me=self.me
        )

    @staticmethod
    def fast_related_loading(queryset, me, point=None):
        queryset = queryset.prefetch_related(
            # Подгрузка медиа
            Prefetch(
                'media',
                queryset=MediaModel.objects.filter(
                    deleted=False,
                    type__in=[MediaType.LOGO.value, MediaType.BANNER.value],
                    owner_ct_id=ContentType.objects.get_for_model(Distributor).id,
                    format=MediaFormat.IMAGE.value
                ),
                to_attr='medias'
            )
        )

        region = Region.objects.filter(boundary__covers=point).first() if point else None

        if region and me:
            queryset = queryset.prefetch_related(
                # подгрузка отзывов по региону в котором находится пользователь
                Prefetch(
                    'reviews',
                    queryset=Review.objects.filter(
                        owner_id=me.id,
                        target_ct=ContentType.objects.get_for_model(Distributor),
                        region=region
                    )
                )
            )

        return queryset


class AsyncDistributorsRepository(DistributorsRepository):
    def __init__(self, me=None) -> None:
        super().__init__()
        self.me = me

    @database_sync_to_async
    def get_by_id(self, record_id):
        return super().get_by_id(record_id)


class ShopsRepository(MakeReviewMethodProviderRepository):
    model = Shop

    def __init__(self, point=None, screen_diagonal_points=None, me=None) -> None:
        super().__init__()

        self.me = me
        self.point = point
        self.screen_diagonal_points = screen_diagonal_points

        # Выражения для вычисляемых полей в annotate
        self.distance_expression = Distance('location', point) if point else Value(None, IntegerField())

        # Выражения для вычисляемых полей в annotate
        self.vacancies_expression = Count('vacancy')

        # Основная часть запроса, содержащая вычисляемые поля
        self.base_query = self.model.objects.annotate(
            distance=self.distance_expression,
            vacancies_count=self.vacancies_expression
        )

        # Фильтрация по вхождению в область на карте
        if self.screen_diagonal_points:
            self.base_query = self.base_query.filter(
                location__contained=ExpressionWrapper(
                    Envelope(
                        MultiPoint(
                            self.screen_diagonal_points[0], self.screen_diagonal_points[1], srid=settings.SRID
                        )
                    ),
                    output_field=GeometryField()
                )
            )

    def get_by_id(self, record_id):
        record = self.base_query.filter(id=record_id)
        record = self.fast_related_loading(record).first()
        if not record:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден')
        return record

    def filter_by_kwargs(self, kwargs, paginator=None, order_by: list = None):
        try:
            if order_by:
                records = self.base_query.order_by(*order_by).exclude(deleted=True).filter(**kwargs)
            else:
                records = self.base_query.exclude(deleted=True).filter(**kwargs)
        except Exception:  # no 'deleted' field
            if order_by:
                records = self.base_query.order_by(*order_by).filter(**kwargs)
            else:
                records = self.base_query.filter(**kwargs)

        return self.fast_related_loading(  # Предзагрузка связанных сущностей
            queryset=records[paginator.offset:paginator.limit] if paginator else records,
            point=self.point
        )

    def filter(self, args: list = None, kwargs={}, paginator=None, order_by: list = None):
        try:
            if order_by:
                records = self.base_query.order_by(*order_by).exclude(deleted=True).filter(args, **kwargs)
            else:
                records = self.base_query.exclude(deleted=True).filter(args, **kwargs)
        except Exception:  # no 'deleted' field
            if order_by:
                records = self.base_query.order_by(*order_by).filter(args, **kwargs)
            else:
                records = self.base_query.filter(args, **kwargs)
        return self.fast_related_loading(  # Предзагрузка связанных сущностей
            queryset=records[paginator.offset:paginator.limit] if paginator else records,
            point=self.point
        )

    @staticmethod
    def fast_related_loading(queryset, point=None):
        """ Подгрузка зависимостей
            Media
        """
        queryset = queryset.prefetch_related(
            # Подгрузка медиа для магазинов
            Prefetch(
                'media',
                queryset=MediaModel.objects.filter(
                    deleted=False,
                    type__in=[MediaType.LOGO.value, MediaType.BANNER.value],
                    owner_ct_id=ContentType.objects.get_for_model(Shop).id,
                    format=MediaFormat.IMAGE.value
                ),
                to_attr='medias'

            )
        )

        return queryset

    def map(self, kwargs, paginator=None, order_by: list = None):
        queryset = self.filter_by_kwargs(kwargs, paginator, order_by)

        return self.clustering(queryset)

    def clustering(self, queryset):
        raw_sql = f'''
            WITH clusters AS (
                SELECT 
                    cluster_geometries,
                    ST_Centroid (cluster_geometries) AS centroid,
                    ST_NumGeometries(cluster_geometries) as clustered_count
                FROM 
                    UNNEST(
                        (
                            SELECT 
                                ST_ClusterWithin(location, 500/111111.0) 
                            FROM 
                                (
                                    {queryset.only('location').query}
                                ) subquery
                        ) 
                    ) cluster_geometries
            )
            ------======================================-------

            SELECT
                s.id,
                s.title,
                clusters.clustered_count,
                (
                    SELECT 
                        ARRAY_AGG(id) 
                    FROM app_market__shops
                    WHERE ST_Intersects(cluster_geometries, location)
                ) AS clustered_ids,
                ST_X(ST_Centroid (cluster_geometries)) AS lon,
                ST_Y(ST_Centroid (cluster_geometries)) AS lat
--                 clusters.centroid
--                 ST_DistanceSphere(s.location, ST_GeomFromGeoJSON('{self.point.geojson}')) AS distance
            FROM clusters
            JOIN app_market__shops s ON (s.location=ST_ClosestPoint(clusters.cluster_geometries, ST_GeomFromGeoJSON('{self.point.geojson}'))) -- JOIN с ближайшей точкой 
            ORDER BY 3 DESC
        '''
        return self.model.objects.raw(raw_sql)

    def get_managers(self, record_id):
        record = self.model.objects.filter(pk=record_id).first()
        if record:
            return [manager for manager in record.staff.filter(account_type=AccountType.MANAGER.value)]
        return []


class AsyncShopsRepository(ShopsRepository):
    def __init__(self, me=None) -> None:
        super().__init__()
        self.me = me

    @database_sync_to_async
    def get_by_id(self, record_id):
        return super().get_by_id(record_id)


class CustomLookupBase(Lookup):
    # Кастомный lookup
    lookup_name = 'custom'
    parametric_string = "%s <= %s AT TIME ZONE timezone"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return self.parametric_string % (lhs, rhs), params


@Field.register_lookup
class DatesArrayContains(CustomLookupBase):
    # Кастомный lookup с приведением типов для массива дат
    lookup_name = 'dacontains'
    parametric_string = "%s::DATE[] @> %s"


@Field.register_lookup
class LTTimeTZ(CustomLookupBase):
    # Кастомный lookup для сравнения времени с учетом временной зоны из поля timezone
    lookup_name = 'lttimetz'
    parametric_string = "%s < %s AT TIME ZONE timezone"


@Field.register_lookup
class LTETimeTZ(CustomLookupBase):
    # Кастомный lookup для сравнения времени с учетом временной зоны из поля timezone
    lookup_name = 'ltetimetz'
    parametric_string = "%s <= %s AT TIME ZONE timezone"


@Field.register_lookup
class GTETimeTZ(CustomLookupBase):
    # Кастомный lookup для сравнения времени с учетом временной зоны из поля timezone
    lookup_name = 'gtetimetz'
    parametric_string = "%s >= %s AT TIME ZONE timezone"


@Field.register_lookup
class GTTimeTZ(CustomLookupBase):
    # Кастомный lookup для сравнения времени с учетом временной зоны из поля timezone
    lookup_name = 'gttimetz'
    parametric_string = "%s > %s AT TIME ZONE timezone"


@Field.register_lookup
class LTdtTZ(CustomLookupBase):
    # Кастомный lookup для сравнения времени с учетом временной зоны из поля timezone
    lookup_name = 'ltdttz'
    parametric_string = "%s AT TIME ZONE timezone < %s AT TIME ZONE timezone"


@Field.register_lookup
class LTEdtTZ(CustomLookupBase):
    # Кастомный lookup для сравнения времени с учетом временной зоны из поля timezone
    lookup_name = 'ltedttz'
    parametric_string = "%s AT TIME ZONE timezone <= %s AT TIME ZONE timezone"


@Field.register_lookup
class GTEdtTZ(CustomLookupBase):
    # Кастомный lookup для сравнения времени с учетом временной зоны из поля timezone
    lookup_name = 'gtedttz'
    parametric_string = "%s AT TIME ZONE timezone >= %s AT TIME ZONE timezone"


@Field.register_lookup
class GTdtTZ(CustomLookupBase):
    # Кастомный lookup для сравнения времени с учетом временной зоны из поля timezone
    lookup_name = 'gtdttz'
    parametric_string = "%s AT TIME ZONE timezone > %s AT TIME ZONE timezone"


@Field.register_lookup
class DateTZ(CustomLookupBase):
    # Кастомный lookup с приведением типов для даты во временной зоне из поля timezone
    lookup_name = 'datetz'
    parametric_string = "(%s AT TIME ZONE timezone)::DATE = %s :: DATE"


@Field.register_lookup
class DateTZGte(CustomLookupBase):
    # Кастомный lookup с приведением типов для сравнения дат во временной зоне из поля timezone
    lookup_name = 'datetz_gte'
    parametric_string = "(%s AT TIME ZONE timezone)::DATE >= %s :: DATE"


@Field.register_lookup
class DateTZLte(CustomLookupBase):
    # Кастомный lookup с приведением типов для сравнения дат во временной зоне из поля timezone
    lookup_name = 'datetz_lte'
    parametric_string = "(%s AT TIME ZONE timezone)::DATE <= %s :: DATE"


class ShiftsRepository(MasterRepository):
    model = Shift

    SHIFTS_CALENDAR_DEFAULT_DAYS_COUNT = 10

    def __init__(self, me=None, calendar_from=None, calendar_to=None, vacancy_timezone_name='UTC') -> None:
        super().__init__()
        # TODO брать из вакансии vacancy_timezone_name
        self.vacancy_timezone_name = vacancy_timezone_name
        self.me = me
        # Получаем дату начала диапазона для расписани
        self.calendar_from = localtime(
            now(), timezone=timezone(vacancy_timezone_name)
        ).isoformat() if calendar_from is None else localtime(
            calendar_from, timezone=timezone(vacancy_timezone_name)  # Даты высчитываем в часовых поясах вакансий
        ).isoformat()

        # Получаем дату окончания диапазона для расписания
        self.calendar_to = localtime(now() + timedelta(days=self.SHIFTS_CALENDAR_DEFAULT_DAYS_COUNT),
                                     timezone=timezone(vacancy_timezone_name)).isoformat() \
            if calendar_to is None else localtime(calendar_to, timezone=timezone(vacancy_timezone_name)).isoformat()

        # Annotation Expressions
        self.active_dates_expression = Func(
            F('frequency'),
            F('by_month'),
            F('by_monthday'),
            F('by_weekday'),
            Value(self.calendar_from),
            Value(self.calendar_to),
            function='rrule_list_occurences',  # Кастомная postgres функция (возвращает массив дат вида TIMESTAMPTZ)
            output_field=ArrayField(DateTimeField())
        )

        self.active_today_expression = Case(
            When(
                # Используем поле active_dates из предыдущего annotate и кастомный lookup для приведения типов в PgSQL
                # TIMESTAMPTZ[] -> DATE[] так как нужно проверить наличие текущей даты без времени в массиве расписания,
                # который содержит массив дат со временем и зонами

                # Можно рассмотреть вариант массива без времени, получаемого из rrule_list_occurences,
                # чтобы не использовать кастомный lookup
                # Для этого нужно поменять тип возвращаемых данных из кастомной функции
                active_dates__dacontains=Cast(
                    [localtime(now(), timezone=timezone(vacancy_timezone_name))],
                    output_field=ArrayField(DateField())
                ),
                then=True
            ),
            default=False,
            output_field=BooleanField()
        )

        # Основная часть запроса, содержащая вычисляемые поля
        self.base_query = self.model.objects.annotate(
            active_dates=self.active_dates_expression,
            active_today=self.active_today_expression,
        )

    def filter_by_kwargs(self, kwargs, paginator=None, order_by: list = None):
        try:
            if order_by:
                records = self.base_query.order_by(*order_by).exclude(deleted=True).filter(**kwargs)
            else:
                records = self.base_query.exclude(deleted=True).filter(**kwargs)
        except Exception:  # no 'deleted' field
            if order_by:
                records = self.base_query.order_by(*order_by).filter(**kwargs)
            else:
                records = self.base_query.filter(**kwargs)
        return records[paginator.offset:paginator.limit] if paginator else records

    def filter(self, args: list = None, kwargs={}, paginator=None, order_by: list = None):
        try:
            if order_by:
                records = self.base_query.order_by(*order_by).exclude(deleted=True).filter(args, **kwargs)
            else:
                records = self.base_query.exclude(deleted=True).filter(args, **kwargs)
        except Exception:  # no 'deleted' field
            if order_by:
                records = self.base_query.order_by(*order_by).filter(args, **kwargs)
            else:
                records = self.base_query.filter(args, **kwargs)
        return records[paginator.offset:paginator.limit] if paginator else records

    @staticmethod
    def active_dates(queryset):
        active_dates = []
        current_time = now()
        if queryset.count():
            for shift in queryset:
                vacancy_timezone = pytz.timezone(shift.vacancy.timezone)
                utc_offset = vacancy_timezone.utcoffset(datetime.utcnow()).total_seconds()
                for active_date in shift.active_dates:
                    # Нужно сравнивать даты без времени и только во временной зоне вакансии
                    if localtime(active_date, timezone=vacancy_timezone).date() >= localtime(
                            current_time, timezone=vacancy_timezone
                    ).date():
                        active_dates.append({
                            'utc_offset': utc_offset,
                            'timestamp': datetime_to_timestamp(active_date)
                        })

        return active_dates

    def get_shift_for_managers(self, record_id, active_date=now()):
        shifts = self.base_query.filter(id=record_id, deleted=False).annotate(
            # Флаг - активна ли смена в указанную дату, для фильтрации (вычислются 10 дат от текущего дня по умолчанию)
            # для расширения диапазона надо передавать calendar_from calendar_to
            active_this_date=Case(
                When(
                    active_dates__dacontains=Cast(
                        [localtime(active_date, timezone=timezone(self.vacancy_timezone_name))],
                        output_field=ArrayField(DateField())
                    ),
                    then=True
                ),
                default=False,
                output_field=BooleanField()
            )
        ).filter(active_this_date=True).select_related('vacancy').annotate(
            confirmed_appeals_count=Coalesce(Count('appeals', filter=Q(
                appeals__status=ShiftAppealStatus.CONFIRMED.value,
                # дата смены в отклике должна совпадать с переданной датой
                appeals__shift_active_date__datetz=localtime(  # в часовом поясе вакансии
                    active_date, timezone=timezone(self.vacancy_timezone_name)
                ).date()
            )), 0),
        )
        if not shifts:
            raise HttpException(detail=f'Смена с ID {record_id} не найдена', status_code=RESTErrors.NOT_FOUND.value)
        return shifts.first()

    def get_shifts_on_current_date_for_vacancy(self, vacancy, current_date=now()):
        shifts = self.base_query.filter(vacancy_id=vacancy.id, deleted=False).annotate(
            # Флаг - активна ли смена в указанную дату, для фильтрации (вычислются 10 дат от текущего дня по умолчанию)
            # для расширения диапазона надо передавать calendar_from calendar_to
            active_this_date=Case(
                When(
                    active_dates__dacontains=Cast(
                        [localtime(current_date, timezone=timezone(self.vacancy_timezone_name))],
                        output_field=ArrayField(DateField())
                    ),
                    then=True
                ),
                default=False,
                output_field=BooleanField()
            )
        ).filter(active_this_date=True)
        return shifts

    @staticmethod
    def get_appeals_with_appliers(instance: Shift, current_date, filters):
        appeals = [
            appeal.applier for appeal in
            instance.appeals.annotate(  # Добавляем поле timezone для работы с кастомным лукапом datetz
                timezone=F('shift__vacancy__timezone')
            ).filter(
                # TODO Нужно префетчить
                shift_active_date__datetz=localtime(  # в часовом поясе вакансии
                    current_date, timezone=timezone(instance.vacancy.timezone)
                ).date(),
                **filters
            )
        ]

        return appeals

    def work_location_update(self, point, shift_id=None):
        self.me.location = point
        self.me.save()

        should_notify_managers = False
        managers = None
        managers_sockets = None
        chat_id = None

        shift = Shift.objects.filter(
            id=shift_id
        ).select_related('vacancy').first()
        if not shift:
            raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=f'Смена с ID={shift_id} не найдена')

        vacancy_timezone_name = shift.vacancy.timezone if shift.vacancy.timezone else 'Europe/Moscow'

        is_appeal_confirmed_for_today = ShiftAppeal.objects.annotate(
            timezone=F('shift__vacancy__timezone')
        ).filter(
            applier=self.me,
            status=ShiftAppealStatus.CONFIRMED.value,
            shift_id=shift_id,
            shift_active_date__datetz=localtime(now(), timezone=timezone(vacancy_timezone_name)),
            time_start__ltetimetz=localtime(now(), timezone=timezone(vacancy_timezone_name)),
            time_end__gttimetz=localtime(now(), timezone=timezone(vacancy_timezone_name))
        ).exists()

        is_within_radius = Vacancy.objects.annotate(  # Есть вакансия, где дистанция меньше, чем указанный в ней радиус
            distance=Distance('shop__location', point)
        ).filter(
            Q(id=shift.vacancy_id, radius__isnull=False, distance__lte=F('radius')) |
            Q(id=shift.vacancy_id, radius__isnull=True)  # Защита от вакансий без радиуса, чтобы не сигналило постоянно
        ).exists()

        if is_appeal_confirmed_for_today and not is_within_radius:
            should_notify_managers = True

            managers, managers_sockets = VacanciesRepository().get_managers_and_sockets_for_vacancy(
                shift.vacancy
            )

            chat = Chat.objects.filter(
                subject_user=self.me,
                target_ct=ContentType.objects.get_for_model(Vacancy),
                target_id=shift.vacancy_id
            ).first()
            chat_id = chat.id

        return should_notify_managers, managers, managers_sockets, chat_id


# class UserShiftRepository(MasterRepository):
#     model = UserShift
#
#     def __init__(self, me=None):
#         super().__init__()
#         self.me = me
#
#     def update_status_by_qr_check(self, instance):
#         if instance.shift.vacancy.shop not in self.me.shops.all():
#             raise PermissionDenied()
#
#         if self.me.is_security:
#             return
#         if self.me.is_manager:
#             if instance.status == ShiftStatus.INITIAL:
#                 instance.status = ShiftStatus.STARTED
#                 instance.save()
#             elif instance.status == ShiftStatus.STARTED:
#                 instance.status = ShiftStatus.COMPLETED
#                 instance.qr_data = {}
#                 instance.save()
#             elif instance.status == ShiftStatus.COMPLETED:
#                 return


class VacanciesRepository(MakeReviewMethodProviderRepository):
    model = Vacancy

    # TODO если у вакансии несколько смен, то вакансия постоянно будет горящая?
    IS_HOT_HOURS_THRESHOLD = 4  # Количество часов до начала смены для статуса вакансии "Горящая"
    TRIGRAM_SIMILARITY_MIN_RATE = 0.3  # Мин коэффициент сходства по pg_trigram
    SIMILAR_VACANCIES_MAX_DISTANCE_M = 50000  # Максимальное расстояние для похожих вакансий

    def __init__(self, point=None, screen_diagonal_points=None, me=None, timezone_name='Europe/Moscow') -> None:
        super().__init__()

        self.point = point
        self.screen_diagonal_points = screen_diagonal_points
        self.me = me

        # Выражения для вычисляемых полей в annotate
        self.distance_expression = Distance('shop__location', point) if point else Value(None, IntegerField())
        self.is_hot_expression = BoolOr(  # Аггрегация булевых значений (Если одно из значений true, то результат true)
            Case(When(Q(  # Смена должна начаться в ближайшие 4 часа #
                # Используем кастомные lookup ltetimetz и gttimetz для учета часового пояса вакансии (лежит в timezone)
                shift__time_start__ltetimetz=(datetime.utcnow() + timedelta(hours=self.IS_HOT_HOURS_THRESHOLD)).time(),
                shift__time_start__gttimetz=datetime.utcnow().time()
            ), then=True), default=False, output_field=BooleanField())
        )
        morning_range = ShiftMapper.work_time_to_time_range(ShiftWorkTime.MORNING.value)
        day_range = ShiftMapper.work_time_to_time_range(ShiftWorkTime.DAY.value)
        evening_range = ShiftMapper.work_time_to_time_range(ShiftWorkTime.EVENING.value)

        # Выставляем work_time по времени начала смены - time_start
        self.work_time_expression = ArrayRemove(  # Удаляем из массива null значения с помощью ArrayRemove
            ArrayAgg(  # Аггрегация значений в массив
                Case(
                    When(Q(  # Если начинается утром
                        shift__time_start__gte=morning_range[0],
                        shift__time_end__gt=morning_range[0],
                        shift__time_start__lt=morning_range[1],
                        shift__time_end__lte=morning_range[1]
                    ),
                        then=ShiftWorkTime.MORNING
                    ),
                    When(Q(  # Если начинается днем
                        shift__time_start__gte=day_range[0],
                        shift__time_end__gt=day_range[0],
                        shift__time_start__lt=day_range[1],
                        shift__time_end__lte=day_range[1]
                    ),
                        then=ShiftWorkTime.DAY
                    ),
                    When(  # Если начинается вечером c 18 до 23:59 (0:00)
                        Q(  # Если в смене окончание указано НЕ ровно в 0:00:00
                            shift__time_start__gte=evening_range[0],
                            shift__time_end__gt=evening_range[0],
                            shift__time_start__lt=evening_range[1],
                            shift__time_end__lte=evening_range[1]
                        ) |
                        Q(  # Если в смене окончание указано ровно в 0:00:00
                            shift__time_start__gte=evening_range[0],
                            shift__time_end=evening_range[2],
                        ),
                        then=ShiftWorkTime.EVENING
                    ),
                    default=None,
                    output_field=IntegerField()
                )
            ), None)  # Удаляем из массива null значения

        # количество общих мест в вакансии
        self.total_count_expression = ExpressionWrapper(
            Sum('shift__max_employees_count'), output_field=IntegerField()
        )

        # Количество свободных мест в вакансии
        self.free_count_expression = ExpressionWrapper(
            Sum('shift__max_employees_count') - Sum('shift__employees_count'),
            output_field=IntegerField()
        )

        # Основная часть запроса, содержащая вычисляемые поля
        self.base_query = self.model.objects.annotate(
            distance=self.distance_expression,
            is_hot=self.is_hot_expression,
            work_time=self.work_time_expression,
            total_count=self.total_count_expression,
            free_count=self.free_count_expression,
        )

        # Фильтрация по вхождению в область на карте
        if self.screen_diagonal_points:
            self.base_query = self.base_query.filter(
                shop__location__contained=ExpressionWrapper(
                    Envelope(  # BoundingCircle использовался для описывающего круга
                        MultiPoint(
                            self.screen_diagonal_points[0], self.screen_diagonal_points[1], srid=settings.SRID
                        )
                    ),
                    output_field=GeometryField()
                )
            )

    def modify_kwargs(self, kwargs):
        if self.screen_diagonal_points:
            # Если передана область на карте, то радиус поиска от указанной точки не учитывается в фильтрации
            kwargs.pop('distance__lte', None)

    def get_by_id(self, record_id):
        record = self.base_query.filter(id=record_id)
        record = self.fast_related_loading(record, self.point).first()
        if not record:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден')
        return record

    def get_by_id_for_manager_or_security(self, record_id):
        record = self.get_by_id(record_id=record_id)
        if record.shop not in self.me.shops.all():
            raise PermissionDenied()
        return record

    def filter_by_kwargs(self, kwargs, paginator=None, order_by: list = None):
        self.modify_kwargs(kwargs)  # Изменяем kwargs для работы с objects.filter(**kwargs)
        try:
            if order_by:
                records = self.base_query.order_by(*order_by).exclude(deleted=True).filter(**kwargs)
            else:
                records = self.base_query.exclude(deleted=True).filter(**kwargs)
        except Exception:  # no 'deleted' field
            if order_by:
                records = self.base_query.order_by(*order_by).filter(**kwargs)
            else:
                records = self.base_query.filter(**kwargs)

        return self.fast_related_loading(  # Предзагрузка связанных сущностей
            queryset=records[paginator.offset:paginator.limit] if paginator else records,
            point=self.point
        )

    def get_vacancy_managers(self, record_id):
        record = self.model.objects.filter(pk=record_id).prefetch_related(Prefetch(
            'shop__staff',
            queryset=UserProfile.objects.filter(account_type=AccountType.MANAGER.value)
        )).first()
        if record:
            return [manager for manager in record.shop.staff.all()]
        return []

    def get_vacancy_managers_sockets(self, record_id):
        record = self.model.objects.filter(pk=record_id).annotate(
            sockets=ArrayRemove(
                ArrayAgg(
                    'shop__staff__sockets__socket_id',
                    filter=Q(staff__account_type=AccountType.MANAGER.value)
                ),
                None
            )
        )
        if record:
            return record.sockets
        return []

    def filter(self, args: list = None, kwargs={}, paginator=None, order_by: list = None):
        self.modify_kwargs(kwargs)  # Изменяем kwargs для работы с objects.filter(**kwargs)
        try:
            if order_by:
                records = self.base_query.order_by(*order_by).exclude(deleted=True).filter(args, **kwargs)
            else:
                records = self.base_query.exclude(deleted=True).filter(args, **kwargs)
        except Exception:  # no 'deleted' field
            if order_by:
                records = self.base_query.order_by(*order_by).filter(args, **kwargs)
            else:
                records = self.base_query.filter(args, **kwargs)
        return self.fast_related_loading(  # Предзагрузка связанных сущностей
            queryset=records[paginator.offset:paginator.limit] if paginator else records,
            point=self.point
        )

    def queryset_by_manager(self, order_params=None, pagination=None):
        if not self.me.account_type == AccountType.MANAGER:
            raise PermissionDenied()
        return self.filter_by_kwargs(
            kwargs={'shop_id__in': self.me.shops.all()},
            order_by=order_params,
            paginator=pagination
        )

    def queryset_filtered_by_current_date_range_for_manager(self, order_params, pagination, current_date, next_day):
        vacancies = self.queryset_by_manager()
        shifts = ShiftsRepository(calendar_from=current_date, calendar_to=next_day).filter_by_kwargs(
            kwargs={'vacancy_id__in': vacancies})
        active_vacancies = []
        for shift in shifts:
            for active_date in shift.active_dates:
                if current_date <= active_date < next_day:
                    active_vacancies.append(shift.vacancy)
        filters = {'id__in': [item.id for item in active_vacancies]}

        return self.filter_by_kwargs(kwargs=filters, order_by=order_params, paginator=pagination)

    def single_vacancy_active_dates_list_for_manager(self, record_id, calendar_from=None, calendar_to=None):
        vacancy = self.get_by_id_for_manager_or_security(record_id=record_id)
        shifts = ShiftsRepository(calendar_from=calendar_from, calendar_to=calendar_to).filter_by_kwargs(
            kwargs={'vacancy': vacancy})
        return ShiftsRepository().active_dates(queryset=shifts)

    def vacancies_active_dates_list_for_manager(self, calendar_from=None, calendar_to=None):
        vacancies = self.queryset_by_manager()
        shifts = ShiftsRepository(calendar_from=calendar_from, calendar_to=calendar_to).filter_by_kwargs(
            kwargs={'vacancy_id__in': vacancies})
        return ShiftsRepository().active_dates(queryset=shifts)

    def vacancy_shifts_with_appeals_queryset(self, record_id, pagination=None, current_date=None, next_day=None):
        # active_shifts = []
        vacancy = self.get_by_id_for_manager_or_security(record_id=record_id)
        # shifts = ShiftsRepository(calendar_from=current_date, calendar_to=next_day).filter_by_kwargs(
        #     kwargs={**filters, **{
        #         'vacancy_id': vacancy.id
        #     }},
        #     paginator=pagination)

        shifts = ShiftsRepository(
            calendar_from=current_date, calendar_to=next_day
        ).get_shifts_on_current_date_for_vacancy(
            vacancy=vacancy,
            current_date=current_date
        )

        if pagination:
            return shifts[pagination.offset:pagination.limit]
        return shifts

        # for shift in shifts:
        #     if len(shift.active_dates):
        #         for active_date in shift.active_dates:
        #             if active_date <= current_date < next_day:
        #                 active_shifts.append(shift)
        #                 break
        # return list(set(active_shifts))

    def get_suggestions(self, search, paginator=None):
        records = self.model.objects.exclude(deleted=True).annotate(
            similarity=TrigramSimilarity('title', search),
        ).filter(title__trigram_similar=search).order_by('-similarity')

        records = records.only('title').distinct().values_list('title', flat=True)
        return records[paginator.offset:paginator.limit] if paginator else records[:100]

    @staticmethod
    def fast_related_loading(queryset, point=None):
        """ Подгрузка зависимостей с 3 уровнями вложенности по ForeignKey + GenericRelation
            Vacancy + Media
            -> Shop + Media
            -> Distributor + Media
        """
        queryset = queryset.prefetch_related(
            # Подгрузка медиа для магазинов
            Prefetch(
                'media',
                queryset=MediaModel.objects.filter(
                    deleted=False,
                    type=MediaType.BANNER.value,
                    owner_ct_id=ContentType.objects.get_for_model(Vacancy).id,
                    format=MediaFormat.IMAGE.value
                ),
                to_attr='medias'
            )).prefetch_related(
            Prefetch(
                'shop',
                #  Подгрузка магазинов и вычисление расстояния от каждого до переданной точки
                queryset=Shop.objects.annotate(  # Вычисляем расстояние, если переданы координаты
                    distance=Distance('location', point) if point else Value(None, IntegerField())
                ).prefetch_related(
                    # Подгрузка медиа для магазинов
                    Prefetch(
                        'media',
                        queryset=MediaModel.objects.filter(
                            deleted=False,
                            type=MediaType.LOGO.value,
                            owner_ct_id=ContentType.objects.get_for_model(Shop).id,
                            format=MediaFormat.IMAGE.value
                        ),
                        to_attr='medias'
                    )).prefetch_related(
                    # Подгрузка торговых сетей для магазинов
                    Prefetch(
                        'distributor',
                        queryset=Distributor.objects.all().prefetch_related(
                            # Подгрузка медиа для торговых сетей
                            Prefetch(
                                'media',
                                queryset=MediaModel.objects.filter(
                                    deleted=False,
                                    type__in=[MediaType.LOGO.value, MediaType.BANNER.value],
                                    owner_ct_id=ContentType.objects.get_for_model(
                                        Distributor).id,
                                    format=MediaFormat.IMAGE.value
                                ),
                                to_attr='medias'
                            )
                        )
                    )
                )
            )
        )

        return queryset

    def map(self, kwargs, paginator=None, order_by: list = None):
        queryset = self.model.objects.exclude(deleted=True).filter(**kwargs).annotate(
            location=F('shop__location'),
            logo=Concat(
                Value(f"'{settings.MEDIA_URL}'", output_field=CharField()),
                Subquery(
                    MediaModel.objects.filter(
                        deleted=False,
                        owner_id=OuterRef('shop_id'),
                        type=MediaType.LOGO.value,
                        owner_ct_id=ContentType.objects.get_for_model(Shop).id,
                        format=MediaFormat.IMAGE.value
                    ).values('file')[:1],
                    output_field=CharField()
                )
            )
        )
        # Фильтрация по вхождению в область на карте
        if self.screen_diagonal_points:
            queryset = queryset.filter(
                shop__location__contained=ExpressionWrapper(
                    Envelope(  # BoundingCircle использовался для описывающего круга
                        MultiPoint(
                            self.screen_diagonal_points[0], self.screen_diagonal_points[1], srid=settings.SRID
                        )
                    ),
                    output_field=GeometryField()
                )
            )

        return self.clustering(queryset)

    def clustering(self, queryset):
        """
        :param queryset: Отфильтрованные по области на экране данные
        :return:
        """

        raw_sql = f'''
            WITH clusters AS (
                SELECT 
                    cid, 
                    ST_Collect(location) AS cluster_geometries, 
                    ST_Centroid (ST_Collect(location)) AS centroid,
                    ST_X(ST_Centroid (ST_Collect(location))) AS c_lon,
                    ST_Y(ST_Centroid (ST_Collect(location))) AS c_lat,
                    ARRAY_AGG(id) AS ids_in_cluster,
                    ST_NumGeometries(ST_Collect(location)) as clustered_count,
                    logo
                FROM (
                        SELECT 
                            id, 
                            ST_ClusterDBSCAN(
                                location, 
                                eps := ST_Distance(
                                    ST_GeomFromGeoJSON('{self.screen_diagonal_points[0].geojson}'),
                                    ST_GeomFromGeoJSON('{self.screen_diagonal_points[1].geojson}')
                                )/10.0, -- 1/10 диагонали
                                minpoints := {settings.CLUSTER_MIN_POINTS_COUNT}
                            ) OVER() AS cid, 
                            location,
                            logo
                        FROM 
                            (
                                {queryset.query}
                            ) external_subquery

                ) sq
                GROUP BY cid, logo
            ),

            computed AS (

                SELECT 
                    v.id,
                    v.title,
                    v.price,
--                     v.banner,
                    
                    s.address,
                    ST_X(s.location) AS lon,
                    ST_Y(s.location) AS lat,
                    ST_DistanceSphere(s.location, ST_GeomFromGeoJSON('{self.point.geojson}')) AS distance,
                    
                    c.logo,
                    c.cid, 
                    c.c_lat, 
                    c.c_lon, 
                    c.clustered_count 
                FROM app_market__vacancies v
                INNER JOIN "app_market__shops" s ON ( v."shop_id" = s."id" ) 
                JOIN clusters c ON (s.id=ANY(c.ids_in_cluster))
                LEFT JOIN app_media m ON (
                    s.id=m.owner_id
                )

            )

            SELECT * FROM (
                SELECT 
                    *,
                    ROW_NUMBER() OVER (PARTITION BY cid ORDER BY distance ASC) AS n
                FROM computed
            ) a
            WHERE n<={settings.CLUSTER_NESTED_ITEMS_COUNT}
        '''
        return self.model.objects.raw(raw_sql)

    @staticmethod
    def aggregate_stats(queryset):
        count = queryset.aggregate(
            result_count=Count('id'),
        )

        prices = Vacancy.objects.filter(deleted=False).values('price').order_by('price').annotate(
            count=Count('id'),
        ).aggregate(all_prices=ArrayAgg('price', ordering='price'), all_counts=ArrayAgg('count', ordering='price'))

        return {**count, **prices}

    def aggregate_distributors(self, queryset, pagination=None):
        annotated = queryset.values('shop__distributor').annotate(count=Count('shop__distributor')).order_by('-count')

        distributors_ids_list = annotated.values_list('shop__distributor', flat=True)
        records = Distributor.objects.filter(pk__in=distributors_ids_list)
        if distributors_ids_list:
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(distributors_ids_list)])
            records = records.order_by(preserved)

        return DistributorsRepository.fast_related_loading(  # Предзагрузка связанных сущностей
            queryset=records[pagination.offset:pagination.limit] if pagination else records,
            me=self.me
        )

    def toggle_like(self, vacancy):
        owner_ct = ContentType.objects.get_for_model(self.me)
        target_ct = ContentType.objects.get_for_model(vacancy)
        data = {
            'owner_ct_id': owner_ct.id,
            'owner_ct_name': owner_ct.model,
            'owner_id': self.me.id,
            'target_ct_id': target_ct.id,
            'target_ct_name': target_ct.model,
            'target_id': vacancy.id
        }

        like, crated = Like.objects.get_or_create(**data)
        if not crated:
            like.deleted = not like.deleted
            like.save()

    def get_similar(self, record_id, pagination=None):
        current_vacancy = self.model.objects.filter(pk=record_id, deleted=False).select_related('shop').first()
        if current_vacancy:
            result = self.base_query.annotate(
                similarity=TrigramSimilarity('title', current_vacancy.title),
                distance_from_current=Distance('shop__location', current_vacancy.shop.location)
                if current_vacancy.shop.location else Value(None, IntegerField())
            ).filter(
                deleted=False,
                similarity__gte=self.TRIGRAM_SIMILARITY_MIN_RATE,  # Минимальное сходство
                distance_from_current__lte=self.SIMILAR_VACANCIES_MAX_DISTANCE_M  # Расстояние от текущей вакансии
            ) \
                .exclude(pk=record_id) \
                .order_by('distance_from_current')

            if pagination:
                return result[pagination.offset:pagination.limit]
            return result

        return []

    def get_requirements(self, vacancy_id):
        vacancy = Vacancy.objects.get(pk=vacancy_id)
        required_experience = ''
        if vacancy.required_experience:
            for exp in vacancy.required_experience:
                if exp == WorkExperience.NO.value:
                    required_experience += 'Без опыта'
                    required_experience += '\n'
                if exp == WorkExperience.INVALID.value:
                    required_experience += 'С ограниченными возможностями'
                    required_experience += '\n'
                if exp == WorkExperience.UNDERAGE.value:
                    required_experience += 'До 18 лет'
                    required_experience += '\n'
                if exp == WorkExperience.MIDDLE.value:
                    required_experience += '1-3 года опыта'
                    required_experience += '\n'
                if exp == WorkExperience.STRONG.value:
                    required_experience += 'Более 3 лет опыта'
                    required_experience += '\n'

        employment = ''
        if vacancy.employment == VacancyEmployment.PARTIAL.value:
            employment = 'Частичная занятость'
        if vacancy.employment == VacancyEmployment.FULL.value:
            employment = 'Полная занятость'

        text = ''
        if vacancy.requirements:
            text += f'Требования: {vacancy.requirements}\n'
        if required_experience:
            text += f'Требуемый опыт: {required_experience}\n'
        if vacancy.features:
            text += f'Бонусы: {vacancy.features}\n'
        if employment:
            text += f'Тип занятости: {employment}'

        return text

    def get_necessary_docs(self, vacancy_id):
        vacancy = Vacancy.objects.get(pk=vacancy_id)
        required_docs = ''
        if not vacancy.required_docs:
            return required_docs
        for doc in vacancy.required_docs:
            if doc == DocumentType.OTHER.value:
                required_docs += 'Другие документы'
                required_docs += '\n'
            if doc == DocumentType.PASSPORT.value:
                required_docs += 'Паспорт'
                required_docs += '\n'
            if doc == DocumentType.INN.value:
                required_docs += 'ИНН'
                required_docs += '\n'
            if doc == DocumentType.SNILS.value:
                required_docs += 'СНИЛС'
                required_docs += '\n'
            if doc == DocumentType.DRIVER_LICENCE.value:
                required_docs += 'Водительское удостоверение'
                required_docs += '\n'
            if doc == DocumentType.MEDICAL_BOOK.value:
                required_docs += 'Медицинская книжка'
                required_docs += '\n'

        return required_docs

    def check_if_has_confirmed_appeals(self, subject_user, vacancy_id):
        return ShiftAppeal.objects.filter(
            applier=subject_user,
            shift__vacancy_id=vacancy_id,
            status=ShiftAppealStatus.CONFIRMED.value,
            time_start__gt=now()
        ).exists()

    def get_shift_remaining_time_to_start(self, subject_user, vacancy_id):
        # Только подтвержденные заявки
        earlier_confirmed_appeal = ShiftAppeal.objects.filter(
            applier=subject_user,
            shift__vacancy_id=vacancy_id,
            status=ShiftAppealStatus.CONFIRMED.value,
            time_start__gt=now()
        ).order_by('-time_start').first()

        if earlier_confirmed_appeal:
            # TODO учитывать часовые пояса
            timedelta()
            delta = earlier_confirmed_appeal.time_start - now()
            seconds = delta.total_seconds()

            week = 3600 * 24 * 7
            day = 3600 * 24
            hour = 3600
            minute = 60

            weeks = seconds // week
            seconds -= weeks * week
            days = seconds // day
            seconds -= days * day
            hours = seconds // hour
            seconds -= hours * hour
            minutes = seconds // minute
            seconds -= minutes * minute

            time_str = 'Ваша смена начнётся через '

            if weeks:
                time_str += f'{int(weeks)} нед. '
            if days:
                time_str += f'{int(days)} д. '
            if hours:
                time_str += f'{int(hours)} ч. '
            if minutes:
                time_str += f'{int(minutes)} м. '

            time_str += f'{int(seconds)} c. '

            return time_str
        return None

    def get_managers_and_sockets_for_vacancy(self, vacancy: Vacancy):
        sockets = []
        managers = vacancy.shop.staff.filter(account_type=AccountType.MANAGER.value)

        if managers:
            # TODO учитывать настройки отпуска для менеджера
            sockets = managers.aggregate(
                sockets=ArrayRemove(ArrayAgg('sockets__socket_id'), None)
            )['sockets']

        return managers, sockets


class AsyncVacanciesRepository(VacanciesRepository):
    def __init__(self, me=None) -> None:
        super().__init__()
        self.me = me

    @database_sync_to_async
    def get_by_id(self, record_id):
        return super().get_by_id(record_id)


class ShiftAppealsRepository(MasterRepository):
    model = ShiftAppeal

    def __init__(self, me=None, point=None):
        super().__init__()
        self.me = me
        self.point = point

        self.base_query = self.model.objects.filter(applier=self.me)

        self.limit = 10

    @staticmethod
    def fast_related_loading(queryset, point=None):
        """ Подгрузка зависимостей с 3 уровнями вложенности по ForeignKey + GenericRelation
            ShiftAppeal
            -> Vacancy + Media
                -> Shop + Media

            TODO предзагрузка медиа

                .prefetch_related(
            Prefetch(
                'shop',
                #  Подгрузка магазинов и вычисление расстояния от каждого до переданной точки
                queryset=Shop.objects.annotate(  # Вычисляем расстояние, если переданы координаты
                    distance=Distance('location', point) if point else Value(None, IntegerField())
                ).prefetch_related(
                    # Подгрузка медиа для магазинов
                    Prefetch(
                        'media',
                        queryset=MediaModel.objects.filter(
                            type=MediaType.LOGO.value,
                            owner_ct_id=ContentType.objects.get_for_model(Shop).id,
                            format=MediaFormat.IMAGE.value
                        ),
                        to_attr='medias'
                    )
                )
            )
        )

        """
        queryset = queryset.select_related(
            'shift__vacancy'
        ).prefetch_related(
            Prefetch(
                'shift__vacancy__shop',
                queryset=Shop.objects.filter().annotate(
                    distance=Distance('location', point) if point else Value(None, IntegerField())
                )
            )
        )

        return queryset

    def get_by_qr_text(self, qr_text):
        try:
            return self.model.objects.get(qr_text=qr_text)
        except self.model.DoesNotExist:
            raise HttpException(detail='Appeal not found', status_code=RESTErrors.NOT_FOUND.value)

    @staticmethod
    def get_start_end_time_range(**data):

        shift = data.get('shift')
        if not shift.time_start or not shift.time_end:
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.SHIFT_WITHOUT_TIME))
            ])

        shift_active_date = data.get('shift_active_date')
        time_start = handle_date_for_appeals(shift=shift, shift_active_date=shift_active_date)
        if time_start <= datetime.now():
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.SHIFT_OVERDUE))
            ])

        time_end = handle_date_for_appeals(shift=shift, shift_active_date=shift_active_date, by_end=True)

        return time_start, time_end

    @staticmethod
    def check_if_exists(queryset, data):
        appeal = queryset.filter(**data).first()
        if appeal:
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.APPEAL_EXISTS))
            ])

    @staticmethod
    def check_if_already_completed(appeal):
        if appeal.job_status == JobStatus.COMPLETED.value:
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.APPEAL_ALREADY_COMPLETED))
            ])

    @staticmethod
    def cancel_appeal(appeal):
        if appeal.status == ShiftAppealStatus.CANCELED.value:
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.APPEAL_ALREADY_CANCELLED))
            ])
        appeal.status = ShiftAppealStatus.CANCELED.value
        appeal.save()

    def set_completed_status(self, appeal):
        self.check_if_already_completed(appeal=appeal)
        appeal.status = ShiftAppealStatus.COMPLETED.value
        appeal.save()

    def set_job_completed_status(self, appeal, **data):
        self.check_if_already_completed(appeal=appeal)

        appeal.complete_reason = data.get('reason')
        appeal.complete_reason_text = data.get('text')

        appeal.job_status = JobStatus.COMPLETED.value
        appeal.completed_real_time = now()
        # TODO Прикрутить логику по расчетам выплаты и все такое
        #  Логика расчета выплаты: оплачиваем только полностью отработанные часы + неполные часы из расчета:
        #  1-30 минут ставка за час\2, 31-60 минут ставка за час.
        appeal.save()

    def check_time_range(self, queryset, time_start, time_end):
        if queryset.filter(
                status__in=[ShiftAppealStatus.INITIAL.value, ShiftAppealStatus.CONFIRMED.value]
        ).filter(
            Q(time_start__range=(time_start, time_end)) | Q(time_end__range=(time_start, time_end))
        ).count() >= self.limit:
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.APPEALS_LIMIT_REACHED))
            ])

    def update_data(self, data):
        time_start, time_end = self.get_start_end_time_range(**data)
        data.update({
            'applier': self.me,
            'time_start': time_start,
            'time_end': time_end
        })
        return data

    def get_or_create(self, **data):
        time_start, time_end = self.get_start_end_time_range(**data)
        data = self.update_data(data=data)

        queryset = self.base_query

        # проверяем наличие отклика в бд
        self.check_if_exists(queryset=queryset, data={
            **data,
            **{
                # Проверяем только отклики новые или подтвержденные
                'status__in': [ShiftAppealStatus.INITIAL.value, ShiftAppealStatus.CONFIRMED.value]
            }
        })

        # проверяем количество откликов на разные смены в одинаковое время
        self.check_time_range(queryset=queryset, time_start=time_start, time_end=time_end)

        instance, created = self.model.objects.get_or_create(defaults={
            'status': ShiftAppealStatus.INITIAL.value
        }, **{
            **data,
            **{
                # Проверяем только отклики новые или подтвержденные
                'status__in': [ShiftAppealStatus.INITIAL.value, ShiftAppealStatus.CONFIRMED.value]
            }
        })
        return instance, created

    def get_by_id(self, record_id):
        # если будет self.base_query.filter() то manager ничего не сможет увидеть
        records = self.model.objects.filter(pk=record_id)
        records = self.fast_related_loading(  # Предзагрузка связанных сущностей
            queryset=records,
            point=self.point
        )
        record = records.first()
        if not record:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден')

        return record

    def filter_by_kwargs(self, kwargs, paginator=None, order_by: list = None):
        if order_by:
            records = self.base_query.order_by(*order_by).exclude(deleted=True).filter(**kwargs)
        else:
            records = self.base_query.exclude(deleted=True).filter(**kwargs)

        return self.fast_related_loading(  # Предзагрузка связанных сущностей
            queryset=records[paginator.offset:paginator.limit] if paginator else records,
            point=self.point
        )

    def update(self, record_id, **data):

        time_start, time_end = self.get_start_end_time_range(**data)
        data = self.update_data(data=data)

        queryset = self.base_query

        # проверяем наличие отклика в бд
        self.check_if_exists(queryset=queryset, data=data)

        # проверяем количество откликов на разные смены в одинаковое время
        self.check_time_range(queryset=queryset, time_start=time_start, time_end=time_end)

        return super().update(record_id, **data)

    def delete(self, record_id):
        instance = self.get_by_id(record_id=record_id)
        if not instance.applier == self.me:
            raise PermissionDenied()
        instance.deleted = True
        instance.save()

    def cancel(self, record_id, reason=None, text=None):
        is_confirmed_appeal_canceled = False
        instance = self.get_by_id(record_id=record_id)
        if instance.applier != self.me:
            raise PermissionDenied()

        if instance.status == ShiftAppealStatus.CONFIRMED.value:
            # Если подтвержденный отклик
            is_confirmed_appeal_canceled = True

        instance.status = ShiftAppealStatus.CANCELED.value
        if reason is not None and instance.cancel_reason is None:
            instance.cancel_reason = reason
            instance.reason_text = text
        instance.save()

        return instance, is_confirmed_appeal_canceled

    @staticmethod
    def check_if_active_appeal(vacancy_id, applier_id):
        return ShiftAppeal.objects.filter(
            applier_id=applier_id,
            shift__vacancy__id=vacancy_id,
            # status__in=[ShiftAppealStatus.INITIAL.value] # TODO нужно ли учитывать все заявки при создании чата
        ).exists()

    def is_related_security(self, instance):
        if self.me.account_type == AccountType.SECURITY.value and \
                instance.shift.vacancy.shop not in self.me.shops.all():
            raise PermissionDenied()

    def is_related_manager(self, instance):
        if self.me.account_type == AccountType.MANAGER.value and instance.shift.vacancy.shop not in self.me.shops.all():
            raise PermissionDenied()

    def confirm_by_manager(self, record_id):
        instances = self.model.objects.filter(id=record_id)

        if not instances:
            raise HttpException(detail=f'Отклик с ID={record_id} не найден', status_code=RESTErrors.NOT_FOUND.value)
        instances = self.prefetch_users(instances)

        instance = instances.first()

        status_changed = False
        manager_and_user_sockets = []

        # проверяем доступ менеджера к смене на которую откликнулись
        # self.is_related_manager(instance=instance)

        if not instance.status == ShiftAppealStatus.CONFIRMED:
            instance.status = ShiftAppealStatus.CONFIRMED
            instance.save()
            # удаляем остальные отклики пользователя
            self.model.objects.filter(applier=instance.applier).filter(
                Q(time_start__range=(instance.time_start, instance.time_end)) |
                Q(time_end__range=(instance.time_start, instance.time_end))
            ).exclude(id=instance.id).delete()

            # # создаем смену пользователя
            # UserShift.objects.get_or_create(
            #     user=instance.applier,
            #     shift=instance.shift,
            #     real_time_start=instance.time_start,
            #     real_time_end=instance.time_end
            # )

            status_changed = True
            manager_and_user_sockets += instance.applier.sockets.aggregate(
                sockets=ArrayAgg('socket_id')
            )['sockets']
            manager_and_user_sockets += self.me.sockets.aggregate(
                sockets=ArrayAgg('socket_id')
            )['sockets']

        return status_changed, manager_and_user_sockets, instance

    def reject_by_manager(self, record_id, reason, text=None):
        status_changed = False
        instances = self.model.objects.filter(id=record_id)

        if not instances:
            raise HttpException(detail=f'Отклик с ID={record_id} не найден', status_code=RESTErrors.NOT_FOUND.value)
        instances = self.prefetch_users(instances)

        instance = instances.first()

        manager_and_user_sockets = []

        # проверяем доступ менеджера к смене на которую откликнулись
        self.is_related_manager(instance=instance)
        if not instance.status == ShiftAppealStatus.REJECTED:
            instance.status = ShiftAppealStatus.REJECTED
            instance.manager_cancel_reason = reason
            instance.cancel_reason_text = text
            instance.save()

            status_changed = True
            manager_and_user_sockets += instance.applier.sockets.aggregate(
                sockets=ArrayAgg('socket_id')
            )['sockets']
            manager_and_user_sockets += self.me.sockets.aggregate(
                sockets=ArrayAgg('socket_id')
            )['sockets']

        return status_changed, manager_and_user_sockets, instance

    def get_by_id_for_manager(self, record_id):
        instance = self.get_by_id(record_id=record_id)

        # проверяем доступ менеджера
        self.is_related_manager(instance=instance)
        return instance

    def get_by_qr_text_for_manager(self, qr_text):
        instance = self.get_by_qr_text(qr_text=qr_text)

        # проверяем доступ менеджера
        self.is_related_manager(instance=instance)

        # меняем статус
        if instance.job_status == JobStatus.JOB_SOON.value:
            instance.job_status = JobStatus.JOB_IN_PROCESS.value
            instance.save()

    def get_new_confirmed_count(self):
        return 0

    def get_new_appeals_count(self):
        return 0

    def check_permission_for_appeal(self, shift_id):
        #  Проверяем не заблокирован ли чат с магазином, в которой есть вакансия, или чат с самой вакансией
        s = Shift.objects.filter(id=shift_id).select_related('vacancy').first()
        vacancy_ct = ContentType.objects.get_for_model(Vacancy)
        shop_ct = ContentType.objects.get_for_model(Shop)
        if ChatUser.objects.filter(
                # Ищем чаты где я - subject_user, и мою запись ChatUser где blocked_at не пусто
                Q(chat__subject_user=self.me, user=self.me, blocked_at__isnull=False) &
                (
                        # Чат должен быть либо по вакансии
                        Q(chat__target_ct=vacancy_ct, chat__target_id=s.vacancy_id) |
                        # Либо по магазину
                        Q(chat__target_ct=shop_ct, chat__target_id=s.vacancy.shop_id)
                )
        ).exists():
            return False
        return True

    def get_shift_appeals_for_managers(self, shift_id, active_date=None, filters={}):
        date = timestamp_to_datetime(
            int(active_date)) if active_date is not None else now()  # По умолчанию текущий день

        shift = Shift.objects.filter(id=shift_id).select_related('vacancy').first()
        vacancy_timezone_name = shift.vacancy.timezone if shift.vacancy.timezone else 'Europe/Moscow'

        filtered = self.model.objects.filter(**{**filters, **{'shift_id': shift_id}})
        appeals = filtered.filter(
            shift_active_date__datetz=localtime(
                date, timezone=timezone(vacancy_timezone_name)  # Даты высчитываем в часовых поясах вакансий
            ).date(),
        ).select_related(
            'shift__vacancy'
        )

        appeals = self.prefetch_users(appeals)

        return appeals

    @staticmethod
    def handle_pass_data(appeal):
        series = None
        document = Document.objects.filter(user=appeal.applier, type=DocumentType.PASSPORT.value).first()
        if document:
            series = document.series

        data = {
            'appeal_id': appeal.id,
            'job_status': appeal.job_status,
            'passport': series,
            'position': appeal.shift.vacancy.title,
            'address': appeal.shift.vacancy.shop.address
        }
        return data

    def handle_pass_data_for_self_employed(self, appeal):
        if appeal.applier != self.me:
            raise PermissionDenied()

        return self.handle_pass_data(appeal=appeal)

    def handle_pass_data_for_security(self, qr_text):
        appeal = self.get_by_qr_text(qr_text=qr_text)
        self.is_related_security(instance=appeal)
        appeal.security_qr_scan_time = now()
        appeal.save()
        return self.handle_pass_data(appeal=appeal)

    def handle_pass_data_for_manager(self, qr_text):
        appeal = self.get_by_qr_text(qr_text=qr_text)
        self.is_related_manager(instance=appeal)
        appeal.manager_qr_scan_time = now()
        appeal.save()
        return self.handle_pass_data(appeal=appeal)

    def allow_pass_by_manager(self, record_id):
        appeal = self.get_by_id(record_id=record_id)
        self.is_related_manager(instance=appeal)
        if appeal.job_status == JobStatus.JOB_SOON.value:
            appeal.job_status = JobStatus.JOB_IN_PROCESS.value
            appeal.qr_text = None
            appeal.save()
            sockets = appeal.applier.sockets.aggregate(
                sockets=ArrayRemove(ArrayAgg('socket_id'), None)
            )['sockets']
            return appeal, sockets
        else:
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.INCONVENIENT_JOB_STATUS))
            ])

    def refuse_pass_by_security(self, record_id, validated_data):
        appeal = self.get_by_id(record_id=record_id)
        self.is_related_security(instance=appeal)
        if appeal.job_status == JobStatus.JOB_SOON.value:
            appeal.security_pass_refuse_reason = validated_data.get('reason')
            appeal.security_pass_refuse_reason_text = validated_data.get('text')
            appeal.save()
            sockets = appeal.applier.sockets.aggregate(
                sockets=ArrayRemove(ArrayAgg('socket_id'), None)
            )['sockets']
            return appeal, sockets
        else:
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.INCONVENIENT_JOB_STATUS))
            ])

    def refuse_pass_by_manager(self, record_id, validated_data):
        appeal = self.get_by_id(record_id=record_id)
        self.is_related_manager(instance=appeal)
        if appeal.job_status == JobStatus.JOB_SOON.value:
            appeal.job_status = None
            appeal.status = ShiftAppealStatus.CANCELED.value
            appeal.manager_refuse_reason = validated_data.get('reason')
            appeal.refuse_reason_text = validated_data.get('text')
            appeal.qr_text = None
            appeal.save()
            sockets = appeal.applier.sockets.aggregate(
                sockets=ArrayRemove(ArrayAgg('socket_id'), None)
            )['sockets']
            return appeal, sockets
        else:
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.INCONVENIENT_JOB_STATUS))
            ])

    def handle_qr_related_data(self):
        job_status = JobStatusForClient.NO_JOB.value
        qr_text = None
        qr_pass = None
        leave_time = None
        appeal = None
        confirmed_appeals = self.model.objects.filter(
            applier=self.me,
            status=ShiftAppealStatus.CONFIRMED.value
        )

        if confirmed_appeals.exists():
            appeal_having_job_status = confirmed_appeals.filter(job_status__isnull=False).select_related(
                'shift', 'shift__vacancy', 'shift__vacancy__shop'
            ).first()
            if appeal_having_job_status:
                job_status = appeal_having_job_status.job_status
                appeal = appeal_having_job_status
                if appeal.job_status == JobStatus.JOB_IN_PROCESS.value:
                    qr_pass = self.handle_pass_data_for_self_employed(appeal=appeal_having_job_status)
                elif job_status == JobStatus.COMPLETED.value:
                    leave_time = appeal_having_job_status.completed_real_time + timedelta(minutes=15)
                    leave_time = datetime_to_timestamp(leave_time)
                else:
                    qr_text = appeal_having_job_status.qr_text
            else:
                job_status = JobStatusForClient.JOB_NOT_SOON.value
                appeal = confirmed_appeals.select_related(
                    'shift', 'shift__vacancy', 'shift__vacancy__shop'
                ).earliest('time_start')
        return job_status, qr_text, qr_pass, leave_time, appeal

    def complete_appeal(self, record_id, **data):
        appeal = self.get_by_id(record_id=record_id)
        if self.me != appeal.applier:
            raise PermissionDenied()

        self.set_completed_status(appeal=appeal)
        sockets = appeal.applier.sockets.aggregate(
            sockets=ArrayRemove(ArrayAgg('socket_id'), None)
        )['sockets']
        return appeal, sockets

    def complete_appeal_by_manager(self, **data):
        # Сценарий 3: Самозанятый во время смены просит его отпустить пораньше
        # (для любых случаев, когда самозанятого отпускают и оплатят часть денег)
        # В данном случае самозанятый не обязан сканировать QR для завершения смены.
        appeal = self.get_by_qr_text(qr_text=data.get('qr_text'))
        self.is_related_manager(instance=appeal)
        self.set_job_completed_status(appeal=appeal, **data)
        sockets = appeal.applier.sockets.aggregate(
            sockets=ArrayRemove(ArrayAgg('socket_id'), None)
        )['sockets']
        return appeal, sockets

    def fire_by_manager(self, record_id, validated_data):
        # Сценарий когда менеджер увольняет кого-то
        appeal = self.get_by_id(record_id=record_id)
        self.is_related_manager(instance=appeal)
        self.cancel_appeal(appeal=appeal)
        appeal.manager_fire_reason = validated_data.get('reason')
        appeal.fire_reason_text = validated_data.get('text')
        appeal.save()
        sockets = appeal.applier.sockets.aggregate(
            sockets=ArrayRemove(ArrayAgg('socket_id'), None)
        )['sockets']
        return appeal, sockets

    def prolong_by_manager(self, record_id, validated_data):
        # Сценарий когда менеджер увольняет кого-то
        appeal = self.get_by_id(record_id=record_id)
        self.is_related_manager(instance=appeal)
        self.cancel_appeal(appeal=appeal)
        appeal.time_end = appeal.time_end + timedelta(hours=validated_data.get('hours'))
        appeal.save()
        sockets = appeal.applier.sockets.aggregate(
            sockets=ArrayRemove(ArrayAgg('socket_id'), None)
        )['sockets']
        return appeal, sockets

    @staticmethod
    def prefetch_users(queryset):
        user_ct = ContentType.objects.get_for_model(UserProfile)
        return queryset.prefetch_related(  # Префетчим заявителя
            Prefetch(
                'applier',
                queryset=UserProfile.objects.filter(
                    account_type=AccountType.SELF_EMPLOYED.value
                ).prefetch_related(  # Префетчим аватарку заявителя
                    Prefetch(
                        'media',
                        queryset=MediaModel.objects.filter(
                            deleted=False,
                            owner_ct_id=user_ct.id,
                            type=MediaType.AVATAR.value,
                            format=MediaFormat.IMAGE.value,
                        ).order_by('-created_at'),
                        to_attr='medias'  # Подгружаем аватарки в поле medias
                    )
                ).prefetch_related(
                    Prefetch(
                        'appeals',
                        queryset=ShiftAppeal.objects.all().select_related(  # Все отклики
                            'shift__vacancy'  # Догружаем смены->вакансии
                        ).annotate(  # Вычисляем рейтинг для каждой смены
                            rates_count=Subquery(
                                Review.objects.filter(
                                    target_ct=user_ct,
                                    target_id=OuterRef('applier'),
                                    shift_id=OuterRef('shift'),
                                ).annotate(  # Если нет оценок то будет null
                                    count=Window(
                                        expression=Count('id'), partition_by=[F('shift_id')])
                                ).values('count')[:1]
                            ),
                            rating=Subquery(
                                Review.objects.filter(
                                    target_ct=user_ct,
                                    target_id=OuterRef('applier'),
                                    shift_id=OuterRef('shift'),
                                ).annotate(  # Если нет оценок то будет null
                                    rating=Window(
                                        expression=Avg('value'), partition_by=[F('shift_id')])
                                ).values('rating')[:1]
                            )
                        ).annotate(
                            total_rates_count=Coalesce(Window(  # Если null, то ставим 0
                                expression=Sum('rates_count'), partition_by=[F('shift__vacancy_id')]), 0
                            ),
                            total_rating=Coalesce(Window(  # Если null, то ставим 0
                                expression=Avg('rating'), partition_by=[F('shift__vacancy_id')]), 0
                            ),
                            vacancy_title=F('shift__vacancy__title'),
                            vacancy_id=F('shift__vacancy_id')
                        ),
                        to_attr='shifts'
                    )
                ).annotate(  # Аггрегируем коды документов, которые есть у пользователя
                    documents_types=ArrayRemove(ArrayAgg('documents__type', distinct=True), None),
                )
            )
        )

    def bulk_cancel(self):
        # закрытие неподтвержденных смен, у которых уже прошло время начала

        # Переводим в list ид откликов, чтобы они не перетерлись после .update()
        appeals_ids = list(self.model.objects.annotate(
            timezone=F('shift__vacancy__timezone')
        ).filter(
            status=ShiftAppealStatus.INITIAL.value,
            time_start__ltedttz=now()  # сравнивается время вакансии в ее часовом поясе
        ).values_list('id', flat=True))

        self.model.objects.filter(
            id__in=appeals_ids
        ).update(status=ShiftAppealStatus.CANCELED.value)

        appeals = self.model.objects.filter(
            id__in=appeals_ids
        ).prefetch_related(
            Prefetch(
                'applier',
                queryset=UserProfile.objects.filter(account_type=AccountType.SELF_EMPLOYED.value).annotate(
                    sockets_array=ArrayRemove(ArrayAgg('sockets__socket_id'), None)
                )
            )
        )

        # Нужны заявители, которым отправлять данные по сокетам и по пушам
        return appeals

    def bulk_cancel_with_job_soon_status(self):
        # Сценарий 1: Смена началась, QR для начала смены не отсканирован.
        # В данном случае оставляем отклонение на менеджере,
        # чтобы не было ситуации, когда менеджер опоздал к началу смены и все отклики автоматически отклонились.
        # В таком случае, самозанятый замотивирован найти менеджера, чтобы отсканировать QR,
        # а менеджер уволить, если cамозанятый не явился.
        # Если оба оказываются безответственными, то отклик автоматически отменяется в конце смены.
        appeals_ids = list(self.model.objects.annotate(
            timezone=F('shift__vacancy__timezone')
        ).filter(
            status=ShiftAppealStatus.CONFIRMED,
            job_status=JobStatus.JOB_SOON.value,
            qr_text__isnull=False,
            time_end__ltedttz=now()
        ).values_list('id', flat=True))

        self.model.objects.filter(id__in=appeals_ids).update(
            status=ShiftAppealStatus.CANCELED.value,
            qr_text=None
        )

        appeals = self.model.objects.filter(id__in=appeals_ids).prefetch_related(
            Prefetch(
                'applier',
                queryset=UserProfile.objects.filter(account_type=AccountType.SELF_EMPLOYED.value).annotate(
                    sockets_array=ArrayRemove(ArrayAgg('sockets__socket_id'), None)
                )
            )
        )

        return appeals

    def bulk_set_job_soon_status(self):
        soon = now() + timedelta(minutes=30)

        appeals_ids = list(self.model.objects.annotate(
            timezone=F('shift__vacancy__timezone')
        ).filter(
            status=ShiftAppealStatus.CONFIRMED,
            job_status__isnull=True,
            time_start__ltdttz=soon,
            time_start__gtdttz=now(),
        ).values_list('id', flat=True))

        self.model.objects.filter(id__in=appeals_ids).update(
            qr_text=ExpressionWrapper(
                Concat(Value('userId='), F('applier_id'), Value('&appealId='), F('id')),
                output_field=CharField()
            ),
            job_status=JobStatus.JOB_SOON.value
        )

        upcoming_appeals = self.model.objects.filter(id__in=appeals_ids).prefetch_related(
            Prefetch(
                'applier',
                queryset=UserProfile.objects.filter(account_type=AccountType.SELF_EMPLOYED.value).annotate(
                    sockets_array=ArrayRemove(ArrayAgg('sockets__socket_id'), None)
                )
            )
        )

        return upcoming_appeals

    def bulk_set_waiting_for_completion_status(self):
        appeals_ids = list(self.model.objects.annotate(
            timezone=F('shift__vacancy__timezone')
        ).filter(
            status=ShiftAppealStatus.CONFIRMED,
            job_status=JobStatus.JOB_IN_PROCESS.value,
            time_end__ltdttz=now()
        ).values_list('id', flat=True))

        self.model.objects.filter(id__in=appeals_ids).update(
            qr_text=ExpressionWrapper(
                Concat(Value('userId='), F('applier_id'), Value('&appealId='), F('id')),
                output_field=CharField()
            ),
            job_status=JobStatus.WAITING_FOR_COMPLETION.value
        )

        appeals = self.model.objects.filter(id__in=appeals_ids).prefetch_related(
            Prefetch(
                'applier',
                queryset=UserProfile.objects.filter(account_type=AccountType.SELF_EMPLOYED.value).annotate(
                    sockets_array=ArrayRemove(ArrayAgg('sockets__socket_id'), None)
                )
            ),
            Prefetch(
                # TODO учитывать настройки отпуска у менеджера
                'shift__vacancy__shop__staff',
                queryset=UserProfile.objects.filter(account_type=AccountType.MANAGER.value, deleted=False).annotate(
                    sockets_array=ArrayRemove(ArrayAgg('sockets__socket_id'), None)
                ),
                to_attr='relevant_managers'
            )
        )

        # TODO relevant managers

        return appeals

        # TODO уведомление (скорее всего и менеджеру и пользователю)

    def bulk_set_job_completed_status(self):
        # Сценарий 2: Смена закончилась, QR для завершения смены не отсканирован.
        # В данном случае, если ситуация по вине менеджера, то по истечении 1 часа после завершения смены,
        # она автоматически переходит в статус Завершена и отрабатывается метод для выплаты денег.
        # Если по вине самозанятого, то у менеджера есть час, чтобы решить вопрос
        # (продлить смену или вернуть человека) или уволить.
        interval = timedelta(hours=1)

        appeals_ids = list(self.model.objects.annotate(
            timezone=F('shift__vacancy__timezone')
        ).filter(
            status=ShiftAppealStatus.CONFIRMED.value,
            job_status=JobStatus.WAITING_FOR_COMPLETION.value,
            time_end__ltdttz=now() - interval
        ).values_list('id', flat=True))

        self.model.objects.filter(id__in=appeals_ids).update(
            job_status=JobStatus.COMPLETED.value,
            # status=ShiftAppealStatus.COMPLETED.value,
            completed_real_time=now()
        )

        appeals_to_complete = self.model.objects.filter(id__in=appeals_ids).prefetch_related(
            Prefetch(
                'applier',
                queryset=UserProfile.objects.filter(account_type=AccountType.SELF_EMPLOYED.value).annotate(
                    sockets_array=ArrayRemove(ArrayAgg('sockets__socket_id'), None)
                )
            ),
            Prefetch(
                # TODO учитывать настройки отпуска у менеджера
                'shift__vacancy__shop__staff',
                queryset=UserProfile.objects.filter(account_type=AccountType.MANAGER.value, deleted=False).annotate(
                    sockets_array=ArrayRemove(ArrayAgg('sockets__socket_id'), None)
                ),
                to_attr='relevant_managers'
            )
        )

        return appeals_to_complete

    def bulk_set_completed_status(self):
        # После завершения смены есть таймер 15 минут, по истечении времени переводить статус в COMPLETE
        interval = timedelta(minutes=15)

        appeals_ids = list(self.model.objects.annotate(
            timezone=F('shift__vacancy__timezone')
        ).filter(
            status=ShiftAppealStatus.CONFIRMED.value,
            job_status=JobStatus.COMPLETED.value,
            completed_real_time__ltdttz=now() - interval
        ).values_list('id', flat=True))

        self.model.objects.filter(id__in=appeals_ids).update(
            status=ShiftAppealStatus.COMPLETED.value,
        )

    @staticmethod
    def modify_order_for_confirmed_workers(order_by):
        if 'shift__time_start' in order_by:
            order_by.append('shift__time_end')
        if '-shift__time_start' in order_by:
            order_by.append('-shift__time_end')

    def get_confirmed_workers_for_manager(self, current_date, pagination=None, order_by: list = None, filters={}):
        result = self.model.objects.annotate(
            timezone=F('shift__vacancy__timezone')
        ).filter(
            shift__shop__in=self.me.shops.all(),
            status=ShiftAppealStatus.CONFIRMED.value,
            shift_active_date__datetz=timestamp_to_datetime(int(current_date)).date() if current_date else None,
            **filters
        ).select_related(
            'shift__vacancy'
        )
        if order_by:
            # Добавляем двойную сортировку, так как у смены есть time_start и time_end
            self.modify_order_for_confirmed_workers(order_by)
            result = result.order_by(*order_by)
        if pagination:
            return result[pagination.offset: pagination.limit]
        return result

    def get_confirmed_workers_dates_for_manager(self, calendar_from, calendar_to):
        result = self.model.objects.annotate(
            timezone=F('shift__vacancy__timezone')
        ).filter(
            shift__shop__in=self.me.shops.all(),
            status=ShiftAppealStatus.CONFIRMED.value,
            shift_active_date__datetz_gte=calendar_from.date(),
            shift_active_date__datetz_lte=calendar_to.date(),
        ).select_related(
            'shift__vacancy'
        ).distinct('shift_active_date', 'shift__vacancy__timezone').order_by('shift_active_date')
        return result

    def get_confirmed_workers_professions_for_manager(
            self, current_date, pagination=None, order_by: list = None, filters={}
    ):
        result = self.model.objects.annotate(
            timezone=F('shift__vacancy__timezone')
        ).filter(
            shift__shop__in=self.me.shops.all(),
            status=ShiftAppealStatus.CONFIRMED.value,
            shift_active_date__datetz=timestamp_to_datetime(int(current_date)).date() if current_date else None,
            **filters
        ).select_related(
            'shift__vacancy'
        ).distinct('shift__vacancy__profession')
        if order_by:
            result = result.order_by(*order_by)
        if pagination:
            return result[pagination.offset: pagination.limit]
        return result


class AsyncShiftAppealsRepository(ShiftAppealsRepository):
    def __init__(self, me=None, point=None):
        super().__init__()
        self.me = me
        self.point = point

    @database_sync_to_async
    def get_new_confirmed_count(self):
        return super().get_new_confirmed_count()

    @database_sync_to_async
    def get_new_appeals_count(self):
        return super().get_new_appeals_count()


class ProfessionsRepository(MasterRepository):
    model = Profession

    def add_suggested_profession(self, name):
        self.model.objects.create(name=name, is_suggested=True)


class SkillsRepository(MasterRepository):
    model = Skill


class MarketDocumentsRepository(MasterRepository):
    def __init__(self, me=None):
        super().__init__()
        self.me = me

    _SERVICE_TAX_RATE = 0.3
    _SERVICE_INSURANCE_AMOUNT = 100

    def get_conditions_for_user_on_shift(self, shift, active_date):
        # TODO проверка переданной active_date

        conditions = Shift.objects.filter(id=shift.id).select_related(
            'vacancy', 'vacancy__shop', 'vacancy__shop__distributor'
        ).annotate(
            rounded_hours=Case(  # Количество часов (с округлением)
                When(
                    time_start__gt=F('time_end'),  # Если время начала больше времени окончания
                    then=Round(
                        (Extract(Value("23:59:59", TimeField()) - F('time_start'), 'epoch') +  # Время до полуночи
                         Extract(F('time_end') - Value("00:00:00", TimeField()), 'epoch'))  # Время после полуночи
                        / 3600)  # делим на 3600 чтобы получить кол-во часов
                ),
                default=Round(Extract(F('time_end') - F('time_start'), 'epoch') / 3600),
                output_field=IntegerField()
            )
        ).annotate(
            date=Value(active_date, output_field=IntegerField()),
            full_price=ExpressionWrapper(F('rounded_hours') * F('vacancy__price'), output_field=IntegerField()),
            # TODO поставить price из смены
            insurance=ExpressionWrapper(Value(self._SERVICE_INSURANCE_AMOUNT), output_field=IntegerField()),
            # TODO поставить размер страховки
            tax=ExpressionWrapper(
                Round(F('rounded_hours') * F('vacancy__price') * Value(self._SERVICE_TAX_RATE)),
                output_field=IntegerField()
            )
        ).annotate(
            clean_price=ExpressionWrapper(
                Round(F('full_price') - F('insurance') - F('tax')),
                output_field=IntegerField()
            )
        ).first()

        conditions.shift_id = shift.id  # Для облегчения внутренней логики на ios

        # ## Сбор нужных документов и статус по ним ##
        distributor_ct = ContentType.objects.get_for_model(Distributor)
        vacancy_ct = ContentType.objects.get_for_model(Vacancy)
        # Media
        conditions.documents = MediaModel.objects.filter(
            Q(type=MediaType.RULES_AND_ARTICLES.value, deleted=False) &  # Только с типом документы, правила
            Q(
                Q(owner_id=None) |  # Либо глобальные (Гиберно)
                Q(owner_ct=distributor_ct, owner_id=shift.vacancy.shop.distributor_id) |  # Либо торговой сети
                Q(owner_ct=vacancy_ct, owner_id=shift.vacancy_id)  # Либо вакансии
            )
        ).annotate(
            global_confirmed=Exists(GlobalDocument.objects.filter(document_id=OuterRef('pk'), user=self.me)),
            distributor_confirmed=Exists(DistributorDocument.objects.filter(document_id=OuterRef('pk'), user=self.me)),
            vacancy_confirmed=Exists(VacancyDocument.objects.filter(document_id=OuterRef('pk'), user=self.me))
        ).annotate(
            is_confirmed=Case(
                When(Q(global_confirmed=True) | Q(distributor_confirmed=True) | Q(vacancy_confirmed=True), then=True),
                default=False,
                output_field=BooleanField()
            )
        )

        conditions.text = "Текст о цифровой подписи"

        return conditions

    def accept_global_docs(self):
        global_documents = MediaModel.objects.filter(
            owner_id=None, type=MediaType.RULES_AND_ARTICLES.value, deleted=False)

        for global_document in global_documents:
            GlobalDocument.objects.get_or_create(
                user=self.me,
                document=global_document
            )

    def accept_distributor_docs(self, distributor_id):
        distributor = Distributor.objects.filter(pk=distributor_id).prefetch_related(
            Prefetch(
                'media',
                queryset=MediaModel.objects.filter(deleted=False, type=MediaType.RULES_AND_ARTICLES.value),
                to_attr='documents'
            )
        ).first()
        if not distributor:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {Distributor._meta.verbose_name} с ID={distributor_id} не найден')

        for distributor_document in distributor.documents:
            DistributorDocument.objects.get_or_create(
                user=self.me,
                distributor=distributor,
                document=distributor_document
            )

    def accept_vacancy_docs(self, vacancy_id):
        vacancy = Vacancy.objects.filter(pk=vacancy_id).prefetch_related(
            Prefetch(
                'media',
                queryset=MediaModel.objects.filter(deleted=False, type=MediaType.RULES_AND_ARTICLES.value),
                to_attr='documents'
            )
        ).first()
        if not vacancy:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {Vacancy._meta.verbose_name} с ID={vacancy_id} не найден')

        for vacancy_document in vacancy.documents:
            VacancyDocument.objects.get_or_create(
                user=self.me,
                vacancy=vacancy,
                document=vacancy_document
            )

    def accept_document(self, document_uuid):
        try:
            # Ищем документ с типом RULES_AND_ARTICLES
            document = MediaModel.objects.filter(
                uuid=document_uuid, type=MediaType.RULES_AND_ARTICLES.value, deleted=False
            ).first()
            if not document:
                raise HttpException(
                    status_code=RESTErrors.NOT_FOUND.value,
                    detail=f'Объект {MediaModel._meta.verbose_name} с UUID={document_uuid} и типом RULES_AND_ARTICLES не найден')

            # Если документ никому не принадлежит, то он глобальный для сервиса
            if document.owner is None:
                # Подтверждаем документ для пользователя
                GlobalDocument.objects.get_or_create(
                    user=self.me,
                    document=document
                )

            # Если документ принадлежит торговой сети
            if isinstance(document.owner, Distributor):
                # Подтверждаем документ для пользователя
                DistributorDocument.objects.get_or_create(
                    user=self.me,
                    distributor_id=document.owner_id,
                    document=document
                )

            # Если документ принадлежит вакансии
            if isinstance(document.owner, Vacancy):
                # Подтверждаем документ для пользователя
                VacancyDocument.objects.get_or_create(
                    user=self.me,
                    vacancy_id=document.owner_id,
                    document=document
                )

        except Exception as e:
            raise HttpException(
                status_code=RESTErrors.BAD_REQUEST.value,
                detail=e
            )

    def accept_market_documents(self, global_docs=None, distributor_id=None, vacancy_id=None, document_uuid=None):
        # Подтверждение всех глобальных документов
        if global_docs is True:
            # TODO получение документов Гиберно (документы без владельца == документы компании)
            self.accept_global_docs()

        # Подтверждение всех документов торговой сети
        if distributor_id:
            self.accept_distributor_docs(distributor_id)

        # Подтверждение всех документов вакансии
        if vacancy_id:
            self.accept_vacancy_docs(vacancy_id)

        # Подтверждение конкретного документа
        if document_uuid:
            self.accept_document(document_uuid)
