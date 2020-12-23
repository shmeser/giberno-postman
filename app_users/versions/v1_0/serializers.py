from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from rest_framework import serializers
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from app_geo.versions.v1_0.serializers import LanguageSerializer, CountrySerializer
from app_media.enums import MediaType, MediaFormat
from app_media.versions.v1_0.repositories import MediaRepository
from app_media.versions.v1_0.serializers import MediaSerializer
from app_users.enums import LanguageProficiency
from app_users.models import UserProfile, SocialModel, UserLanguage, UserNationality
from app_users.versions.v1_0.repositories import ProfileRepository, SocialsRepository
from backend.entity import Error
from backend.errors.enums import ErrorsCodes
from backend.errors.http_exception import CustomException
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
    languages = serializers.SerializerMethodField()

    socials = serializers.SerializerMethodField(read_only=True)

    nationalities = serializers.SerializerMethodField(read_only=True)
    country = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()

    registration_completed = serializers.SerializerMethodField()

    def to_internal_value(self, data):
        m2m_errors = []
        # Проверяем m2m поля
        nationalities = data.pop('nationalities', None)
        if nationalities is not None and isinstance(nationalities, list):  # Обрабатываем только list
            # Удаляем гражданства
            self.instance.usernationality_set.all().update(deleted=True)
            # Добавляем или обновляем гражданства пользователя
            for n in nationalities:
                country_id = n.get('id', None)
                if country_id is None:
                    m2m_errors.append(
                        dict(Error(
                            code=ErrorsCodes.VALIDATION_ERROR.name,
                            detail='Указан неправильный id страны'))
                    )
                else:
                    try:
                        UserNationality.objects.update_or_create(defaults={
                            'deleted': False
                        },
                            **{
                                'user': self.instance,
                                'country_id': country_id,
                            }
                        )
                    except IntegrityError:
                        m2m_errors.append(
                            dict(Error(
                                code=ErrorsCodes.VALIDATION_ERROR.name,
                                detail='Указан неправильный id страны'))
                        )

        languages = data.pop('languages', None)
        if languages is not None and isinstance(languages, list):  # Обрабатываем только массив
            # Удаляем языки
            self.instance.userlanguage_set.all().update(deleted=True)
            # Добавляем или обновляем языки пользователя
            for l in languages:
                proficiency = l.get('proficiency', None)
                lang_id = l.get('id', None)
                if proficiency is None or not LanguageProficiency.has_value(proficiency):
                    m2m_errors.append(
                        dict(Error(
                            code=ErrorsCodes.VALIDATION_ERROR.name,
                            detail='Невалидные данные в поле proficiency'))
                    )
                else:
                    try:
                        UserLanguage.objects.update_or_create(defaults={
                            'proficiency': proficiency,
                            'deleted': False
                        },
                            **{
                                'user': self.instance,
                                'language_id': lang_id,
                            }
                        )
                    except IntegrityError:
                        m2m_errors.append(
                            dict(Error(
                                code=ErrorsCodes.VALIDATION_ERROR.name,
                                detail='Указан неправильный id языка'))
                        )

        if m2m_errors:
            raise CustomException(errors=m2m_errors)

        return super().to_internal_value(data)

    def update(self, instance, validated_data):
        print(validated_data)
        return super().update(instance, validated_data)

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

    def get_socials(self, profile: UserProfile):
        socials = SocialsRepository().filter_by_kwargs({
        }, order_by=['-created_at'])

        return SocialSerializer(socials, many=True).data

    def get_languages(self, profile: UserProfile):
        return LanguageSerializer(profile.languages.filter(userlanguage__deleted=False), many=True).data

    def get_nationalities(self, profile: UserProfile):
        return CountrySerializer(profile.nationalities.filter(usernationality__deleted=False), many=True).data

    def get_country(self, profile: UserProfile):
        return None

    def get_city(self, profile: UserProfile):
        return None

    def get_registration_completed(self, profile: UserProfile):
        if profile.first_name and \
                profile.last_name and \
                profile.birth_date is not None and \
                profile.email and \
                profile.phone:
            return True
        return False

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
            'registration_completed'
        ]

        extra_kwargs = {
            'phone': {'read_only': True}
        }


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
