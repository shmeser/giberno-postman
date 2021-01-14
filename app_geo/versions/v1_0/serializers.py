from django.contrib.contenttypes.models import ContentType
from django.db.models import Prefetch
from django_globals import globals as g
from rest_framework import serializers

from app_geo.models import Language, Country, City, Region
from app_geo.versions.v1_0.repositories import LanguagesRepository, RegionsRepository
from app_media.enums import MediaType, MediaFormat, MimeTypes
from app_media.models import MediaModel
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.platform = g.request.headers.get('Platform', '').lower()
        self.mime_type = MimeTypes.PNG.value if Platform.IOS.value in self.platform else MimeTypes.SVG.value

    name = serializers.SerializerMethodField()
    flag = serializers.SerializerMethodField()

    def fast_related_loading(self, queryset):
        country_ct = ContentType.objects.get_for_model(Country).id
        queryset = queryset.prefetch_related(
            Prefetch(
                'media',
                queryset=MediaModel.objects.filter(
                    owner_ct_id=country_ct,
                    type=MediaType.FLAG.value,
                    format=MediaFormat.IMAGE.value,
                    mime_type=self.mime_type
                ).order_by('-created_at'),
                to_attr='medias'  # Подгружаем флаги в поле medias
            )
        )

        return queryset

    def get_name(self, country: Country):
        # TODO для локализации выводить соответствующее название
        return country.names.get('name:ru', None)

    def get_flag(self, country: Country):
        # Берем флаг из поля medias
        if hasattr(country, 'medias') and country.medias:
            return MediaSerializer(country.medias[0], many=False).data
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


class CountryLightSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, country: Country):
        # TODO для локализации выводить соответствующее название
        return country.names.get('name:ru', None)

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


class RegionSerializer(serializers.ModelSerializer):
    repository = RegionsRepository

    name = serializers.SerializerMethodField(read_only=True)

    def get_name(self, region: Region):
        # TODO для локализации выводить соответствующее название
        return region.names.get('name:ru', None)

    class Meta:
        model = Region
        fields = [
            'id',
            'name',
            'native',
        ]


class CitySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField(read_only=True)
    region = serializers.SerializerMethodField(read_only=True)

    @classmethod
    def fast_related_loading(cls, queryset):
        queryset = queryset.select_related('country', 'region')
        return queryset

    def get_name(self, city: City):
        # TODO для локализации выводить соответствующее название
        return city.names.get('name:ru', None)

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
            'country',
            'region',
        ]
