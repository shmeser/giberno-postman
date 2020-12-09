from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.views.generic import RedirectView

from app_users.versions.v1_0.views import AuthVk, social_web_auth, login
from giberno import settings
from giberno.yasg import urlpatterns as doc_urls

urlpatterns = [
                  path('django/admin', admin.site.urls),
                  path('policy', RedirectView.as_view(url='/static/pdf/conf-policy.pdf')),
                  path('user-agreement', RedirectView.as_view(url='/static/pdf/user-agreement.pdf')),
                  path('terms', RedirectView.as_view(url='/static/pdf/terms.pdf')),
              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + \
              static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += doc_urls

v1_0 = [
    path('v1.0/', include(('app_bot.urls', 'app_bot'), namespace='bot_1_0')),
    path('v1.0/', include(('app_users.urls', 'app_users'), namespace='users_1_0')),
    path('v1.0/auth/socials/', include('social_django.urls', namespace="social")),
    path('v1.0/auth/socials/web', social_web_auth, name="web"),
    path('v1.0/auth/socials/login', login, name="login"),
    path('v1.0/auth/socials/logout', auth_views.LogoutView.as_view(), name="web-logout"),
    path('v1.0/auth/socials/vk', AuthVk.as_view()),
]

urlpatterns += v1_0
