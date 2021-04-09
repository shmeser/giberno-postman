import itertools
import operator
from datetime import timedelta

import inflection
from django.contrib.gis.geos import GEOSGeometry
from django.db.models.query import RawQuerySet
from djangorestframework_camel_case.util import underscoreize
from loguru import logger

from app_media.enums import MediaType
from app_media.forms import FileForm
from app_media.mappers import MediaMapper
from backend.entity import Pagination, Error
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exceptions import HttpException, CustomException
from backend.utils import timestamp_to_datetime as t2d, chained_get, timestamp_to_datetime, get_request_body
from giberno import settings


class BaseMapper:
    @classmethod
    def validate(cls, data, field):
        if data.get(field) is None:
            raise HttpException(
                detail='Empty field: ' + field,
                status_code=RESTErrors.BAD_REQUEST.value
            )


class RequestMapper:

    def __init__(self, view_class=None):
        # super().__init__()
        self.filter_params = view_class.filter_params if view_class else dict()
        self.date_filter_params = view_class.date_filter_params if view_class else dict()
        self.bool_filter_params = view_class.bool_filter_params if view_class else dict()
        self.array_filter_params = view_class.array_filter_params if view_class else dict()
        self.default_filters = view_class.default_filters if view_class else dict()

        self.order_params = view_class.order_params if view_class else dict()
        self.default_order_params = view_class.default_order_params if view_class else dict()

    @classmethod
    def pagination(cls, request):
        pagination: Pagination = Pagination()

        if request.GET.get('offset') is None:
            pagination.offset = 0
        else:
            try:
                pagination.offset = int(request.GET.get('offset'))
            except Exception:
                pagination.offset = 0

        if request.GET.get('limit') is None:
            pagination.limit = 10
        else:
            try:
                pagination.limit = pagination.offset + int(request.GET.get('limit'))
            except Exception:
                pagination.limit = 10

        return pagination

    def filters(self, request):
        if not self.filter_params and not self.date_filter_params and not self.bool_filter_params \
                and not self.array_filter_params:
            return

        # копируем, чтобы не изменять сам request.query_params
        filter_values = underscoreize(request.query_params.copy())
        if not filter_values:
            return self.default_filters

        for param in self.date_filter_params:
            if param in filter_values:
                filter_values[param] = t2d(int(filter_values[param]))

        for param in self.bool_filter_params:
            if param in filter_values:
                filter_values[param] = str(filter_values[param]).lower() in [True, 1, 'true', 'yes']

        for param in self.array_filter_params:
            if param in filter_values:
                filter_values[param] = list(filter(
                    lambda y: y, list(map(lambda x: x.strip(), filter_values[param].split(',')))
                ))

        """
        kwargs - конечный вариант фильтров, в виде:
            'title': 'new item';
            'person__id': '1';
            ...
        """
        all_params = {
            **self.filter_params, **self.date_filter_params, **self.bool_filter_params, **self.array_filter_params
        }
        kwargs = {all_params[param]: filter_values.get(param) for param in all_params if filter_values.get(param)}
        return {**kwargs, **self.default_filters}

    def order(self, request):
        if not self.order_params:
            return self.default_order_params

        fields = underscoreize(request.query_params).get('order_by')
        order = request.query_params.get('order')

        if not fields or not order:
            return self.default_order_params

        fields = fields if type(fields) == list else [fields]
        order = order if type(order) == list else [order]

        django_order_params = []
        for field, order in zip(fields, order):
            _field = inflection.underscore(field)
            if _field in self.order_params:
                django_order = '' if order == 'asc' else '-'
                django_field = self.order_params[_field]

                # Удаляем сортировку по умолчанию, если сортировка по тому же полю
                if django_field in self.default_order_params or f'-{django_field}' in self.default_order_params:
                    self.default_order_params.remove(django_field)
                    self.default_order_params.remove(f'-{django_field}')
                ###

                django_order_params.append(f'{django_order}{django_field}')

        return django_order_params + self.default_order_params

    @staticmethod
    def file_entities(request, owner):
        form = FileForm(request.POST, request.FILES)
        entities = []

        if form.is_valid():
            for form_file in form.files.getlist('file'):
                file_title = form.cleaned_data['title'] if 'title' in form.cleaned_data and form.cleaned_data[
                    'title'] else form_file.name
                file_type = form.cleaned_data.get('type', MediaType.OTHER)

                mapped_file = MediaMapper.combine(form_file, owner, file_title, file_type)

                if mapped_file:
                    entities.append(mapped_file)

            return entities
        else:
            # TODO подробные ошибки валидации формы
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.VALIDATION_ERROR)),
                dict(Error(ErrorsCodes.EMPTY_REQUIRED_FIELDS)),
            ])

    @classmethod
    def geo(cls, request, raise_exception=False):
        try:
            if request.body:
                data = get_request_body(request)
            else:
                data = underscoreize(request.query_params)

            _lon = chained_get(data, 'lon')
            _lat = chained_get(data, 'lat')

            _radius = chained_get(request.query_params, 'radius')
            radius = int(_radius) if _radius else None

            _sw_lon = chained_get(data, 'sw_lon')
            _sw_lat = chained_get(data, 'sw_lat')
            _ne_lon = chained_get(data, 'ne_lon')
            _ne_lat = chained_get(data, 'ne_lat')

            if None in [_sw_lon, _sw_lat, _ne_lon, _ne_lat]:
                screen_diagonal_points = None
            else:
                # First diagonal point
                x1 = float(_sw_lon)
                y1 = float(_sw_lat)
                # Second diagonal point
                x2 = float(_ne_lon)
                y2 = float(_ne_lat)

                screen_diagonal_points = GEOSGeometry(f'POINT({x1} {y1})', srid=settings.SRID), GEOSGeometry(
                    f'POINT({x2} {y2})', srid=settings.SRID)

            if _lat is not None and _lon is not None:
                lon = float(_lon)
                lat = float(_lat)
                if not -90 <= lat <= 90 or not -180 <= lon <= 180:
                    raise CustomException(errors=[
                        dict(Error(ErrorsCodes.INVALID_COORDS)),
                    ])
                return GEOSGeometry(f'POINT({lon} {lat})', srid=settings.SRID), screen_diagonal_points, radius
            if raise_exception:
                raise CustomException(errors=[
                    dict(Error(ErrorsCodes.INVALID_COORDS)),
                ])
            return None, screen_diagonal_points, radius
        except Exception as e:
            logger.error(e)
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.INVALID_COORDS)),
            ])

    @classmethod
    def calendar_range(cls, request, raise_exception=False):
        try:
            query_params = underscoreize(request.query_params)

            _range_from_ts = chained_get(query_params, 'calendar_from')
            _range_to_ts = chained_get(query_params, 'calendar_to')

            if _range_from_ts is not None and _range_to_ts is not None:
                range_from = timestamp_to_datetime(float(_range_from_ts))
                range_to = timestamp_to_datetime(float(_range_to_ts))
                return range_from, range_to
            if raise_exception:
                raise CustomException(errors=[
                    dict(Error(ErrorsCodes.INVALID_DATE_RANGE)),
                ])
            return None, None
        except Exception as e:
            logger.error(e)
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.INVALID_DATE_RANGE)),
            ])

    # проверяем валидность заданной даты
    @classmethod
    def current_date_range(cls, request, raise_exception=False):
        try:
            query_params = underscoreize(request.query_params)
            _current_date_ts = chained_get(query_params, 'current_date')
            if _current_date_ts is not None:
                current_date = timestamp_to_datetime(float(_current_date_ts))
                next_day = current_date + timedelta(days=1)
                next_day = next_day.replace(hour=0, minute=0, second=0)
                return current_date, next_day
            if raise_exception:
                raise CustomException(errors=[
                    dict(Error(ErrorsCodes.INVALID_DATE_RANGE)),
                ])
            return None, None
        except Exception as e:
            logger.error(e)
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.INVALID_DATE_RANGE)),
            ])


class DataMapper:
    @staticmethod
    def geo_point(data, raise_exception=False):
        _lon = chained_get(data, 'lon')
        _lat = chained_get(data, 'lat')
        if _lat is not None and _lon is not None:
            lon = float(_lon)
            lat = float(_lat)
            if not -90 <= lat <= 90 or not -180 <= lon <= 180:
                raise CustomException(errors=[
                    dict(Error(ErrorsCodes.INVALID_COORDS)),
                ])
            return GEOSGeometry(f'POINT({lon} {lat})', srid=settings.SRID)
        if raise_exception:
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.INVALID_COORDS)),
            ])
        return None

    @staticmethod
    def clustering_raw_qs(data, key):
        new_list = []
        if isinstance(data, RawQuerySet):
            get_attr = operator.attrgetter(key)
            for k, g in itertools.groupby(data, get_attr):
                grouped = list(g)
                cluster = {
                    'cid': k,
                    'lat': getattr(grouped[0], 'c_lat'),
                    'lon': getattr(grouped[0], 'c_lon'),
                    'clustered_count': getattr(grouped[0], 'clustered_count'),
                    'clustered_items': grouped
                }
                new_list.append(cluster)

        return new_list
