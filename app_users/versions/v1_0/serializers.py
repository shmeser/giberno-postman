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

    languages = serializers.SerializerMethodField(read_only=True)
    countries = serializers.SerializerMethodField(read_only=True)

    def validate_weight(self, weight):
        if weight is None:
            return weight
        if weight <= 20:
            raise HttpException(detail='weight должен быть больше 20кг', status_code=Errors.BAD_REQUEST.value)
        else:
            return weight

    def get_languages(self, product):
        # return g.request.user.vegetarianism
        return []

    def get_countries(self, product):
        # return g.request.user.vegetarianism
        return []

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'first_name',
            'last_name',
            'middle_name',
            'birth_date',
            'phone',
            'email',
            'languages',
            'countries',

        ]


class FillProfileSerializer(ProfileSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'id',
            'first_name',
            'last_name',
            'middle_name',
            'birth_date',
            'phone',
            'email',
            'languages',
            'countries',
        ]

        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': False},
            'middle_name': {'required': False},
            'birth_date': {'required': True},
            # 'email': {'required': False, 'allow_null': True, 'read_only': True},
        }
