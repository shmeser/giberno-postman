from django.urls import path

from app_geo.views import Languages, Countries

urlpatterns = [
    path('geo/languages', Languages.as_view()),
    path('geo/languages/<int:record_id>', Languages.as_view()),

    path('geo/countries', Countries.as_view()),
    path('geo/countries/<int:record_id>', Countries.as_view()),
]
