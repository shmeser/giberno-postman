from django.urls import path

from app_geo.views import Languages

urlpatterns = [
    path('geo/languages', Languages.as_view()),
    path('geo/languages/<int:record_id>', Languages.as_view()),
]
