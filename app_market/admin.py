from django.contrib.gis import admin

from app_market.models import Distributor, Shop, Vacancy, Shift, Order, Transaction, Coupon, Profession, \
    UserProfession, DistributorCategory, Category, ShiftAppeal, Partner, Achievement, AchievementProgress, \
    Advertisement, UserCode, Code, ShiftAppealInsurance, Skill, UserSkill, Structure, DistributorStructure, Organization
from backend.mixins import FormattedAdmin

_ITEMS_PER_ITERATION = 5


@admin.register(Distributor)
class DistributorAdmin(FormattedAdmin):
    list_display = ['id', 'title', 'description', 'required_docs']


@admin.register(Organization)
class OrganizationAdmin(FormattedAdmin):
    list_display = ['id', 'title', 'short_name', 'full_name']


@admin.register(Partner)
class PartnerAdmin(FormattedAdmin):
    list_display = ['id', 'distributor']
    raw_id_fields = ['distributor']


@admin.register(Shop)
class ShopAdmin(FormattedAdmin):
    list_display = ['id', 'title', 'description', 'address']
    raw_id_fields = ['distributor', 'city']


@admin.register(Vacancy)
class VacancyAdmin(FormattedAdmin):
    list_display = [
        'id', 'title', 'description', 'requirements', 'required_experience', 'required_docs', 'features', 'price',
        'currency', 'radius'
    ]

    readonly_fields = ['required_docs']
    raw_id_fields = ['shop']


@admin.register(ShiftAppeal)
class ShiftAppealAdmin(FormattedAdmin):
    list_display = ['id', 'applier', 'shift', 'status', 'job_status', 'time_start', 'time_end', 'security_qr_scan_time',
                    'manager_qr_scan_time', 'started_real_time', 'completed_real_time']


@admin.register(Shift)
class ShiftAdmin(FormattedAdmin):
    list_display = [
        'id', 'vacancy', 'vacancy_id', 'shop_id', 'price', 'currency', 'max_employees_count', 'min_employee_rating',
        'auto_control_threshold_minutes', 'time_start', 'time_end', 'date_start', 'date_end', 'frequency'
    ]
    raw_id_fields = ['vacancy', 'shop']


@admin.register(Coupon)
class CouponAdmin(FormattedAdmin):
    list_display = [
        'id',
        'description',
        'bonus_price',
        'discount',
        'discount_terms',
        'service_description'
    ]
    raw_id_fields = ['partner', ]


@admin.register(Code)
class CodeAdmin(FormattedAdmin):
    list_display = [
        'id',
        'value',
        'coupon_id'
    ]
    raw_id_fields = ['coupon', ]


@admin.register(UserCode)
class UserCodeAdmin(FormattedAdmin):
    list_display = [
        'id',
        'code_id',
        'activated_at',
        'order_id'
    ]
    raw_id_fields = ['code', 'order']


@admin.register(Order)
class OrderAdmin(FormattedAdmin):
    list_display = ['id', 'email', 'description', 'terms_accepted']
    raw_id_fields = ['user', ]


@admin.register(Transaction)
class TransactionAdmin(FormattedAdmin):
    list_display = [
        'id',
        'amount',
        'exchange_rate',
        'type',
        'status',
        'uuid',
        'comment'
    ]


@admin.register(Profession)
class ProfessionAdmin(FormattedAdmin):
    list_display = [
        'id', 'name', 'description', 'suggested_by', 'approved_at', 'created_at', 'updated_at',
    ]
    list_filter = []


@admin.register(UserProfession)
class UserProfessionAdmin(FormattedAdmin):
    raw_id_fields = ['user', 'profession']


@admin.register(Category)
class CategoryAdmin(FormattedAdmin):
    list_display = [
        'id', 'title', 'description'
    ]


@admin.register(Structure)
class StructureAdmin(FormattedAdmin):
    list_display = [
        'id', 'title', 'description'
    ]


@admin.register(DistributorStructure)
class DistributorStructureAdmin(FormattedAdmin):
    raw_id_fields = ['distributor', 'structure']


@admin.register(DistributorCategory)
class DistributorCategoryAdmin(FormattedAdmin):
    raw_id_fields = ['distributor', 'category']


@admin.register(Achievement)
class AchievementAdmin(FormattedAdmin):
    list_display = [
        'id', 'name', 'description', 'actions_min_count', 'type'
    ]

    list_filter = ["type"]


@admin.register(AchievementProgress)
class AchievementProgressAdmin(FormattedAdmin):
    list_display = [
        'id', 'achievement_id', 'actions_min_count', 'achieved_count', 'completed_at'
    ]

    raw_id_fields = ['user', 'achievement']


@admin.register(Advertisement)
class AdvertisementAdmin(FormattedAdmin):
    list_display = [
        'id', 'title', 'description'
    ]


@admin.register(ShiftAppealInsurance)
class ShiftAppealInsuranceAdmin(FormattedAdmin):
    list_display = [
        'id', 'deleted', 'number'
    ]
    raw_id_fields = ['appeal', ]


@admin.register(Skill)
class SkillAdmin(FormattedAdmin):
    list_display = [
        'id', 'name', 'description'
    ]


@admin.register(UserSkill)
class UserSkillAdmin(FormattedAdmin):
    list_display = [
        'id', 'user', 'skill'
    ]
    raw_id_fields = ['user', 'skill']
