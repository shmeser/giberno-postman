import pytz
from django.contrib.gis.db import models
from django.contrib.postgres.fields import HStoreField

from backend.models import BaseModel
from giberno import settings


class Language(BaseModel):
    name = models.CharField(max_length=1024, null=True, blank=True)
    native = models.CharField(max_length=1024, null=True, blank=True)
    iso_code = models.CharField(max_length=4, null=True, blank=True, unique=True)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        db_table = 'app_geo__languages'
        verbose_name = 'Язык'
        verbose_name_plural = 'Языки'


class Country(BaseModel):
    name = models.CharField(max_length=1024, null=True, blank=True)
    names = HStoreField(null=True, blank=True)
    iso_code = models.CharField(max_length=8, null=True, blank=True, unique=True)

    osm = HStoreField(null=True, blank=True)

    boundary = models.MultiPolygonField(srid=settings.SRID, blank=True, null=True)

    languages = models.ManyToManyField(Language, blank=True, db_table='app_geo__country_language')

    def __str__(self):
        return f'{self.names.get("name:en", "")} - {self.name}'

    class Meta:
        db_table = 'app_geo__countries'
        verbose_name = 'Страна'
        verbose_name_plural = 'Страны'


class Region(BaseModel):
    name = models.CharField(max_length=1024, null=True, blank=True)
    names = HStoreField(null=True, blank=True)

    osm = HStoreField(null=True, blank=True)

    country = models.ForeignKey(Country, blank=True, null=True, on_delete=models.SET_NULL)

    boundary = models.MultiPolygonField(srid=settings.SRID, blank=True, null=True)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        db_table = 'app_geo__regions'
        verbose_name = 'Регион'
        verbose_name_plural = 'Регионы'


class District(BaseModel):
    name = models.CharField(max_length=1024, null=True, blank=True)
    names = HStoreField(null=True, blank=True)

    osm = HStoreField(null=True, blank=True)

    country = models.ForeignKey(Country, blank=True, null=True, on_delete=models.SET_NULL)
    region = models.ForeignKey(Region, blank=True, null=True, on_delete=models.SET_NULL)

    boundary = models.MultiPolygonField(srid=settings.SRID, blank=True, null=True)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        db_table = 'app_geo__districts'
        verbose_name = 'Район'
        verbose_name_plural = 'Районы'


class City(BaseModel):
    name = models.CharField(max_length=1024, null=True, blank=True)
    names = HStoreField(null=True, blank=True)

    osm = HStoreField(null=True, blank=True)

    country = models.ForeignKey(Country, blank=True, null=True, on_delete=models.SET_NULL)
    region = models.ForeignKey(Region, blank=True, null=True, on_delete=models.SET_NULL)
    district = models.ForeignKey(District, blank=True, null=True, on_delete=models.SET_NULL)

    boundary = models.MultiPolygonField(srid=settings.SRID, blank=True, null=True)
    position = models.PointField(srid=settings.SRID, blank=True, null=True)
    timezone = models.CharField(max_length=512, default='UTC', choices=[(tz, tz) for tz in pytz.common_timezones])

    def __str__(self):
        return f'{self.name}'

    class Meta:
        db_table = 'app_geo__cities'
        verbose_name = 'Город'
        verbose_name_plural = 'Города'
