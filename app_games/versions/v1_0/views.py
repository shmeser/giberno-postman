from django.http import JsonResponse
from djangorestframework_camel_case.util import camelize
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from app_games.versions.v1_0.repositories import PrizesRepository, TasksRepository, UserBonusesRepository
from app_games.versions.v1_0.serializers import PrizesSerializer, PrizeCardsSerializer, TasksSerializer, \
    PrizesSerializerAdmin, TasksSerializerAdmin, UserBonusesSerializerAdmin
from app_media.versions.v1_0.serializers import MediaSerializer
from backend.mappers import RequestMapper
from backend.mixins import CRUDAPIView
from backend.utils import get_request_headers, get_request_body
from giberno.settings import BONUS_PROGRESS_STEP_VALUE


class Prizes(CRUDAPIView):
    serializer_class = PrizesSerializer
    repository_class = PrizesRepository
    allowed_http_methods = ['get']

    filter_params = {
        'name': 'name__istartswith',
    }

    bool_filter_params = {
        'is_favourite': 'is_favourite',
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
            dataset = self.repository_class(request.user).inited_get_by_id(record_id)
        else:
            dataset = self.repository_class(request.user).inited_filter_by_kwargs(
                kwargs=filters, paginator=pagination, order_by=order_params
            )
            self.many = True

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class LikePrize(APIView):
    def post(self, request, **kwargs):
        prize_id = kwargs.get('record_id')
        PrizesRepository(request.user).set_like(prize_id)
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, **kwargs):
        prize_id = kwargs.get('record_id')
        PrizesRepository(request.user).remove_like(prize_id)
        return Response(None, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def bonus_progress_for_prizes(request):
    return JsonResponse(camelize({
        'value': request.user.bonuses_acquired % BONUS_PROGRESS_STEP_VALUE,
        'min': 0,
        'max': BONUS_PROGRESS_STEP_VALUE
    }), status=status.HTTP_200_OK)


class PrizesDocuments(APIView):
    def get(self, request):
        result = PrizesRepository.get_conditions_for_promotion()
        serialized = MediaSerializer(result, many=True)
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class PrizeCards(APIView):
    def get(self, request, **kwargs):
        result = PrizesRepository(request.user).get_cards()
        serialized = PrizeCardsSerializer(result, many=True)
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class OpenPrizeCard(APIView):
    def get(self, request, **kwargs):
        result = PrizesRepository(request.user).open_issued_card(record_id=kwargs.get('record_id'))
        serialized = PrizeCardsSerializer(result, many=False)
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class Tasks(CRUDAPIView):
    serializer_class = TasksSerializer
    repository_class = TasksRepository
    allowed_http_methods = ['get']

    filter_params = {
        'period': 'period',
    }
    bool_filter_params = {
        'is_completed': 'is_completed'
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
            result = self.repository_class(request.user).inited_get_by_id(record_id)
        else:
            result = self.repository_class(request.user).inited_filter_by_kwargs(
                kwargs=filters, paginator=pagination, order_by=order_params
            )
            self.many = True

        serialized = self.serializer_class(result, many=self.many)
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class TasksCount(CRUDAPIView):
    repository_class = TasksRepository
    allowed_http_methods = ['get']

    filter_params = {
        'period': 'period',
    }

    bool_filter_params = {
        'is_completed': 'is_completed'
    }

    default_order_params = []

    default_filters = {
    }

    order_params = {
        'name': 'name',
        'id': 'id'
    }

    def get(self, request, **kwargs):
        filters = RequestMapper(self).filters(request) or dict()
        result = self.repository_class(request.user).inited_filter_by_kwargs(
            kwargs=filters,
        )
        return Response(camelize({
            'result_count': result.count()
        }), status=status.HTTP_200_OK)


class AdminPrizes(CRUDAPIView):
    serializer_class = PrizesSerializerAdmin
    repository_class = PrizesRepository
    allowed_http_methods = ['get', 'post']

    filter_params = {
        'name': 'name__istartswith',
    }

    bool_filter_params = {
        'is_favourite': 'is_favourite',
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
            count = 1
            dataset = self.repository_class(request.user).admin_get_by_id(record_id)
        else:
            dataset, count = self.repository_class(request.user).admin_filter_by_kwargs(
                kwargs=filters, paginator=pagination, order_by=order_params
            )
            self.many = True

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        return Response(camelize(serialized.data), headers={'total-count': count}, status=status.HTTP_200_OK)

    def post(self, request, **kwargs):
        body = get_request_body(request)
        serialized = self.serializer_class(data=body, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        serialized.is_valid(raise_exception=True)
        serialized.save()
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class AdminPrize(AdminPrizes):
    allowed_http_methods = ['get', 'put', 'delete']

    def put(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        instance = self.repository_class(me=request.user).get_by_id(record_id)
        body = get_request_body(request)
        serialized = self.serializer_class(instance, data=body, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        serialized.is_valid(raise_exception=True)
        serialized.save()
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)

    def delete(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        instance = self.repository_class(me=request.user).get_by_id(record_id)
        instance.deleted = True
        instance.save()

        serialized = self.serializer_class(instance, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class AdminTasks(CRUDAPIView):
    serializer_class = TasksSerializerAdmin
    repository_class = TasksRepository
    allowed_http_methods = ['get']

    filter_params = {
        'period': 'period',
    }
    bool_filter_params = {
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
            count = 1
            result = self.repository_class(request.user).get_by_id(record_id)
        else:
            result, count = self.repository_class(request.user).admin_filter_by_kwargs(
                kwargs=filters, paginator=pagination, order_by=order_params
            )
            self.many = True

        serialized = self.serializer_class(result, many=self.many)
        return Response(camelize(serialized.data), headers={'total-count': count}, status=status.HTTP_200_OK)

    def post(self, request, **kwargs):
        body = get_request_body(request)
        serialized = self.serializer_class(data=body, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        serialized.is_valid(raise_exception=True)
        serialized.save()
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class AdminTask(AdminTasks):
    allowed_http_methods = ['get', 'put', 'delete']

    def put(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        instance = self.repository_class(me=request.user).get_by_id(record_id)
        body = get_request_body(request)
        serialized = self.serializer_class(instance, data=body, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        serialized.is_valid(raise_exception=True)
        serialized.save()
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)

    def delete(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        instance = self.repository_class(me=request.user).get_by_id(record_id)
        instance.deleted = True
        instance.save()

        serialized = self.serializer_class(instance, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class AdminUsersBonuses(CRUDAPIView):
    serializer_class = UserBonusesSerializerAdmin
    repository_class = UserBonusesRepository
    allowed_http_methods = ['get']

    filter_params = {
    }
    bool_filter_params = {
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
            count = 1
            result = self.repository_class(request.user).get_user_with_bonuses(record_id)
        else:
            result, count = self.repository_class(request.user).get_users_with_bonuses(
                kwargs=filters, paginator=pagination, order_by=order_params
            )
            self.many = True

        serialized = self.serializer_class(result, many=self.many)
        return Response(camelize(serialized.data), headers={'total-count': count}, status=status.HTTP_200_OK)

    def post(self, request, **kwargs):
        body = get_request_body(request)
        serialized = self.serializer_class(data=body, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        serialized.is_valid(raise_exception=True)
        serialized.save()
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class AdminUserBonuses(AdminUsersBonuses):
    allowed_http_methods = ['get', 'put', 'delete']

    def put(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        instance = self.repository_class(me=request.user).get_by_id(record_id)
        body = get_request_body(request)
        serialized = self.serializer_class(instance, data=body, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        serialized.is_valid(raise_exception=True)
        serialized.save()
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)

    def delete(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        instance = self.repository_class(me=request.user).get_by_id(record_id)
        instance.deleted = True
        instance.save()

        serialized = self.serializer_class(instance, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)
