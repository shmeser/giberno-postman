import datetime
import os

from celery.schedules import crontab
from datetime import timedelta, datetime
from giberno.environment.environments import Environment

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
    'rest_framework',
    'rest_framework_simplejwt',
    'fcm_django',
    'drf_yasg',
    'celery',
    'constance',
    'social_django',
    'backend.apps.BackendConfig',
    'app_seeds.apps.AppSeedsConfig',
    'app_bot.apps.AppBotConfig',
    'app_users.apps.AppUsersConfig',
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
    'django_globals.middleware.Global',
]

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
                # 'social_django.context_processors.backends',
            ],
        },
    },
]

ASGI_APPLICATION = 'giberno.routing.application'
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
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning'
}

CELERY_BEAT_SCHEDULE = {
    # 'check_subscription': {
    #     'task': 'subscriptions.tasks.check_subscription',
    #     'schedule': crontab(hour='*', minute='0', day_of_week='*')
    # },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),

    'AUTH_HEADER_TYPES': ('Bearer', 'JWT'),

    'USER_ID_FIELD': 'id',
    'PAYLOAD_ID_FIELD': 'uid',
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# SILENCED_SYSTEM_CHECKS = ['urls.W002']

STATIC_URL = '/static/'

LOGS_URL = '/logs/'
MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join(BASE_DIR, 'files', 'static')
MEDIA_ROOT = os.path.join(BASE_DIR, 'files', 'media')
LOGS_ROOT = os.path.join(BASE_DIR, 'files', 'logs')

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

AUTH_USER_MODEL = 'app_users.UserProfile'

AVATAR_SIZE = 500, 500

AVATAR_FILE_TYPES = [
    'image/jpeg',
    'image/pjpeg',
    'image/png',
    'image/bmp',
    'image/x-windows-bmp'
]

DOCUMENT_FILE_TYPES = [
    'image/jpeg',
    'image/pjpeg',
    'image/png',
    'image/bmp',
    'image/x-windows-bmp',
    'application/pdf'
]

RAPIDAPI_KEY = os.getenv('X_RAPIDAPI_KEY')
RAPIDAPI_HOST = os.getenv('X_RAPIDAPI_HOST')

EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS')
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_PORT = os.getenv('EMAIL_PORT')

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

SOCIAL_AUTH_VK_OAUTH2_KEY = '7693503'
SOCIAL_AUTH_VK_OAUTH2_SECRET = 'kwAirsk5Y36eU3sp5Ken'
SOCIAL_AUTH_VK_OAUTH2_SCOPE = ['email']

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

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_BOT_PASSWORD = os.getenv('TELEGRAM_BOT_PASSWORD')
TELEGRAM_URL = 'https://api.telegram.org/bot'

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
            'class': 'app_bot.controllers.BotLogger',
        },
        'file_log': {
            'level': 'DEBUG',
            'filename': 'files/logs/log.txt',
            'formatter': 'simple',
            'class': 'backend.logger.MakeFileHandler',
            'when': 'D',  # daily
            'backupCount': 100,  # 100 days backup
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['telegram_log', 'file_log'],
            'propagate': True,
        },
    },
}

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

# ### POSTGIS ###


if os.getenv('ENVIRONMENT', Environment.LOCAL) == Environment.DEVELOP.value:
    from .environment.develop_settings import *
elif os.getenv('ENVIRONMENT', Environment.LOCAL) == Environment.STAGE.value:
    from .environment.stage_settings import *
elif os.getenv('ENVIRONMENT', Environment.LOCAL) == Environment.RELEASE.value:
    from .environment.release_settings import *
else:
    from .environment.local_settings import *
