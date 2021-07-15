from rest_framework import serializers

from app_games.models import Prize


class PrizesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prize
        fields = [
            'id',
            'name',
            'price',
        ]
