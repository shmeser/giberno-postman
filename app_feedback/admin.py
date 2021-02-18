from django.contrib.gis import admin
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField, JSONField, HStoreField
from django.db.models import UUIDField
from django.forms import TextInput, Textarea

from app_feedback.models import Review, Like


class FormattedAdmin(admin.OSMGeoAdmin):
    formfield_overrides = {
        ArrayField: {'widget': TextInput(attrs={'size': '150'})},
        models.CharField: {'widget': TextInput(attrs={'size': '150'})},
        UUIDField: {'widget': TextInput(attrs={'size': '150'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 10, 'cols': 150})},
        JSONField: {'widget': Textarea(attrs={'rows': 10, 'cols': 150})},
        HStoreField: {'widget': Textarea(attrs={'rows': 10, 'cols': 150})},
    }


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
