from djangorestframework_camel_case.util import camelize
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.errors.enums import Errors
from backend.errors.http_exception import HttpException
from backend.mappers import RequestToFilters, RequestToOrderParams, RequestToPaginationMapper
from backend.permissions import AbbleToPerform
from backend.repositories import BaseRepository
from backend.utils import create_admin_serializer, get_request_body, user_is_admin


class CRUDSerializer(serializers.ModelSerializer):
    repository = None

    def create(self, validated_data):
        return self.repository().create(**validated_data)

    def update(self, instance, validated_data):
        return self.repository().update(instance.id, **validated_data)


class MasterRepository(BaseRepository):
    model = None

    def __init__(self):
        super().__init__(self.model)


class CRUDAPIView(APIView):
    serializer_class = None
    repository_class = None
    urlpattern_record_id_name = 'record_id'
    filter_params = dict()
    order_params = dict()
    date_filter_params = dict()  # словарь, в котором будут указанны фитльтры в формате timestamp.
    permission_classes = [AbbleToPerform]
    # есть возможность указать http методы которые будут обрабатываться.
    allowed_http_methods = []
    admin_serializer = None
    nullable_fields = {}
    # используется в permissions.py для проверки check_object_permissions.
    # Если у созданной модели поле создателя называется не owner, то,
    # необходимо присвоить используемое имя.
    owner_field_name: str = 'owner'
    default_order_params = []

    def __init__(self, **kwargs):
        if self.allowed_http_methods:
            self.http_method_names = self.allowed_http_methods

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        pagination = RequestToPaginationMapper.map(request)
        filters = RequestToFilters().map(request, self.filter_params,
                                         self.date_filter_params) or dict()
        queryset = self.get_queryset(request=request, **kwargs)
        order_params = RequestToOrderParams.map(request, self.order_params) + self.default_order_params

        if record_id:
            if user_is_admin(request.user) and request.user.is_superuser:
                dataset = super(self.repository_class().__class__, self.repository_class()).get_by_id(record_id)
                if self.admin_serializer:
                    serializer_class = self.admin_serializer
                else:
                    serializer_class = create_admin_serializer(self.serializer_class)
                serialized = serializer_class(dataset)
            else:
                dataset = self.repository_class().get_by_id(record_id)
                serialized = self.serializer_class(dataset)

        elif queryset is not None:
            dataset = queryset
            dataset = dataset.order_by(*order_params).filter(**filters)
            dataset = dataset[pagination.offset:pagination.limit]
            serialized = self.serializer_class(dataset, many=True)

        else:
            if user_is_admin(request.user) and request.user.is_superuser:
                dataset = super(self.repository_class().__class__, self.repository_class()).filter_by_kwargs(
                    kwargs=filters, paginator=pagination, order_by=order_params)
                if self.admin_serializer:
                    serializer_class = self.admin_serializer
                else:
                    serializer_class = create_admin_serializer(self.serializer_class)
                serialized = serializer_class(dataset, many=True)
            else:
                dataset = self.repository_class().filter_by_kwargs(kwargs=filters, paginator=pagination,
                                                                   order_by=order_params)
                serialized = self.serializer_class(dataset, many=True)

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)

    def post(self, request):
        data = get_request_body(request)
        record = self.serializer_class(data=data)
        record.is_valid(raise_exception=True)
        record.save()
        return Response(camelize(record.data), status=status.HTTP_200_OK)

    def put(self, request, **kwargs):
        data = get_request_body(request)
        record_id = kwargs.get(self.urlpattern_record_id_name)
        record_to_update = self.repository_class().get_by_id(record_id)
        self.check_object_permissions(request, obj=record_to_update)
        if self.nullable_fields.__len__():
            self.nullable_fields = self.repository_class().Model().get_nullable_fields()
        {data.setdefault(nullable_field) for nullable_field in self.nullable_fields}
        record = self.serializer_class(instance=record_to_update, data=data)
        try:
            record.is_valid(raise_exception=True)
        except HttpException:
            raise HttpException(detail='One or more fields passed as an ID were not found.',
                                status_code=Errors.NOT_FOUND)
        record.save()
        return Response(camelize(record.data), status=status.HTTP_200_OK)

    def patch(self, request, **kwargs):
        data = get_request_body(request)
        record_id = kwargs.get(self.urlpattern_record_id_name)
        record_to_update = self.repository_class().get_by_id(record_id)
        self.check_object_permissions(request, obj=record_to_update)
        record = self.serializer_class(instance=record_to_update, data=data,
                                       partial=True)
        try:
            record.is_valid(raise_exception=True)
        except HttpException:  # 404 NOT_FOUND из BaseRepository
            raise HttpException(detail='One or more fields passed as an ID were not found.',
                                status_code=Errors.NOT_FOUND)
        record.save()
        return Response(camelize(record.data), status=status.HTTP_200_OK)

    def delete(self, request, record_id):
        self.repository_class().delete(record_id)
        return Response(data={'status': 200}, status=200)

    def get_queryset(self, **kwargs):
        """
        метод, помогающий подставить свой набор данных вместо стандартных
        'get_by_id' и 'get_all' в теле GET метода.
        """
        return None
