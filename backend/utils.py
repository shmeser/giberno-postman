import csv
import datetime
import importlib
import json
import os
import re
from functools import reduce
from io import BytesIO
from json import JSONDecodeError
from urllib.request import urlopen, HTTPError, Request
from uuid import UUID

import exiftool
import pytz
from PIL import Image, ExifTags
from django.conf import settings
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.db.models import Lookup, Field
from django.db.models.expressions import Func, Expression, F, Value as V
from django.db.models.functions.datetime import TruncBase
from django.utils.timezone import make_aware, get_current_timezone, localtime
from djangorestframework_camel_case.util import underscoreize
from ffmpy import FFmpeg
from loguru import logger
from timezonefinder import TimezoneFinder

from app_media.enums import MediaFormat, FileDownloadStatus, MimeTypes
from backend.entity import File as FileEntity
from backend.errors.enums import RESTErrors
from backend.errors.http_exceptions import HttpException
from giberno.settings import DOCUMENT_MIME_TYPES, IMAGE_MIME_TYPES, IMAGE_SIDE_MAX, IMAGE_PREVIEW_SIDE_MAX, \
    VIDEO_MIME_TYPES, VIDEO_PREVIEW_SIDE_MAX, VIDEO_SIDE_MAX


def get_request_headers(request):
    headers = {}
    for k, v in request.headers.items():
        headers[k] = v
    return headers


def get_request_body(request):
    if not request.body:
        raise HttpException(detail=RESTErrors.BAD_REQUEST.name, status_code=RESTErrors.BAD_REQUEST)
    try:
        data = json.loads(request.body.decode('utf-8'))
        return underscoreize(data)
    except JSONDecodeError:
        data = request.body.decode('utf-8')
        return data


def choices(em):
    return [(e.value, e.name) for e in em]


def timestamp_to_datetime(timestamp, local_time=True, milliseconds=True):
    delta = datetime.timedelta(milliseconds=timestamp) if milliseconds else datetime.timedelta(seconds=timestamp)
    if local_time:
        tz = get_current_timezone()
        overflowed_date = make_aware(
            datetime.datetime(1970, 1, 1) + delta, pytz.timezone("UTC")
        )
        overflowed_date = localtime(overflowed_date, tz)
    else:
        overflowed_date = make_aware(
            datetime.datetime(1970, 1, 1) + delta, pytz.timezone("UTC")
        )
    return overflowed_date


def datetime_to_timestamp(date_time, milliseconds=True):
    try:
        # для возможности выбора дат за пределами границ таймштампа используем разницу дат с эпохой
        diff = date_time.replace(tzinfo=None) - datetime.datetime(1970, 1, 1)
        multiplier = 1000 if milliseconds else 1
        large_timestamp = int(diff.total_seconds() * multiplier)
        return large_timestamp
    except Exception as e:
        logger.error(e)
        return None


def create_admin_serializer(cls):
    meta_model = cls.Meta.model

    class AdminSerializer(cls):
        class Meta:
            model = meta_model
            exclude = ['deleted']

    return AdminSerializer


def user_is_admin(user):
    return 'admins' in user.groups.values_list('name', flat=True)


def chunks_func(list_data, n):
    """Дробим список на части по n элементов"""
    for i in range(0, len(list_data), n):
        yield list_data[i:i + n]


def chunks(list_data, n):
    return list(chunks_func(list_data, n))


def get_media_format(mime_type=None):
    if mime_type in DOCUMENT_MIME_TYPES:
        return MediaFormat.DOCUMENT.value
    if mime_type in IMAGE_MIME_TYPES:
        return MediaFormat.IMAGE.value
    if mime_type in VIDEO_MIME_TYPES:
        return MediaFormat.VIDEO.value
    return MediaFormat.UNKNOWN.value


def rotate_image(img):
    # Переворачиваем повернутые изображения
    orientation_tag = None
    try:
        for tag in ExifTags.TAGS.keys():
            if ExifTags.TAGS[tag] == 'Orientation':
                orientation_tag = tag
                break
        exif = dict(img._getexif().items())

        if exif[orientation_tag] == 2:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        elif exif[orientation_tag] == 3:
            img = img.transpose(Image.ROTATE_180)
        elif exif[orientation_tag] == 4:
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
        elif exif[orientation_tag] == 5:
            img = img.transpose(Image.ROTATE_270)
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        elif exif[orientation_tag] == 6:
            img = img.transpose(Image.ROTATE_270)
        elif exif[orientation_tag] == 7:
            img = img.transpose(Image.ROTATE_90)
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        elif exif[orientation_tag] == 8:
            img = img.transpose(Image.ROTATE_90)
        #####
        return img
    except Exception as e:
        logger.error(e)
        return img


