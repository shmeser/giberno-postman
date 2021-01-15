from django.contrib.gis import admin
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField, JSONField, HStoreField
from django.db.models import UUIDField
from django.forms import TextInput, Textarea

from app_market.models import Distributor, Shop, Vacancy, Shift, UserShift, Order, Transaction, Coupon, Profession, \
    UserProfession


class FormattedAdmin(admin.OSMGeoAdmin):
    formfield_overrides = {
        ArrayField: {'widget': TextInput(attrs={'size': '150'})},
        models.CharField: {'widget': TextInput(attrs={'size': '150'})},
        UUIDField: {'widget': TextInput(attrs={'size': '150'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 10, 'cols': 150})},
        JSONField: {'widget': Textarea(attrs={'rows': 10, 'cols': 150})},
        HStoreField: {'widget': Textarea(attrs={'rows': 10, 'cols': 150})},
    }


_ITEMS_PER_ITERATION = 5


@admin.register(Distributor)
class DistributorAdmin(FormattedAdmin):
    list_display = ['id', 'title', 'category', 'description', 'required_docs']


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
    raw_id_fields = ['shop']


@admin.register(Shift)
class ShiftAdmin(FormattedAdmin):
    list_display = [
        'id', 'price', 'currency', 'employees_count', 'max_employees_count', 'time_start', 'time_end',
        'date_start', 'date_end', 'frequency'
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
