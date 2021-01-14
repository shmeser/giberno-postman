from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from rest_framework import serializers
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from app_geo.models import City, Country
from app_geo.versions.v1_0.serializers import LanguageSerializer, CountrySerializer, CitySerializer
from app_media.enums import MediaType, MediaFormat
from app_media.versions.v1_0.repositories import MediaRepository
from app_media.versions.v1_0.serializers import MediaSerializer
from app_users.enums import LanguageProficiency
from app_users.models import UserProfile, SocialModel, UserLanguage, UserNationality, Notification, \
    NotificationsSettings, UserCity
from app_users.versions.v1_0.repositories import ProfileRepository, SocialsRepository, NotificationsRepository
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
    cities = serializers.SerializerMethodField()

    registration_completed = serializers.SerializerMethodField()

    rating_place = serializers.SerializerMethodField(read_only=True)
    notifications_count = serializers.SerializerMethodField(read_only=True)

    def update_cities(self, data, errors):
        cities = data.pop('cities', None)
        if cities is not None and isinstance(cities, list):  # Обрабатываем только list
            # Удаляем города
            self.instance.usercity_set.all().update(deleted=True)
            # Добавляем или обновляем города пользователя
            for c in cities:
                city_id = c.get('id', None) if isinstance(c, dict) else c
                if city_id is None:
                    errors.append(
                        dict(Error(
                            code=ErrorsCodes.VALIDATION_ERROR.name,
                            detail=f'Объект {City._meta.verbose_name} с ID={city_id} не найден'))
                    )
                else:
                    try:
                        UserCity.objects.update_or_create(defaults={
                            'deleted': False
                        },
                            **{
                                'user': self.instance,
                                'city_id': city_id,
                            }
                        )
                    except IntegrityError:
                        errors.append(
                            dict(Error(
                                code=ErrorsCodes.VALIDATION_ERROR.name,
                                detail=f'Объект {City._meta.verbose_name} с ID={city_id} не найден'))
                        )

    def update_nationalities(self, data, errors):
        nationalities = data.pop('nationalities', None)
        if nationalities is not None and isinstance(nationalities, list):  # Обрабатываем только list
            # Удаляем гражданства
            self.instance.usernationality_set.all().update(deleted=True)
            # Добавляем или обновляем гражданства пользователя
            for n in nationalities:
                country_id = n.get('id', None) if isinstance(n, dict) else n
                if country_id is None:
                    errors.append(
                        dict(Error(
                            code=ErrorsCodes.VALIDATION_ERROR.name,
                            detail=f'Объект {Country._meta.verbose_name} с ID={country_id} не найден'))
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
                        errors.append(
                            dict(Error(
                                code=ErrorsCodes.VALIDATION_ERROR.name,
                                detail=f'Объект {Country._meta.verbose_name} с ID={country_id} не найден'))
                        )

    def update_languages(self, data, errors):
        languages = data.pop('languages', None)
        if languages is not None and isinstance(languages, list):  # Обрабатываем только массив
            # Удаляем языки
            self.instance.userlanguage_set.all().update(deleted=True)
            # Добавляем или обновляем языки пользователя
            for l in languages:
                proficiency = l.get('proficiency', None)
                lang_id = l.get('id', None)
                if proficiency is None or not LanguageProficiency.has_value(proficiency):
                    errors.append(
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
                        errors.append(
                            dict(Error(
                                code=ErrorsCodes.VALIDATION_ERROR.name,
                                detail='Указан неправильный id языка'))
                        )

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        errors = []

        # Проверяем fk поля

        # Проверяем m2m поля
        self.update_cities(data, errors)
        self.update_nationalities(data, errors)
        self.update_languages(data, errors)

        if errors:
            raise CustomException(errors=errors)

        return ret

    def get_avatar(self, profile: UserProfile):
        avatar = MediaRepository().filter_by_kwargs({
            'owner_id': profile.id,
            'owner_ct_id': ContentType.objects.get_for_model(profile).id,
            'type': MediaType.AVATAR.value,
            'format': MediaFormat.IMAGE.value
        }, order_by=['-created_at']).first()
        if avatar:
            return MediaSerializer(avatar, many=False).data
        return None

    def get_documents(self, profile):
        documents = MediaRepository().filter_by_kwargs({
            'owner_id': profile.id,
            'owner_ct_id': ContentType.objects.get_for_model(profile).id,
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
            'user': profile,
            'deleted': False
        }, order_by=['-created_at'])

        return SocialSerializer(socials, many=True).data

    def get_languages(self, profile: UserProfile):
        return LanguageSerializer(profile.languages.filter(userlanguage__deleted=False), many=True).data

    def get_nationalities(self, profile: UserProfile):
        return CountrySerializer(profile.nationalities.filter(usernationality__deleted=False), many=True).data

    def get_cities(self, profile: UserProfile):
        return CitySerializer(profile.cities.filter(usercity__deleted=False), many=True).data

    def get_rating_place(self, profile: UserProfile):
        return None

    def get_notifications_count(self, profile: UserProfile):
        return profile.notification_set.filter(read_at__isnull=True, deleted=False).count()

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
            'first_name',
            'last_name',
            'middle_name',
            'birth_date',
            'gender',
            'phone',
            'show_phone',
            'email',
            'terms_accepted',
            'policy_accepted',
            'agreement_accepted',
            'registration_completed',
            'verified',
            'bonus_balance',
            'rating_place',
            'notifications_count',
            'favourite_vacancies_count',
            'avatar',
            'documents',
            'socials',
            'languages',
            'nationalities',
            'cities',
        ]

        extra_kwargs = {
            'phone': {'read_only': True},
            'verified': {'read_only': True},
            'bonus_balance': {'read_only': True},
            'favourite_vacancies_count': {'read_only': True}
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
            'created_at',
            'is_for_reg',
        ]


class NotificationSerializer(CRUDSerializer):
    repository = NotificationsRepository

    created_at = DateTimeField()
    read_at = DateTimeField()

    class Meta:
        model = Notification
        fields = [
            'id',
            'subject_id',
            'title',
            'message',
            'type',
            'action',
            'read_at',
            'created_at',
        ]


class NotificationsSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationsSettings
        fields = [
            'enabled_types',
        ]
