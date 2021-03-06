import pytz
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.gis.db import models
from django.contrib.postgres.fields import HStoreField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField

from app_media.models import MediaModel
from backend.models import BaseModel
from giberno import settings


# TODO добавить GIN индексы для FTS


class Language(BaseModel):
    name = models.CharField(max_length=1024, null=True, blank=True)
    names = HStoreField(null=True, blank=True)
    native = models.CharField(max_length=1024, null=True, blank=True)
    iso_code = models.CharField(max_length=4, null=True, blank=True, unique=True)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        db_table = 'app_geo__languages'
        verbose_name = 'Язык'
        verbose_name_plural = 'Языки'


class Country(BaseModel):
    native = models.CharField(max_length=1024, null=True, blank=True)
    names = HStoreField(null=True, blank=True)
    iso_code = models.CharField(max_length=8, null=True, blank=True, unique=True)

    osm = HStoreField(null=True, blank=True)

    boundary = models.MultiPolygonField(srid=settings.SRID, blank=True, null=True)

    languages = models.ManyToManyField(Language, blank=True, db_table='app_geo__country_language')

    media = GenericRelation(MediaModel, object_id_field='owner_id', content_type_field='owner_ct')

    def __str__(self):
        return f'{self.names.get("name:en", "")} - {self.native}'

    class Meta:
        db_table = 'app_geo__countries'
        verbose_name = 'Страна'
        verbose_name_plural = 'Страны'


class Region(BaseModel):
    native = models.CharField(max_length=1024, null=True, blank=True)
    names = HStoreField(null=True, blank=True)

    osm = HStoreField(null=True, blank=True)

    country = models.ForeignKey(Country, blank=True, null=True, on_delete=models.SET_NULL)

    boundary = models.MultiPolygonField(srid=settings.SRID, blank=True, null=True)

    def __str__(self):
        return f'{self.native}'

    class Meta:
        db_table = 'app_geo__regions'
        verbose_name = 'Регион'
        verbose_name_plural = 'Регионы'


class District(BaseModel):
    native = models.CharField(max_length=1024, null=True, blank=True)
    names = HStoreField(null=True, blank=True)

    osm = HStoreField(null=True, blank=True)

    country = models.ForeignKey(Country, blank=True, null=True, on_delete=models.SET_NULL)
    region = models.ForeignKey(Region, blank=True, null=True, on_delete=models.SET_NULL)

    boundary = models.MultiPolygonField(srid=settings.SRID, blank=True, null=True)

    def __str__(self):
        return f'{self.native}'

    class Meta:
        db_table = 'app_geo__districts'
        verbose_name = 'Район'
        verbose_name_plural = 'Районы'


class City(BaseModel):
    native = models.CharField(max_length=1024, null=True, blank=True)
    names = HStoreField(null=True, blank=True)

    osm = HStoreField(null=True, blank=True)

    country = models.ForeignKey(Country, blank=True, null=True, on_delete=models.SET_NULL)
    region = models.ForeignKey(Region, blank=True, null=True, on_delete=models.SET_NULL)
    district = models.ForeignKey(District, blank=True, null=True, on_delete=models.SET_NULL)

    boundary = models.MultiPolygonField(srid=settings.SRID, blank=True, null=True)
    position = models.PointField(srid=settings.SRID, blank=True, null=True)
    population = models.PositiveIntegerField(blank=True, null=True)
    timezone = models.CharField(
        max_length=512, null=True, blank=True, default='UTC', choices=[(tz, tz) for tz in pytz.common_timezones]
    )

    names_tsv = SearchVectorField(null=True)

    native_tsv = SearchVectorField(null=True)

    def __str__(self):
        return f'{self.native}'

    class Meta:
        db_table = 'app_geo__cities'
        verbose_name = 'Город'
        verbose_name_plural = 'Города'

        indexes = [
            GinIndex(
                name="app_geo__cities__native_tsv",
                fields=("native_tsv",),
            ),
            GinIndex(
                name="app_geo__cities__names_tsv",
                fields=("names_tsv",),
            ),
            GinIndex(
                name="app_geo__cities__native",
                fields=("native",),
                opclasses=("gin_trgm_ops",)
            ),
        ]
