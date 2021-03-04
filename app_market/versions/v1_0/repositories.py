from datetime import timedelta, datetime

from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db.models import GeometryField
from django.contrib.gis.db.models.functions import Distance, BoundingCircle
from django.contrib.postgres.aggregates import BoolOr, ArrayAgg
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Value, IntegerField, Case, When, BooleanField, Q, Count, Prefetch, F, Func, DateTimeField, \
    Lookup, Field, DateField, Sum, FloatField, ExpressionWrapper, Subquery, OuterRef
from django.db.models.functions import Cast
from django.utils.timezone import now, localtime
from pytz import timezone

from app_feedback.models import Review, Like
from app_geo.models import Region
from app_market.enums import ShiftWorkTime
from app_market.models import Vacancy, Profession, Skill, Distributor, Shop, Shift
from app_market.versions.v1_0.mappers import ShiftMapper
from app_media.enums import MediaType, MediaFormat
from app_media.models import MediaModel
from backend.errors.enums import RESTErrors
from backend.errors.http_exception import HttpException
from backend.mixins import MasterRepository
from backend.utils import ArrayRemove


class MakeReviewMethodProviderRepository(MasterRepository):
    def __init__(self, me=None) -> None:
        super().__init__()
        self.me = me

    def make_review(self, record_id, text, value, point=None):
        # TODO добавить загрузку attachments

        owner_content_type = ContentType.objects.get_for_model(self.me)
        owner_ct_id = owner_content_type.id
        owner_ct_name = owner_content_type.model
        owner_id = self.me.id

        target_content_type = ContentType.objects.get_for_model(self.model)
        target_ct_id = target_content_type.id
        target_ct_name = target_content_type.model
        target_id = record_id

        region = Region.objects.filter(boundary__covers=point).first() if point else None

        if not Review.objects.filter(
                owner_ct_id=owner_ct_id,
                owner_id=owner_id,
                target_ct_id=target_ct_id,
                target_id=target_id,
                deleted=False
        ).exists():
            Review.objects.create(
                owner_ct_id=owner_ct_id,
                owner_id=owner_id,
                owner_ct_name=owner_ct_name,

                target_ct_id=target_ct_id,
                target_id=target_id,
                target_ct_name=target_ct_name,

                value=value,
                text=text,
                region=region
            )

            # Пересчитываем количество оценок и рейтинг
            self.model.objects.filter(pk=record_id).update(
                # в update нельзя использовать результаты annotate
                # используем annotate в Subquery
                rating=Subquery(
                    self.model.objects.filter(
                        id=OuterRef('id')
                    ).annotate(
                        calculated_rating=ExpressionWrapper(
                            Sum('reviews__value') / Count('reviews'),
                            output_field=FloatField()
                        )
                    ).values('calculated_rating')[:1]
                ),
                rates_count=Subquery(
                    self.model.objects.filter(
                        id=OuterRef('id')
                    ).annotate(
                        calculated_rates_count=Count('reviews'),
                    ).values('calculated_rates_count')[:1]
                ),
                updated_at=now()
            )


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
                shop__location__contained=ExpressionWrapper(
                    BoundingCircle(screen_diagonal_points),
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


class ShifsRepository(MasterRepository):
    model = Shift

    SHIFTS_CALENDAR_DEFAULT_DAYS_COUNT = 10

    def __init__(self, calendar_from=None, calendar_to=None, vacancy_timezone_name='Europe/Moscow') -> None:
        super().__init__()
        # TODO брать из вакансии vacancy_timezone_name

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
            free_count=self.free_count_expression,
        )

        # Фильтрация по вхождению в область на карте
        if self.screen_diagonal_points:
            self.base_query = self.base_query.filter(
                shop__location__contained=ExpressionWrapper(
                    BoundingCircle(screen_diagonal_points),
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


class ProfessionsRepository(MasterRepository):
    model = Profession

    def add_suggested_profession(self, name):
        self.model.objects.create(name=name, is_suggested=True)


class SkillsRepository(MasterRepository):
    model = Skill
