from django.urls import path

from app_geo.views import Languages, Countries, Cities, custom_languages, custom_countries

urlpatterns = [
    path('geo/languages', Languages.as_view()),
    path('geo/languages/<int:record_id>', Languages.as_view()),
    path('geo/languages/custom', custom_languages),

    path('geo/countries', Countries.as_view()),
    path('geo/countries/<int:record_id>', Countries.as_view()),
    path('geo/countries/custom', custom_countries),

    path('geo/cities', Cities.as_view()),
    path('geo/cities/<int:record_id>', Cities.as_view()),
]
