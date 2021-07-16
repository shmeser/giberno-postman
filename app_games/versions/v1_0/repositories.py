from django.contrib.contenttypes.models import ContentType
from django.db.models import Prefetch, ExpressionWrapper, Exists, OuterRef, BooleanField, Subquery, Count, Window
from django.db.models.functions import Coalesce
from django.utils.timezone import now

from app_games.enums import Grade
from app_games.models import Prize, Task, UserFavouritePrize, UserPrizeProgress
from app_media.enums import MediaType, MediaFormat
from app_media.models import MediaModel
from backend.entity import Error
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exceptions import HttpException, CustomException
from backend.mixins import MasterRepository
from giberno.settings import MAX_AMOUNT_FOR_PREFERRED_DEFAULT_GRADE_PRIZES


class PrizesRepository(MasterRepository):
    model = Prize

    def __init__(self, me=None) -> None:
        super().__init__()
        self.me = me

        # является ли приоритетным призом
        self.is_favourite_expression = ExpressionWrapper(
            Exists(UserFavouritePrize.objects.filter(
                deleted=False,
                user_id=self.me.id,
                prize_id=OuterRef('pk'),
            )),
            output_field=BooleanField()
        )

        # прогресс по осколкам
        self.price_progress_expression = Coalesce(Subquery(
            UserPrizeProgress.objects.filter(
                prize=OuterRef('pk'), user=self.me, completed_at__isnull=True
            ).values('value')[:1]
        ), 0)

        # Основная часть запроса, содержащая вычисляемые поля
        self.base_query = self.model.objects.annotate(
            is_favourite=self.is_favourite_expression,
            price_progress=self.price_progress_expression,
        )

    def inited_get_by_id(self, record_id):
        # если будет self.base_query.filter() то manager ничего не сможет увидеть
        records = self.base_query.filter(pk=record_id).exclude(deleted=True)
        record = self.fast_related_loading(records).first()
        if not record:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден')
        return record

    def set_like(self, record_id):
        prize = self.model.objects.filter(pk=record_id, deleted=False).annotate(
            # Считаем сколько лайков уже есть для призов такого же уровня, как у запрашиваемого приза
            same_grade_likes_count=Coalesce(Subquery(
                UserFavouritePrize.objects.filter(
                    deleted=False,
                    prize__grade=OuterRef('grade'),  # Берем такой же уровень
                    user=self.me,  # Мои приоритетные товары
                ).annotate(
                    count=Window(
                        expression=Count('id'),  # Считаем количество
                    )
                ).values('count')[:1]
            ), 0)
        ).first()

        if not prize:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден')

        # проверка на уровень приза, если лайкается с тем же уровнем
        if prize.grade == Grade.DEFAULT.value:
            if prize.same_grade_likes_count >= MAX_AMOUNT_FOR_PREFERRED_DEFAULT_GRADE_PRIZES:
                raise CustomException(errors=[
                    dict(Error(ErrorsCodes.MAX_PREFERRED_PRIZES_AMOUNT_EXCEEDED))
                ])
        else:
            if prize.same_grade_likes_count > 0:  # Не больше одного предпочитаемого товара более высокого уровня
                raise CustomException(errors=[
                    dict(Error(ErrorsCodes.MAX_PREFERRED_PRIZES_AMOUNT_EXCEEDED))
                ])

        like, created = UserFavouritePrize.objects.get_or_create(
            user=self.me,
            prize=prize
        )

        if not created:
            like.deleted = False
            like.updated_at = now()
            like.save()

    def remove_like(self, record_id):
        prize = self.get_by_id(record_id)

        like = UserFavouritePrize.objects.filter(
            user=self.me,
            prize=prize
        ).first()

        if like:
            like.deleted = True
            like.updated_at = now()
            like.save()

    @staticmethod
    def get_conditions_for_promotion():
        promo_documents = MediaModel.objects.filter(
            owner_id=None, type=MediaType.MARKETING_POLICY.value, deleted=False
        )

        return promo_documents

    def get_cards(self):
        return self.model.objects.filter(deleted=False)

    @staticmethod
    def fast_related_loading(queryset):
        prize_ct = ContentType.objects.get_for_model(Prize).id
        queryset = queryset.prefetch_related(
            Prefetch(
                'media',
                queryset=MediaModel.objects.filter(
                    deleted=False,
                    owner_ct_id=prize_ct,
                    type=MediaType.PRIZE_IMAGE.value,  # Подгружаем изображения призов
                    format=MediaFormat.IMAGE.value,
                ).order_by('-created_at'),
                to_attr='medias'  # Подгружаем файлы в поле medias
            ),
            'categories'
        )

        return queryset

    def inited_filter_by_kwargs(self, kwargs, paginator=None, order_by: list = None):
        # Изменяем kwargs для работы с objects.filter(**kwargs)
        if order_by:
            records = self.base_query.order_by(*order_by).exclude(deleted=True).filter(**kwargs)
        else:
            records = self.base_query.exclude(deleted=True).filter(**kwargs)
        return self.fast_related_loading(  # Предзагрузка связанных сущностей
            queryset=records[paginator.offset:paginator.limit] if paginator else records,
        )


class TasksRepository(MasterRepository):
    model = Task

    def __init__(self, me=None) -> None:
        super().__init__()
        self.me = me

    def get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден'
            )

    def get_tasks(self, kwargs, paginator, order_by):
        return []
