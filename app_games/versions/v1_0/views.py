from djangorestframework_camel_case.util import camelize
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from app_games.versions.v1_0.repositories import PrizesRepository
from app_games.versions.v1_0.serializers import PrizesSerializer, PrizeCardsSerializer
from app_media.versions.v1_0.serializers import MediaSerializer
from backend.mappers import RequestMapper
from backend.mixins import CRUDAPIView
from backend.utils import get_request_headers


class Prizes(CRUDAPIView):
    serializer_class = PrizesSerializer
    repository_class = PrizesRepository
    allowed_http_methods = ['get']

    filter_params = {
        'name': 'name__istartswith',
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


class LikePrize(APIView):
    def post(self, request, **kwargs):
        prize_id = kwargs.get('record_id')
        result = PrizesRepository(request.user).set_like(prize_id)
        serialized = PrizesSerializer(result, many=False)
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)

    def delete(self, request, **kwargs):
        prize_id = kwargs.get('record_id')
        result = PrizesRepository(request.user).remove_like(prize_id)
        serialized = PrizesSerializer(result, many=False)
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class PrizesDocuments(APIView):
    def get(self, request):
        result = PrizesRepository.get_conditions_for_promotion()
        serialized = MediaSerializer(result, many=True)
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class PrizeCards(APIView):
    def get(self, request, **kwargs):
        result = PrizesRepository(request.user).get_get_cards()
        serialized = PrizeCardsSerializer(result, many=False)
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class Tasks(CRUDAPIView):
    def get(self, request, **kwargs):
        result = PrizesRepository(request.me).get_tasks()
        serialized = TasksSerializer(result, many=False)
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)
