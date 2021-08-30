from rest_framework import serializers

from app_games.models import Prize, PrizeCard, GoodsCategory, Task
from app_media.enums import MediaType
from app_media.versions.v1_0.controllers import MediaController
from app_users.models import UserProfile


class GoodsCategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsCategory
        fields = [
            'id',
            'title'
        ]


class PrizesSerializer(serializers.ModelSerializer):
    available_count = serializers.SerializerMethodField()
    price_progress = serializers.SerializerMethodField()
    is_favourite = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    def get_price_progress(self, instance):
        return instance.price_progress

    def get_available_count(self, instance):
        return instance.available_count

    def get_is_favourite(self, instance):
        return instance.is_favourite

    def get_image(self, prefetched_data):
        return MediaController(self.instance).get_related_images(
            prefetched_data, MediaType.PRIZE_IMAGE.value, only_prefetched=True
        )

    def get_categories(self, instance):
        return GoodsCategoriesSerializer(instance.categories, many=True).data

    class Meta:
        model = Prize
        fields = [
            'id',
            'name',
            'description',
            'price',
            'price_progress',
            'grade',
            'count',
            'available_count',
            'is_favourite',
            'categories',
            'image'
        ]


class PrizesSerializerAdmin(PrizesSerializer):
    class Meta:
        model = Prize
        fields = [
            'id',
            'name',
            'description',
            'price',
            'real_price',
            'real_price_currency',
            'grade',
            'count',
            'available_count',
            'categories',
            'image'
        ]


class PrizesInCardsSerializer(PrizesSerializer):
    class Meta:
        model = Prize
        fields = [
            'id',
            'name',
            'grade',
            'categories',
            'image'
        ]


class PrizeCardsSerializer(serializers.ModelSerializer):
    prize = serializers.SerializerMethodField()
    is_opened = serializers.SerializerMethodField()

    def get_is_opened(self, data):
        return data.opened_at is not None

    def get_prize(self, data):
        return PrizesInCardsSerializer(data.prize, many=False).data

    class Meta:
        model = PrizeCard
        fields = [
            'id',
            'value',
            'is_opened',
            'prize'
        ]


class TasksSerializer(serializers.ModelSerializer):
    is_completed = serializers.SerializerMethodField()

    def get_is_completed(self, data):
        return data.is_completed

    class Meta:
        model = Task
        fields = [
            'id',
            'name',
            'description',
            'bonus_value',
            'period',
            'type',
            'is_completed',
        ]


class TasksSerializerAdmin(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'id',
            'name',
            'description',
            'bonus_value',
            'period',
            'type',
        ]


class UserBonusesSerializerAdmin(serializers.ModelSerializer):
    bonus_balance = serializers.SerializerMethodField()

    def get_bonus_balance(self, data):
        return data.bonus_balance

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'first_name',
            'middle_name',
            'last_name',
            'username',
            'email',
            'phone',
            'bonus_balance',
        ]
