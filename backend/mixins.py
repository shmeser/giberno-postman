from djangorestframework_camel_case.util import camelize
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from app_media.enums import MimeTypes
from backend.entity import Error
from backend.enums import Platform
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exception import HttpException, CustomException
from backend.mappers import RequestMapper
from backend.permissions import AbbleToPerform
from backend.repositories import BaseRepository
from backend.utils import create_admin_serializer, get_request_body, user_is_admin, chained_get


class CRUDSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.me = chained_get(kwargs, 'context', 'me')
        self.headers = chained_get(kwargs, 'context', 'headers')
        self.platform = chained_get(kwargs, 'context', 'headers', 'Platform', default='').lower()
        self.mime_type = MimeTypes.PNG.value if Platform.IOS.value in self.platform else MimeTypes.SVG.value

    repository = None

    def create(self, validated_data):
        return self.repository().create(**validated_data)

    def update(self, instance, validated_data):
        return self.repository().update(instance.id, **validated_data)

    def process_validation_errors(self, errors):
        errors_processed = []
        for k, e in errors.items():
            if ErrorsCodes.has_key(e[0].code):
                errors_processed.append(dict(Error(ErrorsCodes[e[0].code])))
            else:
                code = ErrorsCodes.VALIDATION_ERROR.name
                detail = ErrorsCodes.VALIDATION_ERROR.value

                if e[0].code == 'unique':
                    if k == 'email':  # Конкретная проверка на уникальность имейла в бд
                        code = ErrorsCodes.EMAIL_IS_USED.name
                    detail = e[0]

                if e[0].code == 'required':
                    detail = k + ' - ' + e[0]

                # Добавляем в массив кастомных ошибок
                errors_processed.append(
                    dict(Error(**{
                        'code': code,
                        'detail': detail
                    }))
                )
        return errors_processed

    def is_valid(self, raise_exception=False):
        # Переопределяем метод для использования кастомной ошибки
        assert hasattr(self, 'initial_data'), (
            'Cannot call `.is_valid()` as no `data=` keyword argument was '
            'passed when instantiating the serializer instance.'
        )

        if not hasattr(self, '_validated_data'):
            try:
                self._validated_data = self.run_validation(self.initial_data)
            except ValidationError as exc:
                self._validated_data = {}
                self._errors = exc.detail
            else:
                self._errors = {}

        if self._errors and raise_exception:
            # Обрабатываем список ошибок валидаторов ValidationError
            errors_processed = self.process_validation_errors(self.errors)
            raise CustomException(errors=errors_processed)

        return not bool(self._errors)


class MasterRepository(BaseRepository):
    model = None

    def __init__(self):
        super().__init__(self.model)


class CRUDAPIView(APIView):
    many = False
    serializer_class = None
    repository_class = None
    urlpattern_record_id_name = 'record_id'
    filter_params = dict()
    order_params = dict()
    date_filter_params = dict()  # словарь c фильтрами в timestamp
    bool_filter_params = dict()  # словарь с фильтрами c типом Bool
    array_filter_params = dict()  # словарь с массивом фильтров, на входе 1 значение либо несколько через запятую
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
    default_filters = {}

    def __init__(self, **kwargs):
        super().__init__()
        if self.allowed_http_methods:
            self.http_method_names = self.allowed_http_methods

    def get_admin_dataset_and_serializer(self, record_id=None, filters=None, pagination=None, order_params={}):
        if self.many:
            dataset = super(self.repository_class().__class__, self.repository_class()).filter_by_kwargs(
                kwargs=filters, paginator=pagination, order_by=order_params)
            if self.admin_serializer:
                serializer_class = self.admin_serializer
            else:
                serializer_class = create_admin_serializer(self.serializer_class)
        else:
            dataset = super(self.repository_class().__class__, self.repository_class()).get_by_id(record_id)
            if self.admin_serializer:
                serializer_class = self.admin_serializer
            else:
                serializer_class = create_admin_serializer(self.serializer_class)
        return dataset, serializer_class

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        queryset = self.get_queryset(request=request, **kwargs)

        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        if record_id:
            if user_is_admin(request.user) and request.user.is_superuser:
                dataset, serializer_class = self.get_admin_dataset_and_serializer(record_id=record_id)
            else:
                dataset = self.repository_class().get_by_id(record_id)
                serializer_class = self.serializer_class

        elif queryset is not None:
            self.many = True
            serializer_class = self.serializer_class
            dataset = queryset
            dataset = dataset.order_by(*order_params).filter(**filters)
            dataset = dataset[pagination.offset:pagination.limit]

        else:
            self.many = True
            if user_is_admin(request.user) and request.user.is_superuser:
                dataset, serializer_class = self.get_admin_dataset_and_serializer(
                    filters=filters, pagination=pagination, order_params=order_params)
            else:
                dataset = self.repository_class().filter_by_kwargs(kwargs=filters, paginator=pagination,
                                                                   order_by=order_params)
                serializer_class = self.serializer_class

        serialized = serializer_class(dataset, many=self.many)
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
                                status_code=RESTErrors.NOT_FOUND)
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
            raise HttpException(
                detail='One or more fields passed as an ID were not found.',
                status_code=RESTErrors.NOT_FOUND)
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
