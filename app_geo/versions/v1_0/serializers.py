from django_globals import globals as g
from rest_framework import serializers

from app_geo.models import Language, Country
from app_geo.versions.v1_0.repositories import LanguagesRepository, CountriesRepository
from backend.mixins import CRUDSerializer


class LanguageSerializer(CRUDSerializer):
    repository = LanguagesRepository
    proficiency = serializers.SerializerMethodField()

    def get_proficiency(self, language: Language):
        user_language = language.userlanguage_set.filter(user=g.request.user).first()
        if user_language:
            return user_language.proficiency
        return None

    class Meta:
        model = Language
        fields = [
            'id',
            'iso_code',
            'name',
            'native',
            'proficiency'
        ]

        extra_kwargs = {
            'iso_code': {'read_only': True},
            'name': {'read_only': True},
            'native': {'read_only': True}
        }


class CountrySerializer(serializers.ModelSerializer):
    repository = CountriesRepository

    class Meta:
        model = Country
        fields = [
            'id',
            'iso_code',
            'name',
        ]

        extra_kwargs = {
            'iso_code': {'read_only': True},
            'name': {'read_only': True},
        }
