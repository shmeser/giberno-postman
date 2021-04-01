from djangorestframework_camel_case.util import camelize
from rest_framework import status
from rest_framework.response import Response

from app_chats.versions.v1_0.repositories import ChatsRepository, MessagesRepository
from app_chats.versions.v1_0.serializers import ChatsSerializer, MessagesSerializer, ChatSerializer
from backend.mappers import RequestMapper
from backend.mixins import CRUDAPIView
from backend.utils import get_request_headers


class Chats(CRUDAPIView):
    serializer_class = ChatsSerializer
    repository_class = ChatsRepository
    allowed_http_methods = ['get']

    filter_params = {
        'shop': 'shop_id',
        'vacancy': 'vacancy_id',
        'user': 'user_id',
        'created_at': 'created_at'
    }

    bool_filter_params = {
    }

    array_filter_params = {
    }

    default_order_params = [
        '-id'
    ]

    default_filters = {}

    order_params = {
        'created_at': 'created_at',
    }

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        if record_id:
            self.serializer_class = ChatSerializer
            dataset = self.repository_class().get_by_id(record_id)
        else:
            self.many = True
            dataset = self.repository_class(request.user).get_chats_or_create(
                kwargs=filters, order_by=order_params, paginator=pagination
            )

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class Messages(CRUDAPIView):
    serializer_class = MessagesSerializer
    repository_class = MessagesRepository
    allowed_http_methods = ['get']

    filter_params = {
        'search': 'text__istartswith',
        'created_at': 'created_at__gte',  # TODO сделать gte или lte в зависимости от order=asc/desc
        'city': 'city_id',
        'shop': 'shop_id',
        'price': 'price__gte',
        'radius': 'distance__lte',
    }

    bool_filter_params = {
    }

    array_filter_params = {
    }

    default_order_params = [
        '-created_at'
    ]

    default_filters = {}

    order_params = {
        'created_at': 'created_at',
    }

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        self.many = True
        dataset = self.repository_class().filter_by_kwargs(
            kwargs=filters, order_by=order_params, paginator=pagination
        )

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)