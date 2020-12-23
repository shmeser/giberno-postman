from celery import group
from django.contrib.gis import admin
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField, JSONField, HStoreField
from django.db.models import UUIDField
from django.forms import TextInput, Textarea

from app_geo.models import Country, City
from backend.tasks import countries_update_flag, countries_update_flag_png
from backend.utils import chunks


class FormattedAdmin(admin.OSMGeoAdmin):
    formfield_overrides = {
        ArrayField: {'widget': TextInput(attrs={'size': '150'})},
        models.CharField: {'widget': TextInput(attrs={'size': '150'})},
        UUIDField: {'widget': TextInput(attrs={'size': '150'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 10, 'cols': 150})},
        JSONField: {'widget': Textarea(attrs={'rows': 10, 'cols': 150})},
        HStoreField: {'widget': Textarea(attrs={'rows': 10, 'cols': 150})},
    }


@admin.register(Country)
class CountryAdmin(FormattedAdmin):
    fields = ['name', 'names', 'iso_code', 'osm', 'boundary', 'languages']
    raw_id_fields = ['languages']
    actions = ["update_flags", "update_flags_png"]

    def update_flags(self, request, queryset):
        _COUNTRIES_PER_REQUEST = 5

        countries_ids_chunked = chunks(queryset.values_list('id', flat=True), _COUNTRIES_PER_REQUEST)
        print('@@@countries COUNT', queryset.count())
        print('@@@countries_ids_chunks count', len(countries_ids_chunked))

        jobs = group(
            [countries_update_flag.s(countries_ids) for countries_ids in countries_ids_chunked])
        jobs.apply_async()

        self.message_user(request, f"{len(queryset)} Стран поставлены в очередь на обновление флагов")

    def update_flags_png(self, request, queryset):
        _COUNTRIES_PER_REQUEST = 5

        countries_ids_chunked = chunks(queryset.values_list('id', flat=True), _COUNTRIES_PER_REQUEST)
        print('@@@countries COUNT', queryset.count())
        print('@@@countries_ids_chunks count', len(countries_ids_chunked))

        jobs = group(
            [countries_update_flag_png.s(countries_ids) for countries_ids in countries_ids_chunked])
        jobs.apply_async()

        self.message_user(request, f"{len(queryset)} Стран поставлены в очередь на обновление флагов")


@admin.register(City)
class CityAdmin(FormattedAdmin):
    fields = ['name', 'names', 'iso_code', 'osm']
