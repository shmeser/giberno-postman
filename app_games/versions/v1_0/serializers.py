from rest_framework import serializers

from app_games.models import Prize, PrizeCard, GoodsCategory, Task
from app_media.enums import MediaType
from app_media.versions.v1_0.controllers import MediaController


class GoodsCategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsCategory
        fields = [
            'id',
            'title'
        ]


class PrizesSerializer(serializers.ModelSerializer):
    price_progress = serializers.SerializerMethodField()
    is_favourite = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    def get_price_progress(self, instance):
        return instance.price_progress

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
            'is_favourite',
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

    def get_prize(self, data):
        return PrizesInCardsSerializer(data.prize, many=False).data

    class Meta:
        model = PrizeCard
        fields = [
            'id',
            'value',
            'prize'
        ]


class TasksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'id',
            'name',
            'description',
            'bonus_value',
            'period',
            'type'
        ]
