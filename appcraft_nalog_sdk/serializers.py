from rest_framework import serializers

from appcraft_nalog_sdk.models import NalogNotificationModel, NalogUser, NalogIncomeRequestModel, \
    NalogBindPartnerRequestModel


class NalogBindPartnerRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = NalogBindPartnerRequestModel
        fields = '__all__'


class NalogUserSerializer(serializers.ModelSerializer):
    bind_request = serializers.SerializerMethodField()

    def get_bind_request(self, user: NalogUser):
        return NalogBindPartnerRequestSerializer(user.nalogbindpartnerrequestmodel_set.last()).data

    class Meta:
        model = NalogUser
        fields = '__all__'


class NalogNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NalogNotificationModel
        fields = '__all__'


class NalogIncomeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = NalogIncomeRequestModel
        fields = '__all__'
