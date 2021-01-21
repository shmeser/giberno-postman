from rest_framework import serializers

from app_market.models import Vacancy, Profession, Skill, Distributor, Shop
from app_market.versions.v1_0.repositories import VacanciesRepository, ProfessionsRepository, SkillsRepository, \
    DistributorsRepository, ShopsRepository
from backend.mixins import CRUDSerializer


class DistributorSerializer(CRUDSerializer):
    repository = DistributorsRepository

    categories = serializers.SerializerMethodField()

    def get_categories(self, instance):
        return []

    class Meta:
        model = Distributor
        fields = [
            'id',
            'title',
            'description',
            'categories',
        ]


class ShopSerializer(CRUDSerializer):
    repository = ShopsRepository

    distributor = serializers.SerializerMethodField()

    def get_distributor(self, instance):
        return None

    class Meta:
        model = Shop
        fields = [
            'id',
            'title',
            'description',
            'location',
            'address',
            'distributor',
        ]


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
