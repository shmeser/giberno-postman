import datetime
import os
from datetime import timedelta, datetime

from celery.schedules import crontab

from giberno.settings_vars.celery_beat_schedule import celery_beat_schedule

SECRET_KEY = os.getenv('SECRET_KEY', 'TeStSeCrEtKeY')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INSTALLED_APPS = [
    'channels',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'django.contrib.postgres',
    'rest_framework',
    'rest_framework_simplejwt',
    'fcm_django',
    'celery',
    'constance',
    'social_django',
    'backend.apps.BackendConfig',
    'app_seeds.apps.AppSeedsConfig',
    'app_bot.apps.AppBotConfig',
    'app_users.apps.AppUsersConfig',
    'app_media.apps.AppMediaConfig',
    'app_geo.apps.AppGeoConfig',
    'app_market.apps.AppMarketConfig',
    'app_feedback.apps.AppFeedbackConfig',
    'app_sockets.apps.AppSocketsConfig',
    'app_chats.apps.AppChatsConfig',
    'app_games.apps.AppGamesConfig',
]

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(os.getenv('REDIS_HOST', '127.0.0.1'), 6379)],
        },
    },
}

CELERY_BROKER_URL = os.getenv('CELERY_BROKER', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_BROKER', 'redis://127.0.0.1:6379/0')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
WORKER_MAX_MEMORY_PER_CHILD = 200000

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

INTERNAL_IPS = ("127.0.0.1",)  # DebugToolbar

GEOIP_PATH = os.path.join('backend')
ROOT_URLCONF = 'giberno.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

ASGI_APPLICATION = 'giberno.asgi.application'
WSGI_APPLICATION = 'giberno.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'UNAUTHENTICATED_USER': None,
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',

    'EXCEPTION_HANDLER': 'backend.errors.handlers.custom_exception_handler'
}

CELERY_BEAT_SCHEDULE = celery_beat_schedule

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),

    'AUTH_HEADER_TYPES': ('Bearer', 'JWT'),

    'USER_ID_FIELD': 'id',
    'PAYLOAD_ID_FIELD': 'uid',
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'

LOGS_URL = '/logs/'
MEDIA_URL = '/media/'

REACT_APP_DIR = os.path.join(BASE_DIR, 'frontend')

STATIC_ROOT = os.path.join(BASE_DIR, 'files', 'static')
MEDIA_ROOT = os.path.join(BASE_DIR, 'files', 'media')
LOGS_ROOT = os.path.join(BASE_DIR, 'files', 'logs')

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
    os.path.join(REACT_APP_DIR, 'build', 'static'),
)

AUTH_USER_MODEL = 'app_users.UserProfile'

IMAGE_RESIZE_QUALITY = 80

IMAGE_SIDE_MAX = 2048
IMAGE_PREVIEW_SIDE_MAX = 720

VIDEO_SIDE_MAX = 1920
VIDEO_PREVIEW_SIDE_MAX = 720

VIDEO_DURATION_MAX = 60

AUDIO_DURATION_MAX = 300

DOCUMENT_MIME_TYPES = [
    'application/msword',
    'application/pdf',
    'text/richtext',
    'text/plain',
    'application/vnd.ms-excel',
]

IMAGE_MIME_TYPES = [
    'image/bmp',
    'image/gif',
    'image/jpeg',
    'image/png',
    'image/tiff',
    'image/svg+xml',
]

AUDIO_MIME_TYPES = [
    'audio/mpeg',
    'audio/x-wav',
]

VIDEO_MIME_TYPES = [
    'video/x-msvideo',
    'video/quicktime',
    'video/mp4',
    'video/mpeg'
]

BONUS_PROGRESS_STEP_VALUE = 500  # Шаг в накоплении бонусов для получения новых карточек с "осколками"

# Устанавливаем единственный обработчик для загрузки файлов - через временные файлы на диске
FILE_UPLOAD_HANDLERS = [
    "django.core.files.uploadhandler.TemporaryFileUploadHandler"
]

FCM_DJANGO_SETTINGS = {
    'FCM_SERVER_KEY': os.getenv('FCM_SERVER_KEY', 'test'),
    'ONE_DEVICE_PER_USER': False,
    'DELETE_INACTIVE_DEVICES': True,
}

IN_APP_APPLE_BUNDLE_ID = os.getenv('IN_APP_APPLE_BUNDLE_ID', 'test')
IN_APP_GOOGLE_BUNDLE_ID = os.getenv('IN_APP_GOOGLE_BUNDLE_ID', 'test')

# social-auth start
AUTHENTICATION_BACKENDS = [
    'social_core.backends.vk.VKOAuth2',
    'django.contrib.auth.backends.ModelBackend'
]

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'web'
LOGOUT_URL = 'web'
LOGOUT_REDIRECT_URL = 'login'

