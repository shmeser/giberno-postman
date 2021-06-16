from rest_framework import serializers

from app_feedback.models import Review
from backend.fields import DateTimeField


class POSTReviewSerializer(serializers.Serializer):
    text = serializers.CharField()
    value = serializers.FloatField(min_value=0.0, max_value=5.0)


class POSTShopReviewSerializer(serializers.Serializer):
    text = serializers.CharField()
    value = serializers.FloatField(min_value=0.0, max_value=5.0)
    shift = serializers.IntegerField(min_value=1)


class POSTReviewByManagerSerializer(serializers.Serializer):
    text = serializers.CharField()
    value = serializers.FloatField(min_value=0.0, max_value=5.0)
    shift = serializers.IntegerField(min_value=1)


class ReviewModelSerializer(serializers.ModelSerializer):
    created_at = DateTimeField()

    class Meta:
        model = Review
        fields = [
            'id',
            'uuid',
            'text',
            'owner_id',
            'created_at'
        ]
