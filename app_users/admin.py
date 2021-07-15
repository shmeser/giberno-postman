from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis import admin

from app_users.models import SocialModel, UserProfile, Notification, NotificationsSettings, JwtToken
from backend.mixins import FormattedAdmin

admin.site.register(User, admin.OSMGeoAdmin)
admin.site.register(ContentType, admin.OSMGeoAdmin)


@admin.register(Permission)
class GroupAdmin(FormattedAdmin):
    list_display = (
        "id", "name", "content_type", "codename"
    )

    raw_id_fields = ("content_type",)


@admin.register(JwtToken)
class JwtTokenAdmin(FormattedAdmin):
    list_display = (
        "id", "user", 'access_token', "created_at"
    )


@admin.register(UserProfile)
class UserProfileAdmin(FormattedAdmin):
    list_display = (
        "id", "account_type", "username", "birth_date", "phone", "email", "created_at"
    )


@admin.register(SocialModel)
class SocialModelAdmin(FormattedAdmin):
    list_display = (
        "id", "user_id", "type", "phone", "email", "created_at"
    )

    raw_id_fields = ("user",)


@admin.register(Notification)
class NotificationAdmin(FormattedAdmin):
    list_display = (
        "id", "user_id", "subject_id", "title", "message", "type", "action", "read_at"
    )

    list_filter = ["type", "action"]
    raw_id_fields = ("user",)


@admin.register(NotificationsSettings)
class NotificationsSettingsAdmin(FormattedAdmin):
    list_display = (
        "id", "user_id", "enabled_types"
    )
