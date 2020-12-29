import csv
import datetime
import importlib
import json
import os
import re
from io import BytesIO
from json import JSONDecodeError
from urllib.request import urlopen, HTTPError, Request

import exiftool
import pytz
from PIL import Image
from django.conf import settings
from django.core.files.uploadedfile import TemporaryUploadedFile,UploadedFile
from django.utils.timezone import make_aware, get_current_timezone, localtime
from djangorestframework_camel_case.util import underscoreize
from ffmpy import FFmpeg

from app_media.enums import MediaFormat, FileDownloadStatus, MimeTypes
from backend.entity import File as FileEntity
from backend.errors.enums import RESTErrors
from backend.errors.http_exception import HttpException
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


class CP:
    """
    Цветной форматированный вывод в консоль
    """

    def __init__(self, **kwargs):
        self.fg = self.FG.black
        if kwargs.get('fg', '') == 'black':
            self.fg = self.FG.black
        if kwargs.get('fg', '') == 'red':
            self.fg = self.FG.red
        if kwargs.get('fg', '') == 'green':
            self.fg = self.FG.green
        if kwargs.get('fg', '') == 'orange':
            self.fg = self.FG.orange
        if kwargs.get('fg', '') == 'blue':
            self.fg = self.FG.blue
        if kwargs.get('fg', '') == 'purple':
            self.fg = self.FG.purple
        if kwargs.get('fg', '') == 'cyan':
            self.fg = self.FG.cyan
        if kwargs.get('fg', '') == 'lightgrey':
            self.fg = self.FG.lightgrey
        if kwargs.get('fg', '') == 'darkgrey':
            self.fg = self.FG.darkgrey
        if kwargs.get('fg', '') == 'lightred':
            self.fg = self.FG.lightred
        if kwargs.get('fg', '') == 'lightgreen':
            self.fg = self.FG.lightgreen
        if kwargs.get('fg', '') == 'yellow':
            self.fg = self.FG.yellow
        if kwargs.get('fg', '') == 'lightblue':
            self.fg = self.FG.lightblue
        if kwargs.get('fg', '') == 'pink':
            self.fg = self.FG.pink
        if kwargs.get('fg', '') == 'lightcyan':
            self.fg = self.FG.lightcyan

        self.bg = self.BG.black
        if kwargs.get('bg', '') == 'black':
            self.bg = self.BG.black
        if kwargs.get('bg', '') == 'red':
            self.bg = self.BG.red
        if kwargs.get('bg', '') == 'green':
            self.bg = self.BG.green
        if kwargs.get('bg', '') == 'orange':
            self.bg = self.BG.orange
        if kwargs.get('bg', '') == 'blue':
            self.bg = self.BG.blue
        if kwargs.get('bg', '') == 'purple':
            self.bg = self.BG.purple
        if kwargs.get('bg', '') == 'cyan':
            self.bg = self.BG.cyan
        if kwargs.get('bg', '') == 'lightgrey':
            self.bg = self.BG.lightgrey

        self.sp = int(kwargs.get('sp', 0))
        self.nl = kwargs.get('nl', True)

    RESET = '\033[0m'
    BOLD = '\033[01m'
    DISABLE = '\033[02m'
    UNDERLINE = '\033[04m'
    REVERSE = '\033[07m'
    STRIKETHROUGH = '\033[09m'
    INVISIBLE = '\033[08m'

    def get_tabs(self):
        tab_code = '\t'
        tabs = ''
        while self.sp > 0:
            tabs += tab_code
            self.sp -= 1

        return tabs

    class FG:
        black = '\033[30m'
        red = '\033[31m'
        green = '\033[32m'
        orange = '\033[33m'
        blue = '\033[34m'
        purple = '\033[35m'
        cyan = '\033[36m'
        lightgrey = '\033[37m'
        darkgrey = '\033[90m'
        lightred = '\033[91m'
        lightgreen = '\033[92m'
        yellow = '\033[93m'
        lightblue = '\033[94m'
        pink = '\033[95m'
        lightcyan = '\033[96m'

    class BG:
        black = '\033[30m'  # '\033[40m' стояло хз че за цвет
        red = '\033[41m'
        green = '\033[42m'
        orange = '\033[43m'
        blue = '\033[44m'
        purple = '\033[45m'
        cyan = '\033[46m'
        lightgrey = '\033[47m'

    def bold(self, data=''):
        data = str(data)
        end = '\n' if self.nl else ''
        print(f"{self.get_tabs()}{self.BOLD}{self.bg}{self.fg}" + data + f"{self.RESET}", end=end)

    def disable(self, data=''):
        data = str(data)
        end = '\n' if self.nl else ''
        print(f"{self.get_tabs()}{self.DISABLE}{self.bg}{self.fg}" + data + f"{self.RESET}", end=end)

    def underline(self, data=''):
        data = str(data)
        end = '\n' if self.nl else ''
        print(f"{self.get_tabs()}{self.UNDERLINE}{self.bg}{self.fg}" + data + f"{self.RESET}", end=end)

    def reverse(self, data=''):
        data = str(data)
        end = '\n' if self.nl else ''
        print(f"{self.get_tabs()}{self.REVERSE}{self.bg}{self.fg}" + data + f"{self.RESET}", end=end)

    def strikethrough(self, data=''):
        data = str(data)
        end = '\n' if self.nl else ''
        print(f"{self.get_tabs()}{self.STRIKETHROUGH}{self.bg}{self.fg}" + data + f"{self.RESET}", end=end)

    def invisible(self, data=''):
        data = str(data)
        end = '\n' if self.nl else ''
        print(f"{self.get_tabs()}{self.INVISIBLE}{self.bg}{self.fg}" + data + f"{self.RESET}", end=end)


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
        CP(sp=1, fg='yellow').bold(e)
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
    # if mime_type in AUDIO_MIME_TYPES:
    #     return MediaFormat.AUDIO.value
    if mime_type in VIDEO_MIME_TYPES:
        return MediaFormat.VIDEO.value
    return MediaFormat.UNKNOWN.value


