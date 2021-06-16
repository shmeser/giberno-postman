from django.contrib.contenttypes.models import ContentType
from django.contrib.gis import admin
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.fields import JSONField, HStoreField
from django.db.models import Count, Sum, FloatField, ExpressionWrapper, Subquery, OuterRef
from django.db.models import UUIDField
from django.forms import TextInput, Textarea
from django.utils.timezone import now
from djangorestframework_camel_case.util import camelize
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from app_feedback.models import Review
from app_geo.models import Region
from app_media.enums import MimeTypes
from backend.entity import Error
from backend.errors.enums import ErrorsCodes
from backend.errors.enums import RESTErrors
from backend.errors.http_exceptions import CustomException
from backend.errors.http_exceptions import HttpException
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
        self.mime_type = MimeTypes.PNG.value  # if Platform.IOS.value in self.platform else MimeTypes.SVG.value

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


class MakeReviewMethodProviderRepository(MasterRepository):
    def __init__(self, me=None) -> None:
        super().__init__()
        self.me = me

    def make_review(self, record_id, text, value, shift=None, point=None):
        # TODO добавить загрузку attachments
        owner_content_type = ContentType.objects.get_for_model(self.me)
        owner_ct_id = owner_content_type.id
        owner_ct_name = owner_content_type.model
        owner_id = self.me.id

        target_content_type = ContentType.objects.get_for_model(self.model)
        target_ct_id = target_content_type.id
        target_ct_name = target_content_type.model
        target_id = record_id

        # проверяем валидность id
        self.get_by_id(record_id=target_id)
        region = Region.objects.filter(boundary__covers=point).first() if point else None

        if not Review.objects.filter(
                owner_ct_id=owner_ct_id,
                owner_id=owner_id,
                target_ct_id=target_ct_id,
                target_id=target_id,
                shift_id=shift,
                deleted=False
        ).exists():
            Review.objects.create(
                owner_ct_id=owner_ct_id,
                owner_id=owner_id,
                owner_ct_name=owner_ct_name,

                target_ct_id=target_ct_id,
                target_id=target_id,
                target_ct_name=target_ct_name,

                value=value,
                text=text,
                region=region,
                shift_id=shift
            )

            # Пересчитываем количество оценок и рейтинг
            self.model.objects.filter(pk=record_id).update(
                # в update нельзя использовать результаты annotate
                # используем annotate в Subquery
                rating=Subquery(
                    self.model.objects.filter(
                        id=OuterRef('id')
                    ).annotate(
                        calculated_rating=ExpressionWrapper(
                            Sum('reviews__value') / Count('reviews'),
                            output_field=FloatField()
                        )
                    ).values('calculated_rating')[:1]
                ),
                rates_count=Subquery(
                    self.model.objects.filter(
                        id=OuterRef('id')
                    ).annotate(
                        calculated_rates_count=Count('reviews'),
                    ).values('calculated_rates_count')[:1]
                ),
                updated_at=now()
            )


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


class FormattedAdmin(admin.OSMGeoAdmin):
    formfield_overrides = {
        ArrayField: {'widget': TextInput(attrs={'size': '150'})},
        models.CharField: {'widget': TextInput(attrs={'size': '150'})},
        UUIDField: {'widget': TextInput(attrs={'size': '150'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 10, 'cols': 150})},
        JSONField: {'widget': Textarea(attrs={'rows': 10, 'cols': 150})},
        HStoreField: {'widget': Textarea(attrs={'rows': 10, 'cols': 150})},
    }
