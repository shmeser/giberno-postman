from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from app_admin.models import AccessUnit, AccessRight
from app_users.models import UserProfile


class AccessRightSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessRight
        fields = [
            'id',
            'get',
            'add',
            'edit',
            'delete',
        ]


class AccessSerializer(serializers.ModelSerializer):
    access_right = serializers.SerializerMethodField()

    def get_access_right(self, data):
        return AccessRightSerializer(data.access_right, many=False).data

    class Meta:
        model = AccessUnit
        fields = [
            'id',
            'object_id',
            'object_ct_id',
            'object_ct_name',
            'has_access',
            'access_right',
        ]


class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = [
            'id',
            'model',
        ]


class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'id',
            'username',
            'first_name',
            'middle_name',
            'last_name',
            'account_type',
        ]
