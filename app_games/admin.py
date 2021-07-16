from django.contrib.gis import admin

from app_games.models import Prize, UserTask, Task, UserPrizeProgress, UserFavouritePrize, PrizeCardsHistory, PrizeCard, \
    GoodsCategory
from backend.mixins import FormattedAdmin

_ITEMS_PER_ITERATION = 5


@admin.register(GoodsCategory)
class GoodsCategoryAdmin(FormattedAdmin):
    list_display = ['id', 'title', 'description']


@admin.register(Prize)
class PrizeAdmin(FormattedAdmin):
    list_display = ['id', 'name', 'price', 'real_price', 'grade']


@admin.register(PrizeCard)
class PrizeCardAdmin(FormattedAdmin):
    list_display = ['id', 'prize', 'value']


@admin.register(PrizeCardsHistory)
class PrizeCardsHistoryAdmin(FormattedAdmin):
    list_display = ['id', 'card', 'user', 'bonuses_acquired']


@admin.register(UserFavouritePrize)
class UserFavouritePrizeAdmin(FormattedAdmin):
    list_display = ['id', 'user', 'prize']


@admin.register(UserPrizeProgress)
class UserPrizeProgressAdmin(FormattedAdmin):
    list_display = ['id', 'user', 'prize', 'value', 'completed_at']


@admin.register(Task)
class TaskAdmin(FormattedAdmin):
    list_display = ['id', 'name', 'description', 'bonus_value', 'period', 'type']


@admin.register(UserTask)
class UserTaskAdmin(FormattedAdmin):
    list_display = ['id', 'user', 'task']
