from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.db.models import Prefetch, ExpressionWrapper, Exists, OuterRef, BooleanField, Subquery, Count, Window, Max, \
    F, IntegerField, Case, When, DateField
from django.db.models.functions import Coalesce, Trunc
from django.utils.timezone import now

from app_games.enums import Grade, TaskKind, TaskPeriod
from app_games.models import Prize, Task, UserFavouritePrize, UserPrizeProgress, PrizeCardsHistory, PrizeCard, UserTask
from app_market.versions.v1_0.repositories import ShiftAppealsRepository
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

        # Количество доступных товаров
        self.available_count_expression = ExpressionWrapper(
            F('count') - Coalesce(Subquery(
                UserPrizeProgress.objects.filter(
                    # Количество завершенных записей прогресса по призу
                    prize=OuterRef('pk'), user=self.me, completed_at__isnull=False
                ).annotate(
                    count=Window(
                        expression=Count('id'),  # Считаем количество
                    )
                ).values('count')[:1]
            ), 0),
            output_field=IntegerField()
        )

        # Основная часть запроса, содержащая вычисляемые поля
        self.base_query = self.model.objects.annotate(
            is_favourite=self.is_favourite_expression,
            price_progress=self.price_progress_expression,
            available_count=self.available_count_expression,
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
        prize_ct = ContentType.objects.get_for_model(Prize).id

        # История выдачи карточек пользователю
        cards_history = PrizeCardsHistory.objects.filter(
            user=self.me,
            deleted=False,
            opened_at__isnull=True
        ).annotate(
            max_bonuses_acquired=Subquery(
                PrizeCardsHistory.objects.filter(
                    user=self.me,
                    deleted=False,
                    opened_at__isnull=True
                ).annotate(
                    max=Window(
                        expression=Max('bonuses_acquired')
                    )
                ).values('max')[:1]
            )
        ).filter(
            # Выбираем те карточки, которые выпали на последнем начислении очков славы
            bonuses_acquired=F('max_bonuses_acquired')
        )

        return PrizeCard.objects.filter(
            deleted=False,
            cards_history__in=cards_history
        ).order_by('-prize__grade', '-prize__real_price').select_related('prize').prefetch_related(
            Prefetch(
                'prize__media',
                queryset=MediaModel.objects.filter(
                    deleted=False,
                    owner_ct_id=prize_ct,
                    type=MediaType.PRIZE_IMAGE.value,  # Подгружаем изображения призов
                    format=MediaFormat.IMAGE.value,
                ).order_by('-created_at'),
                to_attr='medias'  # Подгружаем файлы в поле medias
            ),
            'prize__categories'
        ).annotate(
            opened_at=Subquery(cards_history.filter(card=OuterRef('pk')).values('opened_at')[:1])
        ).filter(opened_at__isnull=True)  # Не показываем открытые ранее карточки

    def open_issued_card(self, record_id):
        """
        Открыть выданную карточку
        :param record_id:
        :return: prize_card
        """
        prize_ct = ContentType.objects.get_for_model(Prize).id

        # История выдачи конкретной карточки пользователю
        card_history = PrizeCardsHistory.objects.filter(
            user=self.me,
            deleted=False,
            opened_at__isnull=True,
            card_id=record_id
        ).annotate(
            max_bonuses_acquired=Subquery(
                PrizeCardsHistory.objects.filter(
                    user=self.me,
                    deleted=False,
                    opened_at__isnull=True,
                    card_id=record_id
                ).annotate(
                    max=Window(
                        expression=Max('bonuses_acquired')
                    )
                ).values('max')[:1]
            )
        ).filter(
            # Выбираем те карточки, которые выпали на последнем начислении очков славы
            bonuses_acquired=F('max_bonuses_acquired')
        ).first()

        if not card_history:
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.PRIZE_CARD_WAS_NOT_BEEN_ISSUED))
            ])

        card_history.opened_at = now()
        card_history.save()

        prize_card = PrizeCard.objects.filter(
            deleted=False,
            cards_history=card_history
        ).order_by('-prize__grade', '-prize__real_price').select_related('prize').prefetch_related(
            Prefetch(
                'prize__media',
                queryset=MediaModel.objects.filter(
                    deleted=False,
                    owner_ct_id=prize_ct,
                    type=MediaType.PRIZE_IMAGE.value,  # Подгружаем изображения призов
                    format=MediaFormat.IMAGE.value,
                ).order_by('-created_at'),
                to_attr='medias'  # Подгружаем файлы в поле medias
            ),
            'prize__categories'
        ).annotate(
            opened_at=Subquery(
                PrizeCardsHistory.objects.filter(
                    pk=card_history.id, card=OuterRef('pk')
                ).values('opened_at')[:1])
        ).first()

        # Пересчитываем прогресс по призу
        self.recalc_prize_progress(user_id=self.me.id, prize_id=prize_card.prize_id, value=prize_card.value)

        return prize_card

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

    @staticmethod
    def get_random_card_for_prize(prize_id):
        return PrizeCard.objects.filter(
            deleted=False,
            prize_id=prize_id
        ).order_by('?').first()

    @staticmethod
    def recalc_prize_progress(user_id, prize_id, value):
        progress, created = UserPrizeProgress.objects.get_or_create(
            deleted=False,
            user_id=user_id,
            prize_id=prize_id,
        )
        if value:
            progress.value += value
            progress.save()

    @classmethod
    def issue_prize_cards_for_user(cls, user_id, bonuses_acquired):
        """
        Выдача карточек пользователю

        :param user_id:
        :param bonuses_acquired:
        :return:
        """

        # Рандомно выбрать 3 обычных товара и по одному товару уровня EPIC и LEGENDARY
        default_prizes = cls.model.objects.filter(
            deleted=False,
            grade=Grade.DEFAULT.value
        ).order_by('?')[:MAX_AMOUNT_FOR_PREFERRED_DEFAULT_GRADE_PRIZES]

        epic_prize = cls.model.objects.filter(
            deleted=False,
            grade=Grade.EPIC.value
        ).first()

        legendary_prize = cls.model.objects.filter(
            deleted=False,
            grade=Grade.LEGENDARY.value
        ).first()

        # TODO по формуле Пуассона распределить для каждого приза номинал карточки
        # TODO учесть в выдаче, что карточки могут быть не открыты пользователем, причем их может быть выдано столько,
        #  что хватит на приз
        #  не нужно выдавать карточек больше чем есть призов в розыгрыше

        # пока рандомно определяем номинал карточек для каждого приза

        history_data = []  # Данные по истории

        # Обрабатываем обычные призы
        for default_prize in default_prizes:
            default_card = cls.get_random_card_for_prize(default_prize.id)
            if not default_card:
                continue
            history_data.append(
                PrizeCardsHistory(
                    card=default_card,
                    user_id=user_id,
                    bonuses_acquired=bonuses_acquired
                )
            )
            # Пересчитываем прогресс по призу
            # cls.recalc_prize_progress(user_id=user_id, prize_id=default_prize.id, value=default_card.value)

        # Обрабатываем эпичный приз
        if epic_prize:
            epic_card = cls.get_random_card_for_prize(epic_prize.id)
            if epic_card:
                history_data.append(
                    PrizeCardsHistory(
                        card=epic_card,
                        user_id=user_id,
                        bonuses_acquired=bonuses_acquired
                    )
                )
                # Пересчитываем прогресс по призу
                # cls.recalc_prize_progress(user_id=user_id, prize_id=epic_prize.id, value=epic_card.value)

        # Обрабатываем легендарный приз
        if legendary_prize:
            legendary_card = cls.get_random_card_for_prize(legendary_prize.id)
            if legendary_card:
                history_data.append(
                    PrizeCardsHistory(
                        card=legendary_card,
                        user_id=user_id,
                        bonuses_acquired=bonuses_acquired
                    )
                )
                # Пересчитываем прогресс по призу
                # cls.recalc_prize_progress(user_id=user_id, prize_id=legendary_prize.id, value=legendary_card.value)

        # Создаем записи для истории выдачи карточек
        PrizeCardsHistory.objects.bulk_create(history_data)

        # Автоматически открываем выданные ранее призовые карточки
        cls.auto_open_previous_batch_of_issued_cards(user_id, bonuses_acquired)

    @classmethod
    def auto_open_previous_batch_of_issued_cards(cls, user_id, bonuses_acquired):
        """
        Автоматически открыть предыдущие карточки, если выдана новая партия
        :param user_id:
        :param bonuses_acquired: всего начислено бонусов на момент выдачи последнего набора карточек
        :return:
        """
        previous_cards = PrizeCardsHistory.objects.filter(
            user_id=user_id,
            bonuses_acquired__lt=bonuses_acquired,  # Карточки из ранних пачек, когда полученных бонусов было меньше
            opened_at__isnull=True,  # не открывавшиеся карточки
            card__prize__deleted=False  # Приз не должен быть удален
        ).select_related('card')

        opened_cards_ids = []
        for pch in previous_cards:
            # Пересчитываем прогресс по призу
            cls.recalc_prize_progress(user_id=user_id, prize_id=pch.card.prize_id, value=pch.card.value)
            opened_cards_ids.append(pch.id)  # Добавляем ид истории для карточки

        if opened_cards_ids:
            # Обновляем историю карточек, ставим opened_at
            PrizeCardsHistory.objects.filter(pk__in=opened_cards_ids).update(
                updated_at=now(),
                opened_at=now()
            )