# VK
SOCIAL_AUTH_VK_OAUTH2_KEY = os.getenv('VK_APP_ID', '')  # WEB AUTH
SOCIAL_AUTH_VK_OAUTH2_SECRET = os.getenv('VK_APP_SECRET', '')  # WEB AUTH
SOCIAL_AUTH_VK_OAUTH2_SCOPE = ['email', 'phone']

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.social_user',
    # custom pipelines
    'app_users.pipelines.exchange_access_token',
    'app_users.pipelines.get_or_create_user',
)

SOCIAL_AUTH_REDIRECT_IS_HTTPS = False  # Нужно True, так как facebook не позволяет указывать незащищенные url

# social-auth end

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_BOT_PASSWORD = os.getenv('TELEGRAM_BOT_PASSWORD', '')
TELEGRAM_URL = 'https://api.telegram.org/bot'

FCM_MAX_DEVICES_PER_REQUEST = 500  # Количество пушей за один запрос в Firebase

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'simple': {
            'format': '%(levelname)s %(asctime)s %(module)s: %(message)s',
        },
    },
    'handlers': {
        'telegram_log': {
            'level': 'ERROR',
            'class': 'app_bot.controllers.TelegramBotLogger',
        },
        'file_log': {
            'level': 'ERROR',
            'filename': 'files/logs/log.txt',
            'formatter': 'simple',
            'class': 'backend.logger.MakeFileHandler',
            'when': 'D',  # daily
            'backup_count': 100,  # 100 days backup
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['telegram_log', 'file_log'],
            'propagate': True,
        },
    },
}

AUTO_SWITCH_TO_BOT_MIN = 15

# POSTGIS ###
SRID = 4326  # WGS 84 -- WGS84 - World Geodetic System 1984, used in GPS
if os.name == 'nt':
    import platform

    OSGEO4W = r"C:\OSGeo4W"
    if '64' in platform.architecture()[0]:
        OSGEO4W += "64"
    assert os.path.isdir(OSGEO4W), "Directory does not exist: " + OSGEO4W
    os.environ['OSGEO4W_ROOT'] = OSGEO4W
    os.environ['GDAL_DATA'] = OSGEO4W + r"\share\gdal"
    os.environ['PROJ_LIB'] = OSGEO4W + r"\share\proj"
    os.environ['PATH'] = OSGEO4W + r"\bin;" + os.environ['PATH']

NEAREST_POINT_DISTANCE_MAX = 1000  # Максимальное расстояние до ближайшей точки для геокодинга координат
CLUSTER_NESTED_ITEMS_COUNT = 10
CLUSTER_MIN_POINTS_COUNT = 2
CLUSTER_ID_FIELD_NAME = 'cid'

# ### POSTGIS ###


CONSTANCE_REDIS_CONNECTION = {
    'host': os.getenv('REDIS_HOST', '127.0.0.1'),
    'port': 6379,
    'db': 0,
}

CONSTANCE_CONFIG = {
    'TELEGRAM_BOT_PASSWORD': (
        TELEGRAM_BOT_PASSWORD, 'Пароль для активации телеграм бота', str
    ),
}

DEBUG = True if os.getenv('DEBUG', False) in ['True', 'true', 'TRUE', True] else False

if DEBUG is not False:
    SWAGGER_SETTINGS = {
        'SECURITY_DEFINITIONS': {
            'JWT': {
                'type': 'apiKey',
                'name': 'Authorization',
                'in': 'header'
            },
            'Bearer': {
                'type': 'apiKey',
                'name': 'Authorization',
                'in': 'header'
            }
        }
    }

    APP_TEST = 'app_tests.apps.AppTestsConfig'
    INSTALLED_APPS.append(APP_TEST)

ALLOWED_HOSTS = [
    os.getenv('MACHINE_HOST', '127.0.0.1'),
    os.getenv('HOST_IP', '127.0.0.1'),
    os.getenv('HOST_DOMAIN', '127.0.0.1')
]

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DB_NAME', 'giberno'),
        'USER': os.getenv('DB_USER', 'admin'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'admin'),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '5432'),
    },
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', True)
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', False)
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = os.getenv('EMAIL_PORT', 587)
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'test@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'test')

GOOGLE_CLOUD_API_KEY = os.getenv('GOOGLE_CLOUD_API_KEY', '')

try:
    from giberno.environment.local_settings import \
        TELEGRAM_BOT_TOKEN, \
        TELEGRAM_BOT_PASSWORD, \
        DATABASES, \
        FCM_DJANGO_SETTINGS, \
        ALLOWED_HOSTS, \
        DEBUG, \
        CHANNEL_LAYERS, \
        CONSTANCE_REDIS_CONNECTION, \
        CONSTANCE_CONFIG, \
        LOGGING, \
        SOCIAL_AUTH_VK_OAUTH2_KEY, \
        EMAIL_HOST_USER, \
        GOOGLE_CLOUD_API_KEY, \
        EMAIL_HOST_PASSWORD
except ImportError as e:
    pass
