from rest_framework import serializers

from app_feedback.models import Review
from app_market.models import Vacancy, Shop
from app_media.enums import MediaType
from app_media.versions.v1_0.controllers import MediaController
from app_users.models import UserProfile
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


class OwnerIsUserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField(read_only=True)

    def get_avatar(self, prefetched_data):
        return MediaController(self.instance).get_related_images(
            prefetched_data, MediaType.AVATAR.value, only_prefetched=True
        )

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "username",
            "first_name",
            "middle_name",
            "last_name",
            'avatar'
        ]


class OwnerIsShopSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField(read_only=True)

    def get_logo(self, prefetched_data):
        return MediaController(self.instance).get_related_images(
            prefetched_data, MediaType.AVATAR.value, only_prefetched=True
        )

    class Meta:
        model = Shop
        fields = [
            "id",
            "title",
            "logo"
        ]


class ReviewOwnerSerializer(serializers.Serializer):
    user = serializers.SerializerMethodField()
    shop = serializers.SerializerMethodField()

    def get_user(self, data):
        if data._meta.model_name == 'userprofile':
            return OwnerIsUserSerializer(data, many=False).data
        return None

    def get_shop(self, data):
        if data._meta.model_name == 'shop':
            return OwnerIsShopSerializer(data, many=False).data
        return None


class VacancyInReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vacancy
        fields = [
            "id",
            "title",
        ]


class ReviewsSerializer(serializers.ModelSerializer):
    created_at = DateTimeField()
    owner = serializers.SerializerMethodField()

    def get_owner(self, data):
        # Owner - GenericRelation - может быть либо user либо shop и т.д.
        if not data.owner:
            return None
        return ReviewOwnerSerializer(data.owner, many=False).data

    class Meta:
        model = Review
        fields = [
            'id',
            'created_at',
            'text',
            'value',
            'owner',
        ]


class ShopReviewsSerializer(ReviewsSerializer):
    vacancy = serializers.SerializerMethodField()

    def get_vacancy(self, data):
        if data.shift:
            return VacancyInReviewSerializer(data.shift.vacancy, many=False).data
        return None

    class Meta:
        model = Review
        fields = [
            'id',
            'created_at',
            'text',
            'value',
            'owner',
            'vacancy'
        ]


class ShopVacanciesReviewsSerializer(ReviewsSerializer):
    vacancy = serializers.SerializerMethodField()

    def get_vacancy(self, data):
        return VacancyInReviewSerializer(data.target, many=False).data

    class Meta:
        model = Review
        fields = [
            'id',
            'created_at',
            'text',
            'value',
            'owner',
            'vacancy'
        ]


class DistributorReviewsSerializer(ReviewsSerializer):
    class Meta:
        model = Review
        fields = [
            'id',
            'created_at',
            'text',
            'value',
            'owner',
        ]


class VacancyReviewsSerializer(ReviewsSerializer):
    class Meta:
        model = Review
        fields = [
            'id',
            'created_at',
            'text',
            'value',
            'owner',
        ]
