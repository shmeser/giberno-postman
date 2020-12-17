from rest_framework import serializers
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from app_users.models import UserProfile
from app_users.versions.v1_0.repositories import ProfileRepository
from backend.fields import DateTimeField
from backend.mixins import CRUDSerializer


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    def validate(self, attrs):
        refresh_token = RefreshToken(attrs['refresh_token'])

        data = {'access_token': str(refresh_token.access_token)}

        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    # Attempt to blacklist the given refresh token
                    refresh_token.blacklist()
                except AttributeError:
                    # If blacklist app not installed, `blacklist` method will
                    # not be present
                    pass

            refresh_token.set_jti()
            refresh_token.set_exp()

            data['refresh_token'] = str(refresh_token)

        return data


class ProfileSerializer(CRUDSerializer):
    repository = ProfileRepository

    birth_date = DateTimeField()
    avatar = serializers.SerializerMethodField(read_only=True)
    documents = serializers.SerializerMethodField(read_only=True)
    languages = serializers.SerializerMethodField(read_only=True)

    nationalities = serializers.SerializerMethodField(read_only=True)
    country = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()

    # def validate_phone(self, phone):
    #     with_same_phone = False
    #     if phone:
    #         with_same_phone = ProfileRepository().filter_by_kwargs({
    #             'phone': phone,
    #         }).exclude(id=globals.request.user.id).exists()
    #     if with_same_phone:
    #         raise serializers.ValidationError(
    #             detail=ErrorsCodes.PHONE_IS_USED.value, code=ErrorsCodes.PHONE_IS_USED.name
    #         )
    #     return phone

    def get_avatar(self, profile):
        return None

    def get_documents(self, profile):
        return []

    def get_languages(self, profile):
        return []

    def get_nationalities(self, profile):
        return []

    def get_country(self, profile):
        return None

    def get_city(self, profile):
        return None

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'avatar',
            'documents',
            'first_name',
            'last_name',
            'middle_name',
            'birth_date',
            'phone',
            'email',
            'languages',
            'nationalities',
            'policy_accepted',
            'agreement_accepted',
            'country',
            'city',
        ]
        extra_kwargs = {
            'phone': {'read_only': True},
        }


class FillProfileSerializer(ProfileSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'id',
            'avatar',
            'documents',
            'first_name',
            'last_name',
            'middle_name',
            'birth_date',
            'phone',
            'email',
            'languages',
            'nationality',
            'policy_accepted',
            'agreement_accepted',
            'country',
            'city',
        ]

        extra_kwargs = {
            'phone': {'read_only': True},
            'first_name': {'required': True},
            'last_name': {'required': False},
            'middle_name': {'required': False},
            'birth_date': {'required': True},
        }
