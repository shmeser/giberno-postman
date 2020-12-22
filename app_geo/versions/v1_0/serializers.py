from django.contrib.contenttypes.models import ContentType
from django_globals import globals as g
from rest_framework import serializers

from app_geo.models import Language, Country
from app_geo.versions.v1_0.repositories import LanguagesRepository, CountriesRepository
from app_media.enums import MediaType, MediaFormat
from app_media.versions.v1_0.repositories import MediaRepository
from app_media.versions.v1_0.serializers import MediaSerializer
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

    name = serializers.SerializerMethodField(read_only=True)
    native = serializers.SerializerMethodField(read_only=True)
    flag = serializers.SerializerMethodField(read_only=True)

    def get_name(self, country: Country):
        # TODO для локализации выводить соответствующее название
        return country.names.get('name:ru', None)

    def get_native(self, country: Country):
        return country.name

    def get_flag(self, country: Country):
        flag_file = MediaRepository().filter_by_kwargs({
            'owner_id': country.id,
            'owner_content_type_id': ContentType.objects.get_for_model(country).id,
            'type__in': [
                MediaType.FLAG.value,
            ],
            'format__in': [
                MediaFormat.IMAGE.value
            ]
        }, order_by=['-created_at']).first()
        if flag_file:
            return MediaSerializer(flag_file, many=False).data
        return None

    class Meta:
        model = Country
        fields = [
            'id',
            'iso_code',
            'name',
            'native',
            'flag'
        ]

        extra_kwargs = {
            'iso_code': {'read_only': True},
        }
