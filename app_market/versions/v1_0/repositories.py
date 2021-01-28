from datetime import timedelta

from django.contrib.gis.db.models.functions import Distance
from django.contrib.postgres.aggregates import BoolOr
from django.contrib.postgres.fields import ArrayField
from django.db.models import Value, IntegerField, Case, When, BooleanField, Q
from django.utils.timezone import now

from app_market.models import Vacancy, Profession, Skill, Distributor, Shop
from backend.mixins import MasterRepository


class DistributorsRepository(MasterRepository):
    model = Distributor


class ShopsRepository(MasterRepository):
    model = Shop


class VacanciesRepository(MasterRepository):
    model = Vacancy

    # TODO если у вакансии несколько смен то вакансия постоянно будет горящая?
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
        self.work_time_expression = Value([], ArrayField(IntegerField()))

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

    def filter_by_kwargs(self, kwargs, paginator=None, order_by: list = None):
        self.modify_kwargs(kwargs)  # Изменяем kwargs для работы с objects.filter(**kwargs)
        try:
            if order_by:
                records = self.base_query.order_by(*order_by).exclude(
                    deleted=True).filter(**kwargs)
            else:
                records = self.base_query.exclude(deleted=True).filter(
                    **kwargs)
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
                records = self.model.objects.annotate(distance=self.distance_expression).filter(args, **kwargs)
        return records[paginator.offset:paginator.limit] if paginator else records


class ProfessionsRepository(MasterRepository):
    model = Profession

    def add_suggested_profession(self, name):
        self.model.objects.create(name=name, is_suggested=True)


class SkillsRepository(MasterRepository):
    model = Skill