def resize_image(file_entity: FileEntity):
    try:
        # копируем объект загруженного в память файла

        img = Image.open(file_entity.file)
        blob = BytesIO()

        img_format = str(img.format).lower()
        img_width = img.width or None
        img_height = img.height or None

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
        CP(bg='red').bold(e)
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
        if _META['width'] > VIDEO_PREVIEW_SIDE_MAX or _META['height'] > VIDEO_PREVIEW_SIDE_MAX:
            if _META['width'] > _META['height'] and _META['rotation'] in [90, 270] or _META['width'] < _META['height']:
                preview_width = '-1'
                preview_height = VIDEO_PREVIEW_SIDE_MAX
            else:
                preview_width = VIDEO_PREVIEW_SIDE_MAX
                preview_height = '-1'

        # Размеры итогового видео
        converted_width = _META['width']
        converted_height = _META['height']
        if _META['width'] > VIDEO_SIDE_MAX or _META['height'] > VIDEO_SIDE_MAX:
            if _META['width'] > _META['height'] and _META['rotation'] in [90, 270] or _META['width'] < _META['height']:
                converted_width = '-1'
                converted_height = VIDEO_SIDE_MAX
            else:
                converted_width = VIDEO_SIDE_MAX
                converted_height = '-1'

        transpose = ''
        # TODO Проставить корректные повороты
        if _META['rotation'] == 180:  # Если повернуто на 180 градусов, то поворачиваем 2 раза по 90 CW
            transpose = ',transpose=1,transpose=1'
        # if _META['rotation'] == 90:  # Если повернуто на 90 CW градусов, то поворачиваем на 90 CW
        #     transpose = ',transpose=1,transpose=1,transpose=1'
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
        CP(bg='red').bold(e)
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
        CP(fg='yellow', bg='red').bold(e)
    return downloaded_file, content_type, size, status


def remove_file_from_server(relative_url=None):
    if relative_url:
        try:
            os.remove(os.path.join(settings.MEDIA_ROOT, relative_url))
        except Exception as e:
            CP(fg='yellow', bg='red').bold(e)


# ####


def assign_swagger_decorator(app_name, view_names, responses: dict = None):
    from drf_yasg.utils import swagger_auto_schema

    module = importlib.import_module(f'{app_name}.views')
    for view_name in view_names:
        view_class = getattr(module, view_name)

        try:
            # CRUDAPIView
            allowed_http_methods = view_class.allowed_http_methods
        except AttributeError:
            # APIView or if 'allowed_http_methods' list not defined
            allowed_http_methods = [method for method in view_class.http_method_names if method in view_class.__dict__]

        for method in allowed_http_methods:
            view_method = getattr(view_class, method)
            if not responses:
                try:
                    lresponses = {200: view_class.serializer_class}
                except (TypeError, AttributeError):
                    raise NotImplementedError('Serializer class not found in view.')
            decorator = swagger_auto_schema(tags=[view_class.__name__], responses=lresponses)
            decorator(view_method)


def read_csv(file_name):
    try:
        with open(file_name, newline='', encoding='utf-8-sig') as csv_result:
            result = []
            reader = csv.reader(csv_result, delimiter=',')
            for row in reader:
                if row[0].__len__() > 0:
                    result.append(row)
            return result
    except Exception as e:
        print('ERROR')
