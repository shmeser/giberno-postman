from app_market.models import Vacancy, Profession, Skill
from app_market.versions.v1_0.repositories import VacanciesRepository, ProfessionsRepository, SkillsRepository
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


class SkillSerializer(CRUDSerializer):
    repository = SkillsRepository

    class Meta:
        model = Skill
        fields = [
            'id',
            'name',
            'description',
        ]
