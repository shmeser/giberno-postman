from django.db.models import F
from djangorestframework_camel_case.util import camelize
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from app_geo.versions.v1_0.repositories import LanguagesRepository, CountriesRepository, CitiesRepository
from app_geo.versions.v1_0.serializers import LanguageSerializer, CountrySerializer, CitySerializer, \
    CityClusterSerializer
from backend.mappers import RequestMapper
from backend.mixins import CRUDAPIView
from backend.utils import get_request_headers


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

        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        if record_id:
            dataset = self.repository_class().get_by_id(record_id)
            serialized = self.serializer_class(dataset, context={
                'me': request.user,
                'headers': get_request_headers(request),
            })
        else:
            dataset = self.repository_class().filter_by_kwargs(
                kwargs=filters, paginator=pagination, order_by=order_params
            )
            serialized = self.serializer_class(dataset, many=True, context={
                'me': request.user,
                'headers': get_request_headers(request),
            })

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


@api_view(['GET'])
def custom_languages(request):
    pagination = RequestMapper.pagination(request)
    dataset = LanguagesRepository().filter_by_kwargs(
        kwargs={
            'iso_code__in': ['ru', 'en', 'hy', 'be', 'kk', 'ky', 'uk']
        }, paginator=pagination
    )
    serialized = LanguageSerializer(
        dataset, many=True, context={
            'me': request.user,
            'headers': get_request_headers(request),
        }
    )
    return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class Countries(CRUDAPIView):
    serializer_class = CountrySerializer
    repository_class = CountriesRepository
    allowed_http_methods = ['get']

    # TODO поиск и сортировка с учетом языка пользователя
    filter_params = {
        'name': 'native__istartswith',
        'code': 'iso_code__istartswith',
    }

    default_order_params = []

    default_filters = {
    }

    order_params = {
        'name': 'native',
        'id': 'id'
    }

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        if record_id:
            dataset = self.repository_class().get_by_id(record_id)
        else:
            self.many = True
            dataset = self.repository_class().filter_by_kwargs(
                kwargs=filters, paginator=pagination, order_by=order_params
            )
            # SpeedUp
            # TODO refactor 2 раза инициализируется сериалайзер
            dataset = self.repository_class.fast_related_loading(
                dataset
            )
            dataset = dataset.defer("boundary", "osm")

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


@api_view(['GET'])
def custom_countries(request):
    pagination = RequestMapper.pagination(request)
    dataset = CountriesRepository().filter_by_kwargs(
        kwargs={
            'iso_code__in': ['RU', 'AM', 'BY', 'KZ', 'KG', 'UA']
        }, paginator=pagination
    )
    # SpeedUp
    dataset = CountriesRepository.fast_related_loading(dataset)
    dataset = dataset.defer("boundary", "osm")

    serialized = CountrySerializer(dataset, many=True, context={
        'me': request.user,
        'headers': get_request_headers(request),
    })
    return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class Cities(CRUDAPIView):
    serializer_class = CitySerializer
    repository_class = CitiesRepository
    allowed_http_methods = ['get']

    filter_params = {
        'name': 'native__istartswith',  # TODO Доработать поиск по строке для строк с пробелами
        'country': 'country_id',
        'region': 'region_id'
    }

    default_order_params = [F('population').desc(nulls_last=True)]

    default_filters = {
    }

    order_params = {
        'name': 'native',
        'id': 'id'
    }

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)
        point, screen_diagonal_points, radius = RequestMapper().geo(request)

        if record_id:
            dataset = self.repository_class().get_by_id(record_id)
        else:
            self.many = True
            dataset = self.repository_class(point, screen_diagonal_points).filter_by_kwargs(
                kwargs=filters, paginator=pagination, order_by=order_params
            )

            # Не запрашиваем ненужные тяжелые данные
            dataset = dataset.defer(
                "boundary", "osm", "native_tsv", "names_tsv",
                "country__boundary", "country__osm",
                "region__boundary", "region__osm",
            )

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class CitiesClusteredMap(Cities):
    serializer_class = CityClusterSerializer

    def get(self, request, **kwargs):
        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)
        point, screen_diagonal_points, radius = RequestMapper().geo(request)

        self.many = True
        dataset = self.repository_class(point, screen_diagonal_points).filter_by_kwargs(
            kwargs=filters, paginator=pagination, order_by=order_params
        )

        # Не запрашиваем ненужные тяжелые данные
        dataset = dataset.defer(
            "boundary", "osm", "native_tsv", "names_tsv",
            "country__boundary", "country__osm",
            "region__boundary", "region__osm",
        )

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


@api_view(['GET'])
def cities_suggestions(request):
    pagination = RequestMapper.pagination(request)
    dataset = []
    search = request.query_params.get('search') if request.query_params else None
    if search:
        dataset = CitiesRepository().get_suggestions(
            # trigram_similar Поиск с использованием pg_trgm на проиндексированном поле native
            search=search,
            paginator=pagination
        )
    return Response(dataset, status=status.HTTP_200_OK)


@api_view(['GET'])
def geocode(request):
    point = RequestMapper().geo(request, raise_exception=True)[0]
    dataset = CitiesRepository().geocode(point)

    # SpeedUp
    dataset = CitiesRepository.fast_related_loading(dataset)
    # Не запрашиваем ненужные тяжелые данные
    dataset = dataset.defer(
        "boundary", "osm", "native_tsv", "names_tsv",
        "country__boundary", "country__osm",
        "region__boundary", "region__osm",
    )

    serialized = CitySerializer(dataset, many=True, context={
        'me': request.user,
        'headers': get_request_headers(request),
    })
    return Response(camelize(serialized.data), status=status.HTTP_200_OK)