def resize_image(file_entity: FileEntity):
    try:
        # копируем объект загруженного в память файла

        img = Image.open(file_entity.file)
        blob = BytesIO()

        img_format = str(img.format).lower()
        img_width = img.width or None
        img_height = img.height or None

        img = rotate_image(img)

        convert_to = 'RGB'
        if img_format in ['png', 'gif', 'tiff', 'bmp']:
            convert_to = 'RGBA'

        img = img.convert(convert_to)

        """ Изменяем размер, если выходит за установленные пределы """
        if img.width > IMAGE_SIDE_MAX or img.height > IMAGE_SIDE_MAX:
            img.thumbnail(size=(IMAGE_SIDE_MAX, IMAGE_SIDE_MAX))
            img_width = img.width
            img_height = img.height

        img.save(blob, img_format)

        result = TemporaryUploadedFile(
            size=blob.__sizeof__(),
            content_type=file_entity.file.content_type,
            name=file_entity.file.name,
            charset=file_entity.file.charset
        )
        img.save(result, img_format)

        """Создаем превью для изображения"""

        # Изменяем размер, если выходит за установленные пределы
        if img.width > IMAGE_PREVIEW_SIDE_MAX or img.height > IMAGE_PREVIEW_SIDE_MAX:
            img.thumbnail(size=(IMAGE_PREVIEW_SIDE_MAX, IMAGE_PREVIEW_SIDE_MAX))

        img.save(blob, img_format)

        preview = TemporaryUploadedFile(
            size=blob.__sizeof__(),
            content_type=file_entity.file.content_type,
            name=file_entity.file.name,
            charset=file_entity.file.charset
        )

        img.save(preview, img_format)

        file_entity.file = result
        file_entity.preview = preview
        file_entity.width = img_width
        file_entity.height = img_height
        file_entity.size = result.size
    except Exception as e:
        logger.error(e)
        file_entity.file = None
        file_entity.preview = None
        file_entity.width = None
        file_entity.height = None
        file_entity.size = None


def convert_video(file_entity: FileEntity):
    try:
        input_full = file_entity.file.file.name
        _META = get_media_metadata(input_full)

        # TODO Проставить корректные повороты
        # Размеры превью для видео
        preview_width = _META['width']
        preview_height = _META['height']

        vertical = True if _META['width'] > _META['height'] and _META['rotation'] in [90, 270] else False

        if _META['width'] > VIDEO_PREVIEW_SIDE_MAX or _META['height'] > VIDEO_PREVIEW_SIDE_MAX:
            if vertical:
                preview_width = '-1'
                preview_height = VIDEO_PREVIEW_SIDE_MAX
            else:
                preview_width = VIDEO_PREVIEW_SIDE_MAX
                preview_height = '-1'

        # Размеры итогового видео
        converted_width = _META['width']
        converted_height = _META['height']
        if _META['width'] > VIDEO_SIDE_MAX or _META['height'] > VIDEO_SIDE_MAX:
            if vertical:
                converted_width = '-1'
                converted_height = VIDEO_SIDE_MAX
            else:
                converted_width = VIDEO_SIDE_MAX
                converted_height = '-1'

        transpose = ''
        # TODO Проставить корректные повороты
        if _META['rotation'] == 180:  # Если повернуто на 180 градусов, то поворачиваем 2 раза по 90 CW
            transpose = ',transpose=1,transpose=1'
        if _META['rotation'] == 270:  # Если повернуто на 270 градусов CW, то поворачиваем 3 раза по 90 CW
            transpose = ',transpose=1'

        preview_resizing = f"scale={preview_width}:{preview_height}" + transpose
        converted_resizing = f"scale={converted_width}:{converted_height}" + transpose

        preview_params = [
            # масштабирование с сохранением пропорций (-2 для поддержки разных видео кодеков)
            '-filter:v', preview_resizing,
            '-abort_on', 'empty_output',  # вызывать ошибку, если пустой файл превью
            '-ss', '1',  # Сдвиг от начала видео в секундах
            '-vframes', '1',
            '-y'
        ]

        converted_params = [
            # масштабирование с сохранением пропорций (-2 для поддержки разных видео кодеков)
            '-filter:v', converted_resizing,
            '-abort_on', 'empty_output',  # вызывать ошибку, если пустой файл превью
            '-y'
        ]

        # Создаем временные файлы, которые удалятся после использования
        result = TemporaryUploadedFile(
            size=file_entity.file.size,
            content_type=file_entity.file.content_type,
            name=file_entity.file.name,
            charset=file_entity.file.charset
        )

        preview = TemporaryUploadedFile(
            size=file_entity.file.size,
            content_type=MimeTypes.JPEG.value,
            name=f'{file_entity.uuid}.jpg',
            charset=file_entity.file.charset
        )

        # Адреса временных файлов под видео и превью
        preview_temp_location = preview.file.name
        converted_temp_location = result.file.name

        ff = FFmpeg(
            inputs={
                input_full: None
            },
            outputs={
                preview_temp_location: preview_params,
                converted_temp_location: converted_params
            }
        )

        ff.run()

        _RESULT_META = get_media_metadata(converted_temp_location)

        file_entity.file = result
        file_entity.preview = preview
        file_entity.width = _RESULT_META['width']
        file_entity.height = _RESULT_META['height']
        file_entity.duration = _RESULT_META['duration']
        file_entity.size = _RESULT_META['size']
    except Exception as e:
        logger.error(e)
        file_entity.file = None


