from django.urls import path

from app_market.views import Vacancies

urlpatterns = [
    path('market/vacancies', Vacancies.as_view()),
]
