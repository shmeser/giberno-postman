from django.contrib.gis import admin

from app_games.models import Prize
from backend.mixins import FormattedAdmin

_ITEMS_PER_ITERATION = 5


@admin.register(Prize)
class PrizeAdmin(FormattedAdmin):
    list_display = ['id', 'name', 'price']
