from django.contrib.gis.db.models.functions import Distance
from django.db.models import Value, IntegerField

from app_market.models import Vacancy, Profession, Skill, Distributor, Shop
from backend.mixins import MasterRepository


class DistributorsRepository(MasterRepository):
    model = Distributor


class ShopsRepository(MasterRepository):
    model = Shop


class VacanciesRepository(MasterRepository):
    model = Vacancy

    def __init__(self, point=None, bbox=None) -> None:
        super().__init__()
        self.bbox = bbox
        self.distance_expression = Distance('shop__location', point) if point else Value(None, IntegerField())

    def filter_by_kwargs(self, kwargs, paginator=None, order_by: list = None):
        if self.bbox:
            # Если передана область на карте, то радиус поиска от указанной точки не учитывается в фильтрации
            kwargs.pop('distance__lte', None)
            kwargs['shop__location__contained'] = self.bbox
        try:
            if order_by:
                records = self.model.objects.annotate(distance=self.distance_expression).order_by(*order_by).exclude(
                    deleted=True).filter(**kwargs)
            else:
                records = self.model.objects.annotate(distance=self.distance_expression).exclude(deleted=True).filter(
                    **kwargs)
        except Exception:  # no 'deleted' field
            if order_by:
                records = self.model.objects.annotate(
                    distance=self.distance_expression
                ).order_by(*order_by).filter(**kwargs)
            else:
                records = self.model.objects.annotate(distance=self.distance_expression).filter(**kwargs)
        return records[paginator.offset:paginator.limit] if paginator else records

    def filter(self, args: list = None, kwargs={}, paginator=None, order_by: list = None):
        if self.bbox:
            # Если передана область на карте, то радиус поиска от указанной точки не учитывается в фильтрации
            kwargs.pop('distance__lte', None)
            kwargs['shop__location__contained'] = self.bbox
        try:
            if order_by:
                records = self.model.objects.annotate(
                    distance=self.distance_expression
                ).order_by(*order_by).exclude(deleted=True).filter(args, **kwargs)
            else:
                records = self.model.objects.annotate(
                    distance=self.distance_expression
                ).exclude(deleted=True).filter(args, **kwargs)
        except Exception:  # no 'deleted' field
            if order_by:
                records = self.model.objects.annotate(
                    distance=self.distance_expression
                ).order_by(*order_by).filter(args, **kwargs)
            else:
                records = self.model.objects.annotate(distance=self.distance_expression).filter(args, **kwargs)
        return records[paginator.offset:paginator.limit] if paginator else records


class ProfessionsRepository(MasterRepository):
    model = Profession

    def add_suggested_profession(self, name):
        self.model.objects.create(name=name, is_suggested=True)


class SkillsRepository(MasterRepository):
    model = Skill
