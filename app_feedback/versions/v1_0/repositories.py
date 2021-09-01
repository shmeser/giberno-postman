from django.contrib.contenttypes.models import ContentType
from django.db.models import prefetch_related_objects, Prefetch

from app_feedback.models import Review
from app_market.models import Shop, Distributor, Vacancy
from app_media.enums import MediaType, MediaFormat
from app_media.models import MediaModel
from app_users.models import UserProfile
from backend.mixins import MasterRepository


class ReviewsRepository(MasterRepository):
    model = Review

    def get_reviews(self, target_ct, target_ids):
        queryset = self.model.objects.filter(
            target_ct=target_ct,
            target_id__in=target_ids,
            deleted=False
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

        return queryset

    def get_shop_vacancies_reviews(self, shop_id, pagination=None):
        target_ct = ContentType.objects.get_for_model(Vacancy)

        vacancies_ids = Vacancy.objects.filter(
            deleted=False,
            shop_id=shop_id
        ).values_list('id', flat=True)

        queryset = self.get_reviews(target_ct, vacancies_ids)

        if pagination:
            return queryset[pagination.offset:pagination.limit]

        return queryset

    def get_distributor_reviews(self, distributor_id, pagination=None):
        target_ct = ContentType.objects.get_for_model(Distributor)
        queryset = self.get_reviews(target_ct, [distributor_id])

        if pagination:
            return queryset[pagination.offset:pagination.limit]

        return queryset

    def get_vacancy_reviews(self, vacancy_id, pagination=None):
        target_ct = ContentType.objects.get_for_model(Vacancy)
        queryset = self.get_reviews(target_ct, [vacancy_id])

        if pagination:
            return queryset[pagination.offset:pagination.limit]

        return queryset

    def get_self_employed_reviews(self, user_id, pagination=None):
        target_ct = ContentType.objects.get_for_model(UserProfile)
        queryset = self.get_reviews(target_ct, [user_id])

        if pagination:
            return queryset[pagination.offset:pagination.limit]

        return queryset
