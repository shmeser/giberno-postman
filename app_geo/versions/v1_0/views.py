from djangorestframework_camel_case.util import camelize
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from app_geo.versions.v1_0.repositories import LanguagesRepository, CountriesRepository
from app_geo.versions.v1_0.serializers import LanguageSerializer, CountrySerializer
from backend.mappers import RequestMapper
from backend.mixins import CRUDAPIView


class Languages(CRUDAPIView):
    serializer_class = LanguageSerializer
    repository_class = LanguagesRepository
    allowed_http_methods = ['get']

    filter_params = {
        'name': 'name__istartswith',
        'native': 'native__istartswith',
        'code': 'iso_code__istartswith',
    }

    default_order_params = []

    default_filters = {
    }

    order_params = {
        'name': 'name',
        'id': 'id'
    }

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        pagination = RequestMapper.pagination(request)
        filters = RequestMapper().filters(
            request, self.filter_params, self.date_filter_params,
            self.default_filters
        ) or dict()
        order_params = RequestMapper.order(request, self.order_params) + self.default_order_params

        if record_id:
            dataset = self.repository_class().get_by_id(record_id)
            serialized = self.serializer_class(dataset)
        else:
            dataset = self.repository_class().filter_by_kwargs(
                kwargs=filters, paginator=pagination, order_by=order_params
            )
            serialized = self.serializer_class(dataset, many=True)

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


@api_view(['GET'])
def custom_languages(request):
    pagination = RequestMapper.pagination(request)
    dataset = LanguagesRepository().filter_by_kwargs(
        kwargs={
            'iso_code__in': ['ru', 'en', 'hy', 'be', 'kk', 'ky', 'uk']
        }, paginator=pagination
    )
    serialized = LanguageSerializer(dataset, many=True)
    return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class Countries(CRUDAPIView):
    serializer_class = CountrySerializer
    repository_class = CountriesRepository
    allowed_http_methods = ['get']

    filter_params = {
        'name': 'name__istartswith',
        'code': 'iso_code__istartswith',
    }

    default_order_params = []

    default_filters = {
    }

    order_params = {
        'name': 'name',
        'id': 'id'
    }

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        pagination = RequestMapper.pagination(request)
        filters = RequestMapper().filters(
            request, self.filter_params, self.date_filter_params,
            self.default_filters
        ) or dict()
        order_params = RequestMapper.order(request, self.order_params) + self.default_order_params

        if record_id:
            dataset = self.repository_class().get_by_id(record_id)
            serialized = self.serializer_class(dataset)
        else:
            dataset = self.repository_class().filter_by_kwargs(
                kwargs=filters, paginator=pagination, order_by=order_params
            )
            serialized = self.serializer_class(dataset, many=True)

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


@api_view(['GET'])
def custom_countries(request):
    pagination = RequestMapper.pagination(request)
    dataset = CountriesRepository().filter_by_kwargs(
        kwargs={
            'iso_code__in': ['RU', 'AM', 'BY', 'KZ', 'KG', 'UA']
        }, paginator=pagination
    )
    serialized = CountrySerializer(dataset, many=True)
    return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class Cities(CRUDAPIView):
    serializer_class = CountrySerializer
    repository_class = CountriesRepository
    allowed_http_methods = ['get']

    filter_params = {
        'name': 'name__istartswith',
        'code': 'iso_code__istartswith',
    }

    default_order_params = []

    default_filters = {
    }

    order_params = {
        'name': 'name',
        'id': 'id'
    }

    def get(self, request, **kwargs):
        None.get('a')
        record_id = kwargs.get(self.urlpattern_record_id_name)

        pagination = RequestMapper.pagination(request)
        filters = RequestMapper().filters(
            request, self.filter_params, self.date_filter_params,
            self.default_filters
        ) or dict()
        order_params = RequestMapper.order(request, self.order_params) + self.default_order_params

        if record_id:
            dataset = self.repository_class().get_by_id(record_id)
            serialized = self.serializer_class(dataset)
        else:
            dataset = self.repository_class().filter_by_kwargs(
                kwargs=filters, paginator=pagination, order_by=order_params
            )
            serialized = self.serializer_class(dataset, many=True)

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)
