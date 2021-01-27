import inflection
from django.contrib.gis.geos import GEOSGeometry
from djangorestframework_camel_case.util import underscoreize

from app_media.enums import MediaType
from app_media.forms import FileForm
from app_media.mappers import MediaMapper
from backend.entity import Pagination, Error
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exception import HttpException, CustomException
from backend.utils import timestamp_to_datetime as t2d, CP, chained_get
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

    @classmethod
    def filters(cls, request, params: dict, date_params: dict, default_filters: dict):
        if not params and not date_params:
            return

        # копируем, чтобы не изменять сам request.query_params
        filter_values = underscoreize(request.query_params.copy())
        if not filter_values:
            return default_filters

        for param in date_params:
            if param in filter_values:
                filter_values[param] = t2d(int(filter_values[param]))

        """
        kwargs - конечный вариант фильтров, в виде:
            'title': 'new item';
            'person__id': '1';
            ...
        """
        all_params = {**params, **date_params}
        kwargs = {all_params[param]: filter_values.get(param) for param in all_params if filter_values.get(param)}
        return {**kwargs, **default_filters}

    @classmethod
    def order(cls, request, params: dict):
        if not params:
            return list()

        fields = underscoreize(request.query_params).get('order_by')
        order = request.query_params.get('order')

        if not fields or not order:
            return list()

        fields = fields if type(fields) == list else [fields]
        order = order if type(order) == list else [order]

        django_order_params = []
        for field, order in zip(fields, order):
            if inflection.underscore(field) in params:
                django_order = '' if order == 'asc' else '-'
                django_field = params[inflection.underscore(field)]

                django_order_params.append(f'{django_order}{django_field}')

        return django_order_params

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
            query_params = underscoreize(request.query_params)

            _lon = chained_get(query_params, 'lon')
            _lat = chained_get(query_params, 'lat')

            _radius = chained_get(request.query_params, 'radius')
            radius = int(_radius) if _radius else None

            _sw_lon = chained_get(query_params, 'sw_lon')
            _sw_lat = chained_get(query_params, 'sw_lat')
            _ne_lon = chained_get(query_params, 'ne_lon')
            _ne_lat = chained_get(query_params, 'ne_lat')

            if None in [_sw_lon, _sw_lat, _ne_lon, _ne_lat]:
                bbox = None
            else:
                coords_str = f'{_sw_lon} {_sw_lat},' \
                    f'{_sw_lon} {_ne_lat},' \
                    f'{_ne_lon} {_ne_lat},' \
                    f'{_ne_lon} {_sw_lat},' \
                    f'{_sw_lon} {_sw_lat}'

                bbox = GEOSGeometry(f'POLYGON(({coords_str}))', srid=settings.SRID)

            if _lat is not None and _lon is not None:
                lon = float(_lon)
                lat = float(_lat)
                if not -90 <= lat <= 90 or not -180 <= lon <= 180:
                    raise CustomException(errors=[
                        dict(Error(ErrorsCodes.INVALID_COORDS)),
                    ])
                return GEOSGeometry(f'POINT({lon} {lat})', srid=settings.SRID), bbox, radius
            if raise_exception:
                raise CustomException(errors=[
                    dict(Error(ErrorsCodes.INVALID_COORDS)),
                ])
            return None, bbox, radius
        except Exception as e:
            CP(fg='red').bold(e)
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.INVALID_COORDS)),
            ])
