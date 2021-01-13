from app_market.models import Vacancy
from app_market.versions.v1_0.repositories import VacanciesRepository
from backend.mixins import CRUDSerializer


class VacancySerializer(CRUDSerializer):
    repository = VacanciesRepository

    class Meta:
        model = Vacancy
        fields = [
            'id',
            'title',
            'description',
            'features',
            'price'
        ]
