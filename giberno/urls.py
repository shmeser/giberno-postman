from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.views.generic import RedirectView

from app_users.views import social_web_auth, login
from giberno import settings
from giberno.yasg import urlpatterns as doc_urls

urlpatterns = [
                  path('django/admin', admin.site.urls),
                  path('policy', RedirectView.as_view(url='/static/pdf/conf-policy.pdf')),
                  path('user-agreement', RedirectView.as_view(url='/static/pdf/user-agreement.pdf')),
                  path('terms', RedirectView.as_view(url='/static/pdf/terms.pdf')),
              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + \
              static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

social_web_auth = [
    path('auth/socials/', include('social_django.urls', namespace="social")),
    path('auth/socials/logout', auth_views.LogoutView.as_view(), name="web-logout"),
    path('auth/socials/login', login, name="login"),
    path('auth/socials/web', social_web_auth, name="web"),
]

v1_0 = [
    path('v1.0/', include(('app_bot.urls', 'bot_1_0'))),
    path('v1.0/', include(('app_users.urls', 'users_1_0'))),
]

urlpatterns += doc_urls
urlpatterns += social_web_auth

urlpatterns += v1_0
