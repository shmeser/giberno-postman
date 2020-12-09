import os

DEBUG = True

ALLOWED_HOSTS = [
    os.getenv('MACHINE_HOST', '127.0.0.1'),
    os.getenv('HOST_IP', '127.0.0.1'),
    os.getenv('HOST_DOMAIN', '127.0.0.1')
]

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DB_NAME', 'db-name'),
        'USER': os.getenv('DB_USER', 'db-user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'db-password'),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '127.0.0.1'),
    },
}
