import inflection
from djangorestframework_camel_case.util import underscoreize

from backend.entity import Pagination
from backend.errors.enums import RESTErrors
from backend.errors.http_exception import HttpException
from backend.utils import timestamp_to_datetime as m_t_d


class BaseMapper:
    @classmethod
    def validate(cls, data, field):
        if data.get(field) is None:
            raise HttpException(detail='Empty field: ' + field,
                                status_code=RESTErrors.BAD_REQUEST.value)


class RequestToPaginationMapper:
    @classmethod
    def map(cls, request):
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


class RequestToFilters:
    @classmethod
    def map(cls, request, params: dict, date_params: dict):
        if not params and not date_params:
            return

        # копируем, чтобы не изменять сам request.query_params
        filter_values = underscoreize(request.query_params.copy())
        if not filter_values:
            return

        for param in date_params:
            if param in filter_values:
                filter_values[param] = m_t_d(int(filter_values[param]))

        """
        kwargs - конечный вариант фильтров, в виде:
            'title': 'new item';
            'person__id': '1';
            ...
        """
        all_params = {**params, **date_params}
        kwargs = {all_params[param]: filter_values.get(param) for param in all_params if filter_values.get(param)}
        return kwargs


class RequestToOrderParams:
    @classmethod
    def map(cls, request, params: dict):
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
