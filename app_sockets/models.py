from django.contrib.gis.db import models

from app_sockets.enums import SocketGroupType
from app_users.models import UserProfile
from backend.models import BaseModel
from backend.utils import choices


class Socket(BaseModel):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    socket_id = models.TextField()
    group_type = models.IntegerField(blank=True, null=True, choices=choices(SocketGroupType))
    group_id = models.IntegerField(blank=True, null=True)
    connected_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'User: {self.user.username}, socket_id: {self.socket_id}'

    class Meta:
        db_table = 'app_sockets'
        verbose_name = 'Сокет'
        verbose_name_plural = 'Сокеты'