class TasksRepository(MasterRepository):
    model = Task

    def __init__(self, me=None) -> None:
        super().__init__()
        self.me = me

        if self.me:
            self.is_completed_expression = ExpressionWrapper(
                Exists(UserTask.objects.annotate(
                    allow_since_date=Case(
                        When(
                            task__period=TaskPeriod.WEEKLY.value,
                            then=ExpressionWrapper(
                                Trunc('created_at', 'week', output_field=DateField()) + timedelta(weeks=1),
                                output_field=DateField()
                            )
                        ),
                        default=ExpressionWrapper(
                            Trunc('created_at', 'day', output_field=DateField()) + timedelta(days=1),
                            output_field=DateField()
                        ),
                        output_field=DateField()
                    )
                ).filter(
                    deleted=False,
                    user_id=self.me.id,
                    task_id=OuterRef('pk'),
                    allow_since_date__gt=now().date()
                )),
                output_field=BooleanField()
            )

            # Основная часть запроса, содержащая вычисляемые поля
            self.base_query = self.model.objects.annotate(
                is_completed=self.is_completed_expression,
            )
        else:
            self.base_query = self.model.objects

    def inited_get_by_id(self, record_id):
        records = self.base_query.filter(pk=record_id).exclude(deleted=True)
        record = records.first()
        if not record:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден'
            )
        return record

    def inited_filter_by_kwargs(self, kwargs, paginator=None, order_by: list = None):
        if order_by:
            records = self.base_query.order_by(*order_by).exclude(deleted=True).filter(**kwargs)
        else:
            records = self.base_query.exclude(deleted=True).filter(**kwargs)
        return records[paginator.offset:paginator.limit] if paginator else records  # [:100]

    @staticmethod
    def get_user_last_task_completed(user_id, task_id):
        return UserTask.objects.filter(user_id=user_id, task_id=task_id, deleted=False).last()

    @staticmethod
    def complete_task(user_id, task_id):
        return UserTask.objects.create(user_id=user_id, task_id=task_id, deleted=False)

    @staticmethod
    def check_fulfilled_conditions(user_id, task, check_after_date=None):
        if task.kind == TaskKind.OPEN_APP.value:
            # Открытие приложения
            return True

        if task.kind == TaskKind.COMPLETE_SHIFT_WITH_MIN_RATING:
            # завершение смены с минимальным рейтингом

            # Найти завершенные смены после check_after_date
            # Для каждой завершенной смены высчитать полученный рейтинг
            # Сравнить рейтинг с величиной в задании
            finished_shifts_with_rating_needed = ShiftAppealsRepository.get_rated_completed_appeals_after_date(
                user_id=user_id, check_after_date=check_after_date, review_rating=task.actions_value
            )

            if finished_shifts_with_rating_needed:
                return True

        return False
