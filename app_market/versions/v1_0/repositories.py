from datetime import timedelta, datetime

import pytz
from channels.db import database_sync_to_async
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db.models import GeometryField, CharField
from django.contrib.gis.db.models.functions import Distance, Envelope
from django.contrib.gis.geos import MultiPoint
from django.contrib.postgres.aggregates import BoolOr, ArrayAgg
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Value, IntegerField, Case, When, BooleanField, Q, Count, Prefetch, F, Func, \
    DateTimeField, Lookup, Field, DateField, Sum, ExpressionWrapper, Subquery, OuterRef
from django.db.models.functions import Cast, Concat
from django.utils.timezone import now, localtime
from pytz import timezone
from rest_framework.exceptions import PermissionDenied

from app_feedback.models import Review, Like
from app_geo.models import Region
from app_market.enums import ShiftWorkTime, ShiftStatus, ShiftAppealStatus
from app_market.models import Vacancy, Profession, Skill, Distributor, Shop, Shift, UserShift, ShiftAppeal
from app_market.versions.v1_0.mappers import ShiftMapper
from app_media.enums import MediaType, MediaFormat
from app_media.models import MediaModel
from app_users.enums import AccountType
from app_users.models import UserProfile
from backend.errors.enums import RESTErrors
from backend.errors.http_exceptions import HttpException
from backend.mixins import MasterRepository, MakeReviewMethodProviderRepository
from backend.utils import ArrayRemove, datetime_to_timestamp
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
class LTETimeTZ(CustomLookupBase):
    # Кастомный lookup для сравнения времени с учетом часовых поясов
    lookup_name = 'ltetimetz'
    parametric_string = "%s <= %s AT TIME ZONE timezone"


@Field.register_lookup
class GTTimeTZ(CustomLookupBase):
    # Кастомный lookup для сравнения времени с учетом часовых поясов
    lookup_name = 'gttimetz'
    parametric_string = "%s > %s AT TIME ZONE timezone"


class ShiftsRepository(MasterRepository):
    model = Shift

    SHIFTS_CALENDAR_DEFAULT_DAYS_COUNT = 10

    def __init__(self, me=None, calendar_from=None, calendar_to=None, vacancy_timezone_name='Europe/Moscow') -> None:
        super().__init__()
        # TODO брать из вакансии vacancy_timezone_name

        self.me = me
        # Получаем дату начала диапазона для расписани
        self.calendar_from = datetime.utcnow().isoformat() if calendar_from is None else localtime(
            calendar_from, timezone=timezone(vacancy_timezone_name)  # Даты высчитываем в часовых поясах вакансий
        ).isoformat()

        # Получаем дату окончания диапазона для расписания
        self.calendar_to = (datetime.utcnow() + timedelta(days=self.SHIFTS_CALENDAR_DEFAULT_DAYS_COUNT)).isoformat() \
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
        if queryset.count():
            for shift in queryset:
                utc_offset = pytz.timezone(shift.vacancy.timezone).utcoffset(datetime.utcnow()).total_seconds()
                for active_date in shift.active_dates:
                    active_dates.append({
                        'utc_offset': utc_offset,
                        'timestamp': datetime_to_timestamp(active_date)
                    })

        return active_dates


class UserShiftRepository(MasterRepository):
    model = UserShift

    def __init__(self, me=None):
        super().__init__()
        self.me = me

    def get_by_qr_data(self, qr_data):
        try:
            return self.model.objects.get(qr_data=qr_data)
        except self.model.DoesNotExist:
            raise HttpException(detail='User shift not found', status_code=400)

    def update_status_by_qr_check(self, instance):
        if instance.shift.vacancy.shop not in self.me.shops.all():
            raise PermissionDenied()

        if self.me.is_security:
            return
        if self.me.is_manager:
            if instance.status == ShiftStatus.INITIAL:
                instance.status = ShiftStatus.STARTED
                instance.save()
            elif instance.status == ShiftStatus.STARTED:
                instance.status = ShiftStatus.COMPLETED
                instance.qr_data = {}
                instance.save()
            elif instance.status == ShiftStatus.COMPLETED:
                return


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
        active_shifts = []
        vacancy = self.get_by_id_for_manager_or_security(record_id=record_id)
        shifts = ShiftsRepository(calendar_from=current_date, calendar_to=next_day).filter_by_kwargs(
            kwargs={'vacancy': vacancy},
            paginator=pagination)

        for shift in shifts:
            if len(shift.active_dates):
                for active_date in shift.active_dates:
                    if active_date <= current_date < next_day:
                        active_shifts.append(shift)
                        break
        return list(set(active_shifts))

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

    def get_or_create(self, **data):
        data.update({'applier': self.me})
        instance, created = self.model.objects.get_or_create(**data)
        return instance

    def get_by_id(self, record_id):
        records = self.base_query.filter(pk=record_id)
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

    def delete(self, record_id):
        instance = self.get_by_id(record_id=record_id)
        if not instance.applier == self.me:
            raise PermissionDenied()
        instance.deleted = True
        instance.save()

    def cancel(self, record_id, reason=None, text=None):
        instance = self.get_by_id(record_id=record_id)
        if instance.applier != self.me:
            raise PermissionDenied()
        instance.status = ShiftAppealStatus.CANCELED.value
        if reason is not None and instance.cancel_reason is None:
            instance.cancel_reason = reason
            instance.reason_text = text
        instance.save()

    @staticmethod
    def check_if_active_appeal(vacancy_id, applier_id):
        return ShiftAppeal.objects.filter(
            applier_id=applier_id,
            shift__vacancy__id=vacancy_id,
            # status__in=[ShiftAppealStatus.INITIAL.value] # TODO нужно ли учитывать отклоненные заявки
        ).exists()

    def is_related_manager(self, instance):
        if instance.shift.vacancy.shop not in self.me.shops.all():
            raise PermissionDenied()

    def confirm_by_manager(self, record_id):
        instance = self.get_by_id(record_id=record_id)

        # проверяем доступ менеджера к смене на которую откликнулись
        self.is_related_manager(instance=instance)

        if not instance.status == ShiftAppealStatus.CONFIRMED:
            instance.status = ShiftAppealStatus.CONFIRMED
            instance.save()

            # создаем смену пользователя
            UserShift.objects.get_or_create(
                user=instance.applier,
                shift=instance.shift,
                real_time_start=instance.shift.time_start,
                real_time_end=instance.shift.time_end
            )

    def reject_by_manager(self, record_id):
        instance = self.get_by_id(record_id=record_id)

        # проверяем доступ менеджера к смене на которую откликнулись
        self.is_related_manager(instance=instance)
        if not instance.status == ShiftAppealStatus.REJECTED:
            instance.status = ShiftAppealStatus.REJECTED
            instance.save()

    def get_by_id_for_manager(self, record_id):
        instance = self.get_by_id(record_id=record_id)

        # проверяем доступ менеджера
        self.is_related_manager(instance=instance)
        return instance

    def get_new_confirmed_count(self):
        return 0

    def get_new_appeals_count(self):
        return 0


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
