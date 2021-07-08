from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

from app_users.views import social_web_auth, login
from frontend.views import PolicyView, AgreementView, DocumentsView, TermsView
from giberno import settings

urlpatterns = [
                  path('django/admin/', admin.site.urls),
              ] \
              + static(settings.LOGS_URL, document_root=settings.LOGS_ROOT) \
              + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) \
              + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

social_web_auth = [
    path('auth/socials/', include('social_django.urls', namespace="social")),
    path('auth/socials/logout', auth_views.LogoutView.as_view(), name="web-logout"),
    path('auth/socials/login', login, name="login"),
    path('auth/socials/web', social_web_auth, name="web"),
]

service_urls = [
    path('documents', DocumentsView.as_view()),
    path('terms', TermsView.as_view()),
    path('policy', PolicyView.as_view()),
    path('agreement', AgreementView.as_view()),
    path('bot/', include('app_bot.urls')),
    path('sockets/', include('app_sockets.urls')),
]

v1_0 = 'v1.0/'
v1_0_urls = [
    path(v1_0, include(('app_users.urls', 'users_1_0'))),
    path(v1_0, include(('app_geo.urls', 'geo_1_0'))),
    path(v1_0, include(('app_market.urls', 'market_1_0'))),
    path(v1_0, include(('app_chats.urls', 'chats_1_0'))),
]

urlpatterns += social_web_auth
urlpatterns += service_urls

urlpatterns += v1_0_urls
if settings.DEBUG:
    test_urls = [
        path('test/', include('app_tests.urls')),
    ]
    urlpatterns += test_urls
