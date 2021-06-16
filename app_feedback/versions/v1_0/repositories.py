from django.contrib.contenttypes.models import ContentType
from django.db.models import prefetch_related_objects, Prefetch

from app_feedback.models import Review
from app_market.models import Shop
from app_media.enums import MediaType, MediaFormat
from app_media.models import MediaModel
from app_users.models import UserProfile
from backend.mixins import MasterRepository


class ReviewsRepository(MasterRepository):
    model = Review

    def get_shop_reviews(self, shop_id, pagination=None):
        target_ct = ContentType.objects.get_for_model(Shop)

        queryset = self.model.objects.filter(
            target_ct=target_ct,
            target_id=shop_id,
            deleted=False
        ).select_related(
            'shift__vacancy'
        ).order_by('-created_at')

        # Префетчим логотипы магазинов для owner, который Generic Relation
        shop_ct = ContentType.objects.get_for_model(Shop)
        owner_is_shop = [item for item in queryset if item.owner_ct_id == shop_ct.id]
        if owner_is_shop:
            prefetch_related_objects(owner_is_shop, Prefetch(
                "owner__media",
                queryset=MediaModel.objects.filter(
                    deleted=False,
                    type=MediaType.LOGO.value,
                    owner_ct_id=ContentType.objects.get_for_model(Shop).id,
                    format=MediaFormat.IMAGE.value
                ).order_by('-created_at'),  # Сортировка по дате обязательно
                to_attr='medias'
            ))

        # Префетчим аватарки пользователей для owner, который Generic Relation
        user_ct = ContentType.objects.get_for_model(UserProfile)
        owner_is_user = [item for item in queryset if item.owner_ct_id == user_ct.id]
        if owner_is_user:
            prefetch_related_objects(owner_is_user, Prefetch(
                "owner__media",
                queryset=MediaModel.objects.filter(
                    deleted=False,
                    type=MediaType.AVATAR.value,
                    owner_ct_id=ContentType.objects.get_for_model(UserProfile).id,
                    format=MediaFormat.IMAGE.value
                ).order_by('-created_at'),  # Сортировка по дате обязательно
                to_attr='medias'
            ))

        if pagination:
            return queryset[pagination.offset:pagination.limit]

        return queryset
