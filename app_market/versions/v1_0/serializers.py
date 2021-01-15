from app_market.models import Vacancy, Profession
from app_market.versions.v1_0.repositories import VacanciesRepository, ProfessionsRepository
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


class ProfessionSerializer(CRUDSerializer):
    repository = ProfessionsRepository

    class Meta:
        model = Profession
        fields = [
            'id',
            'name',
            'description',
        ]
