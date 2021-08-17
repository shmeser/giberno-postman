import re
import string

import luhn
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from rest_framework import serializers
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from app_feedback.models import Review
from app_geo.models import City, Country
from app_geo.versions.v1_0.repositories import CountriesRepository
from app_geo.versions.v1_0.serializers import LanguageSerializer, CountrySerializer, CitySerializer
from app_market.enums import ShiftAppealStatus
from app_market.models import UserProfession, Profession, UserSkill, Skill, ShiftAppealInsurance
from app_market.versions.v1_0.serializers import ProfessionSerializer, SkillSerializer, DistributorsSerializer
from app_media.enums import MediaType, MediaFormat
from app_media.versions.v1_0.controllers import MediaController
from app_media.versions.v1_0.repositories import MediaRepository
from app_media.versions.v1_0.serializers import MediaSerializer
from app_users.enums import LanguageProficiency, CardType, CardPaymentNetwork, DocumentType
from app_users.models import UserProfile, SocialModel, UserLanguage, UserNationality, Notification, \
    NotificationsSettings, UserCity, UserCareer, Document, Card, UserMoney
from app_users.versions.v1_0.repositories import ProfileRepository, SocialsRepository, NotificationsRepository, \
    CareerRepository, DocumentsRepository
from backend.entity import Error
from backend.errors.enums import ErrorsCodes
from backend.errors.http_exceptions import CustomException
from backend.fields import DateTimeField
from backend.mixins import CRUDSerializer
from backend.utils import choices, credit_regex


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

    has_insurance = serializers.SerializerMethodField(read_only=True)
    has_vaccination = serializers.SerializerMethodField(read_only=True)

    account_type = serializers.SerializerMethodField(read_only=True)
    birth_date = DateTimeField(required=False)
    avatar = serializers.SerializerMethodField(read_only=True)
    languages = serializers.SerializerMethodField()
    professions = serializers.SerializerMethodField()
    skills = serializers.SerializerMethodField()

    socials = serializers.SerializerMethodField(read_only=True)

    nationalities = serializers.SerializerMethodField(read_only=True)
    cities = serializers.SerializerMethodField()

    registration_completed = serializers.SerializerMethodField()

    notifications_count = serializers.SerializerMethodField(read_only=True)

    distributors = serializers.SerializerMethodField(read_only=True)

    def validate(self, attrs):
        errors = []

        # Проверяем введенные ссылки для соцсетей
        fb_link = attrs.get('fb_link', None)
        vk_link = attrs.get('vk_link', None)
        instagram_link = attrs.get('instagram_link', None)

        if fb_link is not None and 'facebook.com' not in fb_link:
            errors.append(
                dict(Error(
                    code=ErrorsCodes.VALIDATION_ERROR.name,
                    detail=f'Некорректная ссылка на Facebook'))
            )

        if vk_link is not None and 'vk.com' not in vk_link:
            errors.append(
                dict(Error(
                    code=ErrorsCodes.VALIDATION_ERROR.name,
                    detail=f'Некорректная ссылка на ВКонтакте'))
            )

        if instagram_link is not None and 'instagram.com' not in instagram_link:
            errors.append(
                dict(Error(
                    code=ErrorsCodes.VALIDATION_ERROR.name,
                    detail=f'Некорректная ссылка на Instagram'))
            )

        if errors:
            raise CustomException(errors=errors)

        return attrs

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

    def update_professions(self, data, errors):
        professions = data.pop('professions', None)
        if professions is not None and isinstance(professions, list):  # Обрабатываем только массив
            # Удаляем професии
            self.instance.userprofession_set.all().update(deleted=True)
            # Добавляем или професии
            for p in professions:
                profession_id = p.get('id', None) if isinstance(p, dict) else p
                if profession_id is None:
                    errors.append(
                        dict(Error(
                            code=ErrorsCodes.VALIDATION_ERROR.name,
                            detail='Невалидные данные в поле professions'))
                    )
                else:
                    try:
                        UserProfession.objects.update_or_create(defaults={
                            'profession_id': profession_id,
                            'deleted': False
                        },
                            **{
                                'user': self.instance,
                                'profession_id': profession_id,
                            }
                        )
                    except IntegrityError:
                        errors.append(
                            dict(Error(
                                code=ErrorsCodes.VALIDATION_ERROR.name,
                                detail='Указан неправильный id профессии'))
                        )

    def update_skills(self, data, errors):
        skills = data.pop('skills', None)
        if skills is not None and isinstance(skills, list):  # Обрабатываем только массив
            # Удаляем языки
            self.instance.userskill_set.all().update(deleted=True)
            # Добавляем или обновляем языки пользователя
            for s in skills:
                skill_id = s.get('id', None) if isinstance(s, dict) else s
                if skill_id is None:
                    errors.append(
                        dict(Error(
                            code=ErrorsCodes.VALIDATION_ERROR.name,
                            detail='Невалидные данные в поле skills'))
                    )
                else:
                    try:
                        UserSkill.objects.update_or_create(defaults={
                            'skill_id': skill_id,
                            'deleted': False
                        },
                            **{
                                'user': self.instance,
                                'skill_id': skill_id,
                            }
                        )
                    except IntegrityError:
                        errors.append(
                            dict(Error(
                                code=ErrorsCodes.VALIDATION_ERROR.name,
                                detail='Указан неправильный id специального навыка'))
                        )

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        errors = []

        # Проверяем fk поля

        # Проверяем m2m поля
        self.update_cities(data, errors)
        self.update_nationalities(data, errors)
        self.update_languages(data, errors)
        self.update_professions(data, errors)
        self.update_skills(data, errors)

        if errors:
            raise CustomException(errors=errors)

        return ret

    def get_account_type(self, profile):
        return profile.account_type

    def get_avatar(self, profile: UserProfile):
        # TODO префетчить
        avatar = MediaRepository().filter_by_kwargs({
            'owner_id': profile.id,
            'owner_ct_id': ContentType.objects.get_for_model(profile).id,
            'type': MediaType.AVATAR.value,
            'format': MediaFormat.IMAGE.value
        }, order_by=['-created_at']).first()
        if avatar:
            return MediaSerializer(avatar, many=False).data
        return None

    def get_socials(self, profile: UserProfile):
        # TODO префетчить
        socials = SocialsRepository().filter_by_kwargs({
            'user': profile,
            'deleted': False
        }, order_by=['-created_at'])

        return SocialSerializer(socials, many=True).data

    def get_languages(self, profile: UserProfile):
        # TODO префетчить
        return LanguageSerializer(
            profile.languages.filter(userlanguage__deleted=False), many=True,
            context={
                'me': self.me,
                'headers': self.headers
            }
        ).data

    def get_nationalities(self, profile: UserProfile):
        # TODO префетчить
        return CountrySerializer(
            CountriesRepository().fast_related_loading(
                profile.nationalities.filter(usernationality__deleted=False),
            ),
            many=True, context={
                'me': self.me,
                'headers': self.headers
            }
        ).data

    def get_professions(self, profile: UserProfile):
        # TODO префетчить
        return ProfessionSerializer(
            Profession.objects.filter(userprofession__user=profile, userprofession__deleted=False, deleted=False),
            many=True, context={
                'me': self.me,
                'headers': self.headers
            }
        ).data

    def get_skills(self, profile: UserProfile):
        # TODO префетчить
        return SkillSerializer(
            Skill.objects.filter(userskill__user=profile, userskill__deleted=False, deleted=False),
            many=True, context={
                'me': self.me,
                'headers': self.headers
            }
        ).data

    def get_cities(self, profile: UserProfile):
        # TODO префетчить
        return CitySerializer(profile.cities.filter(usercity__deleted=False), many=True, context={
            'me': self.me,
            'headers': self.headers
        }).data

    def get_notifications_count(self, profile: UserProfile):
        # TODO переделать на вычисление в annotate для ускорения
        return profile.notification_set.filter(read_at__isnull=True, deleted=False).count()

    def get_registration_completed(self, profile: UserProfile):
        if profile.first_name and \
                profile.last_name and \
                profile.birth_date is not None and \
                profile.email and \
                profile.phone:
            return True
        return False

    @staticmethod
    def get_distributors(instance):
        # TODO префетчить
        return DistributorsSerializer(instance=instance.distributors.all(), many=True).data

    @staticmethod
    def get_has_insurance(instance):
        return ShiftAppealInsurance.objects.filter(
            appeal__applier=instance,
            appeal__status=ShiftAppealStatus.CONFIRMED.value,
            deleted=False,
        ).exists()

    @staticmethod
    def get_has_vaccination(instance):
        return Document.objects.filter(
            type=DocumentType.VACCINATION_CERTIFICATE.value,
            user=instance,
            deleted=False
        ).exists()

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'username',
            'account_type',
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
            'rating_place',
            'notifications_count',
            'favourite_vacancies_count',
            'fb_link',
            'vk_link',
            'instagram_link',
            'education',

            'has_insurance',
            'has_vaccination',

            'avatar',
            'socials',
            'languages',
            'nationalities',
            'professions',
            'cities',
            'skills',

            'distributors',
            'shops',
        ]

        extra_kwargs = {
            'phone': {'read_only': True},
            'verified': {'read_only': True},
            'bonuses_acquired': {'read_only': True},
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
    icon = serializers.SerializerMethodField()

    def get_icon(self, prefetched_data):
        return MediaController(self.instance).get_related_images(prefetched_data, MediaType.NOTIFICATION_ICON.value)

    class Meta:
        model = Notification
        fields = [
            'id',
            'uuid',
            'subject_id',
            'title',
            'message',
            'type',
            'icon_type',
            'action',
            'read_at',
            'created_at',
            'icon'
        ]


class NotificationsSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationsSettings
        fields = [
            'enabled_types',
            'sound_enabled',
        ]


class CareerSerializer(CRUDSerializer):
    repository = CareerRepository

    country = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()

    def update_city(self, ret, data, errors):
        city_id = data.pop('city', None)
        if city_id is not None:
            city = City.objects.filter(pk=city_id, deleted=False).first()
            if city is None:
                errors.append(
                    dict(Error(
                        code=ErrorsCodes.VALIDATION_ERROR.name,
                        detail=f'Объект {City._meta.verbose_name} с ID={city_id} не найден'))
                )
            else:
                ret['city_id'] = city_id

    def update_country(self, ret, data, errors):
        country_id = data.pop('country', None)
        if country_id is not None:
            country = Country.objects.filter(pk=country_id, deleted=False).first()
            if country is None:
                errors.append(
                    dict(Error(
                        code=ErrorsCodes.VALIDATION_ERROR.name,
                        detail=f'Объект {City._meta.verbose_name} с ID={country_id} не найден'))
                )
            else:
                ret['country_id'] = country_id

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        errors = []

        # Добавляем пользователя
        ret['user_id'] = self.me.id

        # Проверяем fk поля
        self.update_city(ret, data, errors)
        self.update_country(ret, data, errors)

        if errors:
            raise CustomException(errors=errors)

        return ret

    def get_country(self, career: UserCareer):
        if not career.country:
            return None
        return CountrySerializer(career.country, many=False, context={
            'me': self.me,
            'headers': self.headers
        }).data

    def get_city(self, career: UserCareer):
        if not career.city:
            return None
        return CitySerializer(career.city, many=False, context={
            'me': self.me,
            'headers': self.headers
        }).data

    class Meta:
        model = UserCareer
        fields = [
            'id',
            'work_place',
            'position',
            'year_start',
            'year_end',
            'is_working_now',
            'country',
            'city',
        ]


class DocumentSerializer(CRUDSerializer):
    repository = DocumentsRepository

    media = serializers.SerializerMethodField()
    expiration_date = DateTimeField(required=False)
    issue_date = DateTimeField(required=False)
    created_at = DateTimeField(read_only=True)

    def to_internal_value(self, data):
        ret = super().to_internal_value(data)
        errors = []
        # Добавляем пользователя
        ret['user_id'] = self.me.id
        if errors:
            raise CustomException(errors=errors)

        return ret

    def get_media(self, prefetched_data):
        return MediaController(self.instance).get_related_media(prefetched_data, multiple=True)
        # return MediaSerializer(prefetched_data.medias, many=True).data

    class Meta:
        model = Document
        fields = [
            'id',
            'type',
            'series',
            'number',
            'category',
            'department_code',
            'issue_place',
            'issue_date',
            'is_foreign',
            'expiration_date',
            'created_at',
            'media'
        ]


######################################################################
class CreateManagerByAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'email',
            'phone',
            'first_name',
            'middle_name',
            'last_name',
            'distributors',
            'shops'
        ]


