import uuid

from django.contrib.gis.db import models

from app_users.models import UserProfile
from backend.models import BaseModel


class Socket(BaseModel):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    socket_id = models.TextField()
    room_name = models.CharField(max_length=255, blank=True, null=True)
    room_id = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f'User: {self.user.username}, socket_id: {self.socket_id}, {self.room_name}{self.room_id}'

    class Meta:
        db_table = 'app_sockets'
        verbose_name = 'Сокет'
        verbose_name_plural = 'Сокеты'
