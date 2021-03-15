from django.contrib.gis import admin

from app_sockets.models import Socket


@admin.register(Socket)
class BotChatAdmin(admin.OSMGeoAdmin):
    list_display = ("uuid", "user_id", "room_name", "room_id", "socket_id")

    list_filter = ("room_name",)

    raw_id_fields = ['user']
