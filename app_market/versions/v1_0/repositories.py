from datetime import timedelta, datetime

from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db.models.functions import Distance
from django.contrib.postgres.aggregates import BoolOr, ArrayAgg
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Value, IntegerField, Case, When, BooleanField, Q, Count, Prefetch, F, Func, DateTimeField
from django.utils.timezone import now, localtime
from pytz import timezone

from app_market.enums import ShiftWorkTime
from app_market.models import Vacancy, Profession, Skill, Distributor, Shop, Shift
from app_market.versions.v1_0.mappers import ShiftMapper
from app_media.enums import MediaType, MediaFormat
from app_media.models import MediaModel
from backend.errors.enums import RESTErrors
from backend.errors.http_exception import HttpException
from backend.mixins import MasterRepository
from backend.utils import ArrayRemove


class DistributorsRepository(MasterRepository):
    model = Distributor

    def __init__(self, point=None, bbox=None, time_zone=None) -> None:
        super().__init__()

        # Выражения для вычисляемых полей в annotate
        self.vacancies_expression = Count('shop__vacancy')

        # Основная часть запроса, содержащая вычисляемые поля
        self.base_query = self.model.objects.annotate(
            vacancies_count=self.vacancies_expression
        )

    def get_by_id(self, record_id):
        try:
            return self.base_query.get(id=record_id)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден'
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

    @staticmethod
    def fast_related_loading(queryset):
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
        return queryset


class ShopsRepository(MasterRepository):
    model = Shop


class ShifsRepository(MasterRepository):
    model = Shift

    SHIFTS_CALENDAR_DEFAULT_DAYS_COUNT = 10

    def __init__(self, calendar_from=None, calendar_to=None, vacancy_timezone_name='UTC') -> None:
        super().__init__()
        vacancy_timezone_name = 'Europe/Moscow'  # TODO брать из вакансии

        # Получаем дату начала диапазона для расписани
        self.calendar_from = datetime.utcnow().isoformat() if calendar_from is None else localtime(
            calendar_from, timezone=timezone(vacancy_timezone_name)  # Даты высчитываем в часовых поясах вакансий
        ).isoformat()

        # Получаем дату окончания диапазона для расписания
        self.calendar_to = localtime(
            datetime.utcnow() + timedelta(days=self.SHIFTS_CALENDAR_DEFAULT_DAYS_COUNT)
        ).isoformat() \
            if calendar_to is None else localtime(calendar_to, timezone=timezone(vacancy_timezone_name)).isoformat()

        # Annotation Expressions
        self.active_dates_expression = Func(
            F('frequency'),
            F('by_month'),
            F('by_monthday'),
            F('by_weekday'),
            Value(self.calendar_from),
            Value(self.calendar_to),
            function='rrule_list_occurences',  # Кастомная postgres функция
            output_field=ArrayField(DateTimeField())
        )

        self.active_today_expression = Case(
            When(
                # Используем поле active_dates из предыдущего annotate
                active_dates__contains=[localtime(now(), timezone=timezone(vacancy_timezone_name))],
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


class VacanciesRepository(MasterRepository):
    model = Vacancy

    # TODO если у вакансии несколько смен, то вакансия постоянно будет горящая?
    IS_HOT_HOURS_THRESHOLD = 4  # Количество часов до начала смены для статуса вакансии "Горящая"

    def __init__(self, point=None, bbox=None, time_zone=None) -> None:
        super().__init__()
        self.bbox = bbox

        # Выражения для вычисляемых полей в annotate
        self.distance_expression = Distance('shop__location', point) if point else Value(None, IntegerField())
        self.is_hot_expression = BoolOr(  # Аггрегация булевых значений (Если одно из значений true, то результат true)
            Case(When(Q(  # Смена должна начаться в ближайшие 4 часа
                shift__time_start__lte=now() + timedelta(hours=self.IS_HOT_HOURS_THRESHOLD),
                shift__time_start__gt=now()
            ), then=True), default=False, output_field=BooleanField())
        )
        morning_range = ShiftMapper.work_time_to_time_range(ShiftWorkTime.MORNING.value)
        day_range = ShiftMapper.work_time_to_time_range(ShiftWorkTime.DAY.value)
        evening_range = ShiftMapper.work_time_to_time_range(ShiftWorkTime.EVENING.value)

        # Выставляем work_time по времени начала смены - time_start
        self.work_time_expression = ArrayRemove(ArrayAgg(  # Аггрегация значений в массив
            Case(
                When(Q(  # Если начинается утром
                    shift__time_start__gte=morning_range[0],
                    shift__time_start__lte=morning_range[1]
                ),
                    then=ShiftWorkTime.MORNING
                ),
                When(Q(  # Если начинается днем
                    shift__time_start__gte=day_range[0],
                    shift__time_start__lte=day_range[1]
                ),
                    then=ShiftWorkTime.DAY
                ),
                When(Q(  # Если начинается вечером
                    shift__time_start__gte=evening_range[0],
                    shift__time_start__lte=evening_range[1]
                ),
                    then=ShiftWorkTime.EVENING
                ),
                default=None,
                output_field=IntegerField()
            )
        ), None)  # Удаляем из массива null значения

        # Основная часть запроса, содержащая вычисляемые поля
        self.base_query = self.model.objects.annotate(
            distance=self.distance_expression,
            is_hot=self.is_hot_expression,
            work_time=self.work_time_expression,
        )

    def modify_kwargs(self, kwargs):
        if self.bbox:
            # Если передана область на карте, то радиус поиска от указанной точки не учитывается в фильтрации
            kwargs.pop('distance__lte', None)
            kwargs['shop__location__contained'] = self.bbox

    def get_by_id(self, record_id):
        try:
            return self.base_query.get(id=record_id)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден')

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
        return records[paginator.offset:paginator.limit] if paginator else records

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
        return records[paginator.offset:paginator.limit] if paginator else records

    def get_suggestions(self, search, paginator=None):
        records = self.model.objects.exclude(deleted=True).annotate(
            similarity=TrigramSimilarity('title', search),
        ).filter(title__trigram_similar=search).order_by('-similarity')

        records = records.only('title').distinct().values_list('title', flat=True)
        return records[paginator.offset:paginator.limit] if paginator else records[:100]

    @staticmethod
    def fast_related_loading(queryset, point=None):
        """ Подгрузка зависимостей с 3 уровнями вложенности по ForeignKey + GenericRelation
            Vacancy
            -> Shop + Media
            -> Distributor + Media
        """
        queryset = queryset.prefetch_related(
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

    @staticmethod
    def aggregate_stats(queryset):
        count = queryset.aggregate(
            result_count=Count('id'),
        )

        prices = Vacancy.objects.filter(deleted=False).values('price').order_by('price').annotate(
            count=Count('id'),
        ).aggregate(all_prices=ArrayAgg('price', ordering='price'), all_counts=ArrayAgg('count', ordering='price'))

        return {**count, **prices}


class ProfessionsRepository(MasterRepository):
    model = Profession

    def add_suggested_profession(self, name):
        self.model.objects.create(name=name, is_suggested=True)


class SkillsRepository(MasterRepository):
    model = Skill
