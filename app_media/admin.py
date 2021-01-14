from django.contrib.gis import admin
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField, JSONField, HStoreField
from django.db.models import UUIDField
from django.forms import TextInput, Textarea
from django.utils.html import format_html

from app_media.models import MediaModel


class FormattedAdmin(admin.OSMGeoAdmin):
    formfield_overrides = {
        ArrayField: {'widget': TextInput(attrs={'size': '150'})},
        models.CharField: {'widget': TextInput(attrs={'size': '150'})},
        UUIDField: {'widget': TextInput(attrs={'size': '150'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 10, 'cols': 150})},
        JSONField: {'widget': Textarea(attrs={'rows': 10, 'cols': 150})},
        HStoreField: {'widget': Textarea(attrs={'rows': 10, 'cols': 150})},
    }


@admin.register(MediaModel)
class MediaAdmin(FormattedAdmin):
    list_display = ['uuid', 'owner_id', 'owner_ct', 'owner_ct_name', 'file_preview', 'size', 'mime_type', 'type',
                    'format']
    list_filter = ['owner_ct', 'deleted', 'type', 'format']
    # картинка preview в просмотре
    readonly_fields = ["file_preview", 'uuid']

    def file_preview(self, obj):
        """ Превью загруженных картинок в списке """
        if obj.preview:
            return format_html(f'<img src="{obj.preview.url}" width="{150}" height="{100} "/>')
        else:
            return None
