from rest_framework import serializers

from app_geo.models import Language, Country, City, Region
from app_geo.versions.v1_0.repositories import LanguagesRepository, RegionsRepository
from app_media.enums import MediaType, MediaFormat
from app_media.versions.v1_0.repositories import MediaRepository
from app_media.versions.v1_0.serializers import MediaSerializer
from backend.mixins import CRUDSerializer

DEFAULT_LANGUAGE = 'name:ru'


class LanguageSerializer(CRUDSerializer):
    repository = LanguagesRepository
    name = serializers.SerializerMethodField()
    proficiency = serializers.SerializerMethodField()

    def get_proficiency(self, language: Language):
        user_language = language.userlanguage_set.filter(user=self.me).first()
        if user_language:
            return user_language.proficiency
        return None

    def get_name(self, language: Language):
        user_language = DEFAULT_LANGUAGE
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


class CountrySerializer(CRUDSerializer):
    name = serializers.SerializerMethodField()
    flag = serializers.SerializerMethodField()

    def get_name(self, country: Country):
        # TODO для локализации выводить соответствующее название
        return country.names.get(DEFAULT_LANGUAGE, None)

    def get_flag(self, prefetched_data):
        file = MediaRepository.get_related_media_file(
            self.instance, prefetched_data, MediaType.FLAG.value, MediaFormat.IMAGE.value, mime_type=self.mime_type
        )

        if file:
            return MediaSerializer(file, many=False).data
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


class CountryLightSerializer(CRUDSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, country: Country):
        # TODO для локализации выводить соответствующее название
        return country.names.get(DEFAULT_LANGUAGE, None)

    class Meta:
        model = Country
        fields = [
            'id',
            'iso_code',
            'name',
            'native',
        ]

        extra_kwargs = {
            'iso_code': {'read_only': True},
        }


class RegionSerializer(CRUDSerializer):
    repository = RegionsRepository

    name = serializers.SerializerMethodField(read_only=True)

    def get_name(self, region: Region):
        # TODO для локализации выводить соответствующее название
        return region.names.get(DEFAULT_LANGUAGE, None)

    class Meta:
        model = Region
        fields = [
            'id',
            'name',
            'native',
        ]


class CitySerializer(CRUDSerializer):
    name = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField(read_only=True)
    region = serializers.SerializerMethodField(read_only=True)
    lon = serializers.SerializerMethodField()
    lat = serializers.SerializerMethodField()

    def get_lon(self, city: City):
        return city.position.x if city.position else None

    def get_lat(self, city: City):
        return city.position.y if city.position else None

    def get_name(self, city: City):
        # TODO для локализации выводить соответствующее название
        return city.names.get(DEFAULT_LANGUAGE, None)

    def get_country(self, city: City):
        if city.country:
            return CountryLightSerializer(city.country, many=False).data
        return None

    def get_region(self, city: City):
        if city.region:
            return RegionSerializer(city.region, many=False).data
        return None

    class Meta:
        model = City
        fields = [
            'id',
            'name',
            'native',
            'lon',
            'lat',
            'country',
            'region',
        ]