def get_media_metadata(file_url):
    """ https://github.com/smarnach/pyexiftool/issues/26 """
    with exiftool.ExifTool() as et:
        # print(et.get_metadata(file_url))

        _ROTATION = 'Composite:Rotation'
        _IMAGE_SIZE = 'Composite:ImageSize'
        _FILE_SIZE = 'File:FileSize'
        _DURATION = 'QuickTime:Duration'

        tags = et.get_tags([_ROTATION, _IMAGE_SIZE, _FILE_SIZE, _DURATION], file_url)
        image_size = tags[_IMAGE_SIZE].split(' ') if _IMAGE_SIZE in tags else (0, 0)
        return {
            'width': int(image_size[0]),
            'height': int(image_size[1]),
            'rotation': tags[_ROTATION] if _ROTATION in tags else 0,
            'duration': tags[_DURATION] if _DURATION in tags else 0,
            'size': tags[_FILE_SIZE] if _FILE_SIZE in tags else 0,
        }


def has_latin(text: str = None):
    if text and isinstance(text, str):
        return bool(re.search('[a-zA-Z]', text))
    return False


def nonefy(value, condition=True):
    if condition:
        return None
    return value


def chained_get(obj, *args, default=None):
    def get_value(o, attr):
        if isinstance(o, dict) and (isinstance(attr, str) or attr is None):
            return o.get(attr, default)
        if isinstance(o, (list, tuple)) and isinstance(attr, int):
            return o[attr]
        if isinstance(o, object) and isinstance(attr, str):
            return getattr(o, attr, default)
        return None

    try:
        result = reduce(get_value, args, obj)
        return result
    except Exception:
        return default


def get_remote_file(remote_url):
    status = FileDownloadStatus.FAIL.value
    downloaded_file = None
    content_type = None
    size = 0

    fake_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/79.0.3945.130 Safari/537.36',
        'accept-encoding': 'gzip, deflate, br'
    }

    try:
        req = Request(url=remote_url, headers=fake_headers)
        opened_url = urlopen(req)
        downloaded_file = opened_url.read()
        info = opened_url.info()
        content_type = info.get_content_type()
        size = int(opened_url.getheader('Content-Length'))
        status = FileDownloadStatus.SAVED.value
    except HTTPError as e:
        if e.code == RESTErrors.NOT_FOUND.value:
            status = FileDownloadStatus.NOT_EXIST.value
    except Exception as e:
        logger.error(e)
    return downloaded_file, content_type, size, status


def remove_file_from_server(relative_url=None):
    if relative_url:
        try:
            os.remove(os.path.join(settings.MEDIA_ROOT, relative_url))
        except Exception as e:
            logger.error(e)


def is_valid_uuid(uuid_to_test, version=4):
    try:
        UUID(uuid_to_test, version=version)
        return True
    except ValueError:
        return False


class SimpleFunc(Func):
    def __init__(self, field, *values, **extra):
        if not isinstance(field, Expression):
            field = F(field)
            if values and not isinstance(values[0], Expression):
                values = [V(v) for v in values]
        super(SimpleFunc, self).__init__(field, *values, **extra)


class ArrayRemove(SimpleFunc):
    """
        Реализация Postgres функции array_remove, которой нет в Django
    """
    function = 'ARRAY_REMOVE'


class TruncMilliecond(TruncBase):
    """
        Отсутствующий в Django класс для миллисекунд
    """
    kind = 'millisecond'


class RruleListOccurences(Func):
    function = 'rrule_list_occurences'
    template = "%(function)s(%(expressions)s, 'Zeus')"


# ####


def read_csv(file_name):
    try:
        with open(file_name, newline='', encoding='utf-8-sig') as csv_result:
            result = []
            reader = csv.reader(csv_result, delimiter=',')
            for row in reader:
                if row[0].__len__() > 0:
                    result.append(row)
            return result
    except Exception:
        print('ERROR')


class CustomLookupBase(Lookup):
    # Кастомный lookup
    lookup_name = 'custom'
    parametric_string = "%s <= %s AT TIME ZONE timezone"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return self.parametric_string % (lhs, rhs), params


