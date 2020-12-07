from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

from giberno import settings
from giberno.yasg import urlpatterns as doc_urls

urlpatterns = [
                  path('django/admin', admin.site.urls),
                  path('policy', RedirectView.as_view(url='/static/pdf/conf-policy.pdf')),
                  path('user-agreement', RedirectView.as_view(url='/static/pdf/user-agreement.pdf')),
                  path('terms', RedirectView.as_view(url='/static/pdf/terms.pdf')),

                  path('api/', include(('bot.urls', 'bot'), namespace='bot')),
              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + \
              static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += doc_urls
