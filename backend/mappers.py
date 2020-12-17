import uuid as uuid

import inflection
from django.contrib.contenttypes.models import ContentType
from djangorestframework_camel_case.util import underscoreize

from app_media.enums import MediaType, MediaFormat
from app_media.forms import FileForm
from backend.entity import Pagination, File, Error
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exception import HttpException, CustomException
from backend.utils import timestamp_to_datetime as m_t_d, get_media_format, resize_image


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
                filter_values[param] = m_t_d(int(filter_values[param]))

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
                file_entity = File()

                owner_content_type = ContentType.objects.get_for_model(owner)

                file_entity.owner_content_type_id = owner_content_type.id
                file_entity.owner_content_type = owner_content_type.model
                file_entity.owner_id = owner.id

                file_entity.mime_type = form_file.content_type
                file_entity.format = get_media_format(file_entity.mime_type)
                file_entity.size = form_file.size

                file_entity.title = form.cleaned_data['title'] if 'title' in form.cleaned_data and form.cleaned_data[
                    'title'] else form_file.name
                file_entity.type = form.cleaned_data.get('type', MediaType.OTHER)

                name = str(uuid.uuid4())
                parts = form_file.name.split('.')
                if parts.__len__() > 1:
                    extension = '.' + parts[-1].lower()
                else:
                    extension = ''
                form_file.name = name + extension

                file_entity.file = form_file
                file_entity.mime_type = form_file.content_type

                if file_entity.format == MediaFormat.IMAGE:
                    file_entity.file, file_entity.preview, file_entity.width, file_entity.height, file_entity.size = \
                        resize_image(form_file)
                if file_entity.format == MediaFormat.AUDIO:
                    # duration
                    pass
                if file_entity.format == MediaFormat.VIDEO:
                    # width
                    # height
                    # duration
                    # preview
                    pass
                if file_entity.format == MediaFormat.UNKNOWN:  # Если пришел неизвестный формат файла
                    raise CustomException(errors=[
                        dict(Error(ErrorsCodes.UNSUPPORTED_FILE_FORMAT))
                    ])

                # Не создаем пустые записи, если файл не удалось обработать
                if file_entity.file is not None:
                    entities.append(file_entity)

            return entities
        else:
            # TODO подробные ошибки валидации формы
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.VALIDATION_ERROR)),
                dict(Error(ErrorsCodes.EMPTY_REQUIRED_FIELDS)),
            ])
