from rest_framework import serializers

# from app_feedback.models import Comment
from app_feedback.models import Review
from backend.fields import DateTimeField


# class CommentSerializer(serializers.ModelSerializer):
#     created_at = DateTimeField()
#     attachment = serializers.SerializerMethodField()
#     owner = serializers.SerializerMethodField()
#
#     def get_attachment(self, prefetched_data):
#         return None
#
#     def get_owner(self, prefetched_data):
#         return None
#
#     class Meta:
#         model = Comment
#         fields = [
#             'uuid',
#             'text',
#             'attachment',
#             'owner',
#             'created_at'
#         ]


class POSTReviewSerializer(serializers.Serializer):
    text = serializers.CharField()
    value = serializers.FloatField(min_value=0.0, max_value=5.0)


class ReviewModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'
