from django.contrib.contenttypes.models import ContentType
from django.db.models import Prefetch

from app_geo.models import Language, Country, City, Region
from app_media.enums import MediaType, MediaFormat, MimeTypes
from app_media.models import MediaModel
from backend.errors.enums import RESTErrors
from backend.errors.http_exception import HttpException
from backend.mixins import MasterRepository


class LanguagesRepository(MasterRepository):
    model = Language

    def get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден'
            )


class CountriesRepository(MasterRepository):
    model = Country

    def get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден'
            )

    @staticmethod
    def fast_related_loading(queryset, mime_type=MimeTypes.SVG.value):
        country_ct = ContentType.objects.get_for_model(Country).id
        queryset = queryset.prefetch_related(
            Prefetch(
                'media',
                queryset=MediaModel.objects.filter(
                    owner_ct_id=country_ct,
                    type=MediaType.FLAG.value,
                    format=MediaFormat.IMAGE.value,
                    mime_type=mime_type
                ).order_by('-created_at'),
                to_attr='medias'  # Подгружаем флаги в поле medias
            )
        )

        return queryset


class RegionsRepository(MasterRepository):
    model = Region

    def get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден'
            )


class CitiesRepository(MasterRepository):
    model = City

    def get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден'
            )

    def geocode(self, point):
        return self.model.objects.filter(boundary__covers=point)

    @staticmethod
    def fast_related_loading(queryset):
        queryset = queryset.select_related('country', 'region')
        return queryset
