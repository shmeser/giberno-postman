import csv
import datetime
import importlib
import json
from json import JSONDecodeError

import pytz
from django.utils.timezone import make_aware, get_current_timezone, localtime
from djangorestframework_camel_case.util import underscoreize

from backend.errors.enums import RESTErrors
from backend.errors.http_exception import HttpException


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


def custom_jwt_get_secret_key(user):
    return user.secret_key


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
