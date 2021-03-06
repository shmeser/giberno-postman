from celery import group
from django.contrib.gis import admin

from app_geo.models import Country, City, Region, District
from backend.mixins import FormattedAdmin
from backend.tasks import countries_update_flag, countries_add_png_flag_from_svg
from backend.utils import chunks

_ITEMS_PER_ITERATION = 5


@admin.register(Country)
class CountryAdmin(FormattedAdmin):
    list_display = ['id', 'iso_code', 'native', 'names']
    raw_id_fields = ['languages']
    actions = ["update_flags", "add_png_flags"]

    def update_flags(self, request, queryset):
        countries_ids_chunked = chunks(queryset.values_list('id', flat=True), _ITEMS_PER_ITERATION)

        jobs = group(
            [countries_update_flag.s(countries_ids) for countries_ids in countries_ids_chunked])
        jobs.apply_async()

        self.message_user(request, f"{len(queryset)} Стран поставлены в очередь на обновление флагов")

    def add_png_flags(self, request, queryset):
        countries_ids_chunked = chunks(queryset.values_list('id', flat=True), _ITEMS_PER_ITERATION)

        jobs = group(
            [countries_add_png_flag_from_svg.s(countries_ids) for countries_ids in countries_ids_chunked])
        jobs.apply_async()

        self.message_user(request, f"{len(queryset)} Стран поставлены в очередь на обновление флагов")


@admin.register(Region)
class RegionAdmin(FormattedAdmin):
    list_display = ['id', 'native', 'names', 'osm']
    list_filter = ["country_id"]


@admin.register(District)
class DistrictAdmin(FormattedAdmin):
    list_display = ['id', 'native', 'names', 'osm']
    actions = ["parse_district", "get_border"]
    list_filter = ["country_id", 'region_id']


@admin.register(City)
class CityAdmin(FormattedAdmin):
    list_display = ['id', 'native', 'names', 'osm']
    actions = ["get_border"]
    list_filter = ["country_id", 'region_id']
