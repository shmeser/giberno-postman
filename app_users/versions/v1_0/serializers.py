from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from app_media.enums import MediaType, MediaFormat
from app_media.versions.v1_0.repositories import MediaRepository
from app_media.versions.v1_0.serializers import MediaSerializer
from app_users.models import UserProfile, SocialModel
from app_users.versions.v1_0.repositories import ProfileRepository, SocialsRepository
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

    birth_date = DateTimeField(required=False)
    avatar = serializers.SerializerMethodField(read_only=True)
    documents = serializers.SerializerMethodField(read_only=True)
    languages = serializers.SerializerMethodField(read_only=True)

    socials = serializers.SerializerMethodField(read_only=True)

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

    def get_avatar(self, profile: UserProfile):
        avatar = MediaRepository().filter_by_kwargs({
            'owner_id': profile.id,
            'owner_content_type_id': ContentType.objects.get_for_model(profile).id,
            'type': MediaType.AVATAR.value,
            'format': MediaFormat.IMAGE.value
        }, order_by=['-created_at']).first()
        if avatar:
            return MediaSerializer(avatar, many=False).data
        return None

    def get_documents(self, profile):
        documents = MediaRepository().filter_by_kwargs({
            'owner_id': profile.id,
            'owner_content_type_id': ContentType.objects.get_for_model(profile).id,
            'type__in': [
                MediaType.PASSPORT.value,
                MediaType.INN.value,
                MediaType.SNILS.value,
                MediaType.MEDICAL_BOOK.value,
                MediaType.DRIVER_LICENCE.value,
            ],
            'format__in': [MediaFormat.IMAGE.value, MediaFormat.DOCUMENT.value]
        }, order_by=['-created_at'])

        return MediaSerializer(documents, many=True).data

    def get_socials(self, profile):
        socials = SocialsRepository().filter_by_kwargs({
        }, order_by=['-created_at'])

        return SocialSerializer(socials, many=True).data

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
            'socials',
            'languages',
            'nationalities',
            'policy_accepted',
            'agreement_accepted',
            'country',
            'city',
            'edited'
        ]
        
        extra_kwargs = {}


class SocialSerializer(CRUDSerializer):
    repository = SocialsRepository

    created_at = DateTimeField()

    class Meta:
        model = SocialModel
        fields = [
            'id',
            'type',
            'first_name',
            'last_name',
            'middle_name',
            'username',
            'phone',
            'email',
            'created_at'
        ]

# class FillProfileSerializer(ProfileSerializer):
#     class Meta:
#         model = UserProfile
#         fields = [
#             'id',
#             'avatar',
#             'documents',
#             'first_name',
#             'last_name',
#             'middle_name',
#             'birth_date',
#             'phone',
#             'email',
#             'languages',
#             'nationality',
#             'policy_accepted',
#             'agreement_accepted',
#             'country',
#             'city',
#         ]
#
#         extra_kwargs = {
#             'phone': {'read_only': True},
#             'first_name': {'required': True},
#             'last_name': {'required': False},
#             'middle_name': {'required': False},
#             'birth_date': {'required': True},
#         }
