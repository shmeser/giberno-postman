from django.contrib.gis import admin

from app_market.models import Distributor, Shop, Vacancy, Shift, UserShift, Order, Transaction, Coupon, Profession, \
    UserProfession, DistributorCategory, Category, ShiftAppeal
from backend.mixins import FormattedAdmin

_ITEMS_PER_ITERATION = 5


@admin.register(Distributor)
class DistributorAdmin(FormattedAdmin):
    list_display = ['id', 'title', 'description', 'required_docs']


@admin.register(Shop)
class ShopAdmin(FormattedAdmin):
    list_display = ['id', 'title', 'description', 'is_partner', 'discount', 'address']
    list_filter = ["is_partner"]
    raw_id_fields = ['distributor']


@admin.register(Vacancy)
class VacancyAdmin(FormattedAdmin):
    list_display = [
        'id', 'title', 'description', 'requirements', 'required_experience', 'required_docs', 'features', 'price',
        'currency', 'radius'
    ]

    readonly_fields = ['required_docs']
    raw_id_fields = ['shop']


@admin.register(ShiftAppeal)
class VacancyAppealAdmin(FormattedAdmin):
    list_display = ['id', 'applier', 'shift', 'status']


@admin.register(Shift)
class ShiftAdmin(FormattedAdmin):
    list_display = [
        'id', 'vacancy', 'vacancy_id', 'shop_id', 'price', 'currency', 'employees_count', 'max_employees_count',
        'time_start', 'time_end', 'date_start', 'date_end', 'frequency'
    ]
    raw_id_fields = ['vacancy', 'shop']


@admin.register(UserShift)
class UserShiftAdmin(FormattedAdmin):
    list_display = ['id', 'real_time_start', 'real_time_end', 'qr_code', 'qr_code_gen_at']
    list_filter = ["status"]
    raw_id_fields = ['user', 'shift']


@admin.register(Coupon)
class CouponAdmin(FormattedAdmin):
    list_display = ['id', 'code', 'date', 'discount_amount', 'discount_terms', 'discount_description']
    raw_id_fields = ['user', 'shop', 'distributor']


@admin.register(Order)
class OrderAdmin(FormattedAdmin):
    list_display = ['id', 'email', 'description', 'terms_accepted']
    raw_id_fields = ['user', 'coupon', 'transaction']


@admin.register(Transaction)
class TransactionAdmin(FormattedAdmin):
    list_display = [
        'id', 'amount', 'exchange_rate', 'type', 'status', 'uuid', 'from_id', 'from_content_type', 'to_id',
        'to_content_type', 'comment'
    ]


@admin.register(Profession)
class ProfessionAdmin(FormattedAdmin):
    list_display = [
        'id', 'name', 'description', 'is_suggested', 'approved_at', 'created_at', 'updated_at',
    ]
    list_filter = ["is_suggested"]


@admin.register(UserProfession)
class UserProfessionAdmin(FormattedAdmin):
    raw_id_fields = ['user', 'profession']


@admin.register(Category)
class CategoryAdmin(FormattedAdmin):
    list_display = [
        'id', 'title', 'description'
    ]


@admin.register(DistributorCategory)
class DistributorCategoryAdmin(FormattedAdmin):
    raw_id_fields = ['distributor', 'category']
