import os

from django.urls import path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from backend.enums import Environment

protocol = 'https'
if os.getenv('ENVIRONMENT', Environment.LOCAL.value) == Environment.LOCAL.value:
    protocol = 'http'

schema_view = get_schema_view(
    openapi.Info(
        title='giberno',
        default_version='v1',
        description='...',
        license=openapi.License(name='BSD License'),
    ),
    url=f"""{protocol}://{os.getenv('HOST_DOMAIN', 'localhost')}:{os.getenv('API_PORT', '80')}/""",
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
