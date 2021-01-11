from django.contrib.contenttypes.models import ContentType
from django_globals import globals as g
from rest_framework import serializers

from app_geo.models import Language, Country, City, Region
from app_geo.versions.v1_0.repositories import LanguagesRepository, CountriesRepository, RegionsRepository
from app_media.enums import MediaType, MediaFormat, MimeTypes
from app_media.versions.v1_0.repositories import MediaRepository
from app_media.versions.v1_0.serializers import MediaSerializer
from backend.enums import Platform
from backend.mixins import CRUDSerializer


class LanguageSerializer(CRUDSerializer):
    repository = LanguagesRepository
    name = serializers.SerializerMethodField()
    proficiency = serializers.SerializerMethodField()

    def get_proficiency(self, language: Language):
        user_language = language.userlanguage_set.filter(user=g.request.user).first()
        if user_language:
            return user_language.proficiency
        return None

    def get_name(self, language: Language):
        user_language = 'name:ru'
        if language.names.get(user_language, None):
            return language.names[user_language]
        return language.name

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
        platform = g.request.headers.get('Platform', '').lower()
        mime_type = MimeTypes.PNG.value if Platform.IOS.value in platform else MimeTypes.SVG.value

        flag_file = MediaRepository().filter_by_kwargs({
            'owner_id': country.id,
            'owner_content_type_id': ContentType.objects.get_for_model(country).id,
            'type__in': [
                MediaType.FLAG.value,
            ],
            'format__in': [
                MediaFormat.IMAGE.value
            ],
            'mime_type': mime_type
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


class RegionSerializer(serializers.ModelSerializer):
    repository = RegionsRepository

    name = serializers.SerializerMethodField(read_only=True)
    native = serializers.SerializerMethodField(read_only=True)

    def get_name(self, region: Region):
        # TODO для локализации выводить соответствующее название
        return region.names.get('name:ru', None)

    def get_native(self, region: Region):
        return region.name

    class Meta:
        model = Region
        fields = [
            'id',
            'name',
            'native',
        ]


class CitySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    native = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField(read_only=True)
    region = serializers.SerializerMethodField(read_only=True)

    def get_name(self, city: City):
        # TODO для локализации выводить соответствующее название
        return city.names.get('name:ru', None)

    def get_native(self, city: City):
        return city.name

    def get_country(self, city: City):
        return CountrySerializer(city.country, many=False).data

    def get_region(self, city: City):
        return RegionSerializer(city.region, many=False).data

    class Meta:
        model = City
        fields = [
            'id',
            'name',
            'native',
            'country',
            'region',
        ]
