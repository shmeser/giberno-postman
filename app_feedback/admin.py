from django.contrib.gis import admin

from app_feedback.models import Review, Like
from backend.mixins import FormattedAdmin


@admin.register(Review)
class ReviewAdmin(FormattedAdmin):
    list_display = [
        'text', 'value', 'uuid', 'created_at', 'owner_id', 'owner_ct', 'owner_ct_name', 'target_id', 'target_ct',
        'target_ct_name'
    ]
    list_filter = ['owner_ct_name', 'target_ct_name', 'deleted']
    readonly_fields = ['uuid']


@admin.register(Like)
class LikeAdmin(FormattedAdmin):
    list_display = [
        'created_at', 'owner_id', 'owner_ct', 'owner_ct_name', 'target_id', 'target_ct', 'target_ct_name'
    ]
    list_filter = ['owner_ct_name', 'target_ct_name', 'deleted']