@Field.register_lookup
class DatesArrayContains(CustomLookupBase):
    # Кастомный lookup с приведением типов для массива дат
    lookup_name = 'dacontains'
    parametric_string = "%s::DATE[] @> %s"


@Field.register_lookup
class LTTimeTZ(CustomLookupBase):
    # Кастомный lookup для сравнения времени с учетом временной зоны из поля timezone
    lookup_name = 'lttimetz'
    parametric_string = "%s < %s AT TIME ZONE timezone"


@Field.register_lookup
class LTETimeTZ(CustomLookupBase):
    # Кастомный lookup для сравнения времени с учетом временной зоны из поля timezone
    lookup_name = 'ltetimetz'
    parametric_string = "%s <= %s AT TIME ZONE timezone"


@Field.register_lookup
class GTETimeTZ(CustomLookupBase):
    # Кастомный lookup для сравнения времени с учетом временной зоны из поля timezone
    lookup_name = 'gtetimetz'
    parametric_string = "%s >= %s AT TIME ZONE timezone"


@Field.register_lookup
class GTTimeTZ(CustomLookupBase):
    # Кастомный lookup для сравнения времени с учетом временной зоны из поля timezone
    lookup_name = 'gttimetz'
    parametric_string = "%s > %s AT TIME ZONE timezone"


@Field.register_lookup
class LTdtTZ(CustomLookupBase):
    # Кастомный lookup для сравнения времени с учетом временной зоны из поля timezone
    lookup_name = 'ltdttz'
    parametric_string = "%s AT TIME ZONE timezone < %s AT TIME ZONE timezone"


@Field.register_lookup
class LTEdtTZ(CustomLookupBase):
    # Кастомный lookup для сравнения времени с учетом временной зоны из поля timezone
    lookup_name = 'ltedttz'
    parametric_string = "%s AT TIME ZONE timezone <= %s AT TIME ZONE timezone"


@Field.register_lookup
class GTEdtTZ(CustomLookupBase):
    # Кастомный lookup для сравнения времени с учетом временной зоны из поля timezone
    lookup_name = 'gtedttz'
    parametric_string = "%s AT TIME ZONE timezone >= %s AT TIME ZONE timezone"


@Field.register_lookup
class GTdtTZ(CustomLookupBase):
    # Кастомный lookup для сравнения времени с учетом временной зоны из поля timezone
    lookup_name = 'gtdttz'
    parametric_string = "%s AT TIME ZONE timezone > %s AT TIME ZONE timezone"


@Field.register_lookup
class DateTZ(CustomLookupBase):
    # Кастомный lookup с приведением типов для даты во временной зоне из поля timezone
    lookup_name = 'datetz'
    parametric_string = "(%s AT TIME ZONE timezone)::DATE = %s :: DATE"


@Field.register_lookup
class DateTZGte(CustomLookupBase):
    # Кастомный lookup с приведением типов для сравнения дат во временной зоне из поля timezone
    lookup_name = 'datetz_gte'
    parametric_string = "(%s AT TIME ZONE timezone)::DATE >= %s :: DATE"


@Field.register_lookup
class DateTZLte(CustomLookupBase):
    # Кастомный lookup с приведением типов для сравнения дат во временной зоне из поля timezone
    lookup_name = 'datetz_lte'
    parametric_string = "(%s AT TIME ZONE timezone)::DATE <= %s :: DATE"


@Field.register_lookup
class MSLteContains(CustomLookupBase):
    # Кастомный lookup для фильтрации DateTime по миллисекундам (в бд записи с точностью до МИКРОсекунд)
    lookup_name = 'ms_lte'
    parametric_string = "DATE_TRUNC('millisecond', %s)::TIMESTAMPTZ <= %s"


@Field.register_lookup
class MSGteContains(CustomLookupBase):
    # Кастомный lookup для фильтрации DateTime по миллисекундам (в бд записи с точностью до МИКРОсекунд)
    lookup_name = 'ms_gte'
    parametric_string = "DATE_TRUNC('millisecond', %s)::TIMESTAMPTZ >= %s"


def get_timezone_name_from_utcoffset(seconds):
    utc_offset = datetime.timedelta(seconds=seconds)
    utc_now = datetime.datetime.now(pytz.utc)  # current time UTC
    tz_list = [tz for tz in map(pytz.timezone, pytz.common_timezones_set) if
               utc_now.astimezone(tz).utcoffset() == -utc_offset]
    if tz_list:
        return tz_list[0]

    return 'UTC'


def get_timezone_name_by_geo(lon, lat):
    try:
        tf = TimezoneFinder()
        timezone_name = tf.timezone_at(lng=lon, lat=lat)  # возвращает tz вида 'Europe/Moscow'
        return timezone_name
    except Exception as e:
        logger.error(e)
        return 'UTC'
