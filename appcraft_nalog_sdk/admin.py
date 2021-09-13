from django.contrib import admin

from appcraft_nalog_sdk.models import NalogRequestModel, NalogUser, NalogNotificationModel, \
    NalogBindPartnerRequestModel, NalogIncomeRequestModel, NalogIncomeCancelReasonModel, NalogDocumentModel


@admin.register(NalogUser)
class NalogUserAdmin(admin.ModelAdmin):
    list_display = ['inn', 'status', 'is_tax_payment']
    exclude = ['deleted_at']
    search_fields = ['inn']


@admin.register(NalogRequestModel)
class NalogRequestModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'message_id', 'status', 'created_at', 'updated_at']
    exclude = ['deleted_at']
    list_filter = ['name', 'status']
    search_fields = ['name', 'message_id']


@admin.register(NalogNotificationModel)
class NalogNotificationModelAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'status']
    exclude = ['deleted_at']


@admin.register(NalogBindPartnerRequestModel)
class NalogBindPartnerRequestModelAdmin(admin.ModelAdmin):
    list_display = ['user', 'order_id', 'status']
    exclude = ['deleted_at']
    search_fields = ['user']
    list_filter = ['status']


@admin.register(NalogIncomeRequestModel)
class NalogIncomeRequestModelAdmin(admin.ModelAdmin):
    list_display = ['user', 'receipt_id', 'link', 'error_message', 'canceled_reason']
    exclude = ['deleted_at']


@admin.register(NalogIncomeCancelReasonModel)
class NalogIncomeCancelReasonModelAdmin(admin.ModelAdmin):
    list_display = ['code', 'description', 'deleted_at']


@admin.register(NalogDocumentModel)
class NalogDocumentModelAdmin(admin.ModelAdmin):
    list_display = ['user', 'create_time']
    exclude = ['deleted_at']