class UsernameSerializer(serializers.Serializer):
    username = serializers.CharField()


class PasswordSerializer(serializers.Serializer):
    password = serializers.CharField()

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError('Password is too short')
        for item in value:
            if item not in string.punctuation \
                    and item not in string.ascii_lowercase \
                    and item not in string.ascii_uppercase \
                    and item not in [number for number in range(10)]:
                raise serializers.ValidationError('Password contains invalid symbols')
            return value


class UsernameWithPasswordSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        if username:
            attrs['username'] = username.lower()
        return attrs


class EditManagerProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False)
    first_name = serializers.CharField(required=False)
    middle_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)

    class Meta:
        model = UserProfile
        fields = [
            'username',
            'first_name',
            'middle_name',
            'last_name',
        ]


# SERIALIZERS ONLY FOR SWAGGER
class FirebaseAuthRequestDescriptor(serializers.Serializer):
    firebase_token = serializers.CharField()


# ### SERIALIZERS ONLY FOR SWAGGER


class CreateSecurityByAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'distributors',
            'shops'
        ]


class UserInReviewSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField(read_only=True)

    def get_avatar(self, prefetched_data):
        return MediaController(self.instance).get_related_images(
            prefetched_data, MediaType.AVATAR.value, only_prefetched=False
        )

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'first_name',
            'middle_name',
            'last_name',
            'avatar',
        ]


class RatingSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    place = serializers.SerializerMethodField()

    def get_place(self, instance):
        return instance.place

    def get_rating(self, instance):
        return instance.total_rating

    def get_user(self, instance):
        return UserInReviewSerializer(instance, many=False).data

    class Meta:
        model = Review
        fields = [
            'place',
            'rating',
            'user'
        ]


class CardsValidator(serializers.Serializer):
    pan = serializers.CharField(max_length=19, min_length=14)
    valid_through = serializers.CharField(min_length=5, max_length=5)
    type = serializers.ChoiceField(choices=choices(CardType))
    payment_network = serializers.ChoiceField(choices=choices(CardPaymentNetwork))
    issuer = serializers.CharField(required=False, min_length=3)

    def validate_pan(self, value):
        if not luhn.verify(value):
            raise serializers.ValidationError("Invalid PAN")

        return credit_regex().sub(r'****\8', value)  # r'\2********\8'

    def validate_valid_through(self, value):
        if not re.match(r"(0[1-9]|1[0-2])\/?([0-9]{4}|[0-9]{2})", value):
            raise serializers.ValidationError("Invalid date for validThrough")
        return value


class CardsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = [
            'id',
            'pan',
            'valid_through',
            'type',
            'payment_network',
            'issuer',
        ]


class MoneySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMoney
        fields = [
            'id',
            'currency',
            'amount',
        ]
