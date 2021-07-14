from channels.db import database_sync_to_async
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.db.models import Q, Prefetch, Subquery, OuterRef, FloatField, Window, Avg, F, \
    Value
from django.db.models.functions import DenseRank
from django.utils.timezone import now
from fcm_django.models import FCMDevice
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import RefreshToken

from app_feedback.models import Review
from app_geo.models import Region
from app_market.enums import ShiftAppealStatus
from app_market.models import Shift, ShiftAppeal
from app_media.enums import MediaType, MediaFormat
from app_media.models import MediaModel
from app_media.versions.v1_0.repositories import MediaRepository
from app_users.entities import JwtTokenEntity, SocialEntity
from app_users.enums import AccountType, NotificationType
from app_users.models import SocialModel, UserProfile, JwtToken, NotificationsSettings, Notification, UserCareer, \
    Document, Card, UserMoney
from app_users.utils import validate_username, generate_username, generate_password, EmailSender
from backend.entity import Error
from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.exceptions import EntityDoesNotExistException
from backend.errors.http_exceptions import HttpException, CustomException
from backend.mappers import DataMapper
from backend.mixins import MasterRepository
from backend.repositories import BaseRepository
from backend.utils import is_valid_uuid, make_hash_and_salt


class UsersRepository:
    @staticmethod
    def get_reference_user(reference_code):
        return UserProfile.objects.filter(uuid__icontains=reference_code, deleted=False).first()


class AuthRepository:

    @staticmethod
    def social_registration(social, social_data, defaults, account_type):
        user, created = UserProfile.objects.get_or_create(socialmodel=social, defaults=defaults)

        if created:
            # Привязываем пользователя к соцсети
            social.user = user
            social.is_for_reg = True
            social.save()
            user.email = social_data.email

            # Создаем модель настроек для уведомлений
            NotificationsSettings.objects.create(
                user=user,
                enabled_types=[NotificationType.SYSTEM]
            )
        else:
            # Если ранее уже создан аккаунт и при регистрации указан другой тип аккаунта
            if user.account_type != account_type:
                raise HttpException(
                    detail=ErrorsCodes.ALREADY_REGISTERED_WITH_OTHER_ROLE.value,
                    status_code=RESTErrors.FORBIDDEN
                )

            # Подставляем имеил с соцсети, если его нет
            user.email = social_data.email if not user.email and social_data.email else user.email
            # Подставляем телефон из соцсети всегда
            user.phone = social_data.phone if social_data.phone else user.phone

        user.save()

        return user, created

    @staticmethod
    def social_attaching(social, social_data, base_user):
        user = UserProfile.objects.filter(socialmodel=social).first()

        if user is not None:
            # Пользователь для соцсети найден

            if user.id != base_user.id:
                raise HttpException(
                    detail=ErrorsCodes.SOCIAL_ALREADY_IN_USE.value,
                    status_code=RESTErrors.FORBIDDEN
                )
            # Найден свой аккаунт
            # Подставляем имеил с соцсети, если его нет
            user.email = social_data.email if not user.email and social_data.email else user.email
            # Подставляем телефон из соцсети всегда
            user.phone = social_data.phone if social_data.phone else user.phone

            user.save()

            result = user

        else:
            # Пользователь для соцсети не найден

            # Привязываем ооцсеть к своему base_user
            social.user = base_user
            social.save()

            # Подставляем имеил с соцсети, если его нет
            base_user.email = social_data.email if not base_user.email and social_data.email else base_user.email
            # Подставляем телефон из соцсети всегда
            base_user.phone = social_data.phone if social_data.phone else base_user.phone

            base_user.save()

            result = base_user

        return result

    @classmethod
    def get_or_create_social_user(cls, social_data: SocialEntity, account_type=AccountType.SELF_EMPLOYED,
                                  base_user: UserProfile = None):

        # Получаем способ авторизации
        social, social_created = SocialModel.objects.get_or_create(
            social_id=social_data.social_id, type=social_data.social_type, defaults=social_data.get_kwargs()
        )

        # Получаем или создаем пользователя
        defaults = {
            'phone': social_data.phone,
            'first_name': social_data.first_name,
            'last_name': social_data.last_name,
            'middle_name': social_data.middle_name
        }

        # Проверка типа аккаунта, отсылаемого при авторизации
        if account_type is not None and AccountType.has_value(account_type):
            defaults['account_type'] = account_type

        if base_user is None or base_user.is_anonymous:
            # Если запрос пришел без авторизации (регистрация и содание аккаунта через соцсеть)
            result, created = cls.social_registration(social, social_data, defaults, account_type)

        else:
            # Если происходит привязка соцсети к аккаунту
            created = False
            result = cls.social_attaching(social, social_data, base_user)

        return result, created


class SocialsRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__(SocialModel)

    @staticmethod
    def create(**kwargs):
        return SocialModel.objects.create(**kwargs)


class JwtRepository:
    def __init__(self, headers=None):
        self.app_version = headers['App'] if headers and 'App' in headers else None
        self.platform_name = headers['Platform'] if headers and 'Platform' in headers else None
        self.vendor = headers['Vendor'] if headers and 'Vendor' in headers else None

    @classmethod
    def get_or_create_jwt_token(cls, user: UserProfile):
        try:
            return cls.get_jwt_token(user)
        except EntityDoesNotExistException:
            return cls().create_jwt_token(user)

    def create_jwt_token(self, user: UserProfile):
        refresh = RefreshToken.for_user(user)

        refresh_token = str(refresh)
        access_token = str(refresh.access_token)

        return JwtToken.objects.create(
            user=user, access_token=access_token, refresh_token=refresh_token, app_version=self.app_version,
            platform_name=self.platform_name, vendor=self.vendor
        )

    @staticmethod
    def get_jwt_token(user: UserProfile):
        try:
            return JwtToken.objects.get(user=user)
        except JwtToken.DoesNotExist:
            raise EntityDoesNotExistException()

    @staticmethod
    def remove_old(user):
        JwtToken.objects.filter(**{'user_id': user.id}).delete()

    @staticmethod
    def refresh(refresh_token, new_access_token):
        # TODO нужно доработать, если потребуется ROTATE_REFRESH_TOKENS=True и BLACKLIST_AFTER_ROTATION=True
        pair = JwtToken.objects.filter(**{'refresh_token': refresh_token}).first()
        if pair:
            pair.access_token = new_access_token
            pair.save()

        return pair

    def create_jwt_pair(self, user, lifetime=None):
        refresh = RefreshToken.for_user(user)

        refresh_token = str(refresh)
        access_token = refresh.access_token
        if lifetime:
            access_token.set_exp(lifetime=lifetime)

        return JwtToken.objects.create(
            **JwtTokenEntity(
                user, str(access_token), refresh_token, self.app_version, self.platform_name, self.vendor
            ).get_kwargs()
        )

    @staticmethod
    def get_user(token):
        try:
            return JwtToken.objects.get(access_token=token).user
        except JwtToken.DoesNotExist:
            raise EntityDoesNotExistException()

    @staticmethod
    def get_jwt_pair(user):
        refresh = RefreshToken.for_user(user)

        refresh_token = str(refresh)
        access_token = str(refresh.access_token)

        return JwtToken.objects.create(**JwtTokenEntity(user, access_token, refresh_token).get_kwargs())


class AsyncJwtRepository(JwtRepository):
    def __init__(self) -> None:
        super().__init__()

    @database_sync_to_async
    def get_user(self, token):
        return super().get_user(token)


class ProfileRepository(MasterRepository):
    model = UserProfile

    def __init__(self, me=None) -> None:
        super().__init__()
        self.me = me

    def create_manager_by_admin(self, validated_data):
        data_to_create_user = {
            'username': generate_username(),
            'account_type': AccountType.MANAGER,
            'reg_reference': self.me,
            'email': validated_data.get('email'),
            'phone': validated_data.get('phone'),
            'first_name': validated_data.get('first_name'),
            'middle_name': validated_data.get('middle_name'),
            'last_name': validated_data.get('last_name')
        }

        user = self.create(**data_to_create_user)
        password = generate_password()
        user.set_password(password)
        distributors = validated_data.get('distributors')
        shops = validated_data.get('shops')

        user.distributors.set(distributors)
        user.shops.set(shops)
        user.save()
        NotificationsSettings.objects.create(
            user=user,
            enabled_types=[NotificationType.SYSTEM]
        )
        EmailSender(user=user, password=password).send_account_credentials(subject='Создана учетная запись менеджера')
        return user

    def create_security_by_admin(self, data):
        username = generate_username()
        password = generate_password()

        data_to_create_user = {
            'username': username,
            'account_type': AccountType.SECURITY.value,
            'reg_reference': self.me,
        }

        user = self.create(**data_to_create_user)
        user.set_password(password)
        distributors = data.get('distributors')
        shops = data.get('shops')

        user.distributors.set(distributors)
        user.shops.set(shops)
        user.save()

        NotificationsSettings.objects.create(
            user=user,
            enabled_types=[NotificationType.SYSTEM.value]
        )

        return username, password

    def get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id, is_staff=False)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден'
            )

    def get_by_id_and_type(self, record_id, account_type):
        return self.model.objects.filter(id=record_id, account_type=account_type).first()

    def get_by_username(self, username):
        username = username.lower()
        try:
            return self.model.objects.get(username=username)
        except self.model.DoesNotExist:
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.USERNAME_WRONG))
            ])

    def get_by_username_and_password(self, validated_data):
        user = self.get_by_username(username=validated_data['username'].lower())
        if not user.check_password(validated_data['password']):
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.WRONG_PASSWORD))
            ])
        return user

    def update_location(self, data):
        point = DataMapper.geo_point(data)
        self.me.location = point
        self.me.save()
        return self.me

    def update_username(self, username):
        username = validate_username(username=username)
        if self.me.username == username:
            return

        taken = self.model.objects.filter(username=username)
        if taken.count():
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.USERNAME_TAKEN))
            ])

        self.me.username = username
        self.me.save()

    @staticmethod
    def recalculate_rating_place_for_users():
        user_ct = ContentType.objects.get_for_model(UserProfile)
        updated_ratings = UserProfile.objects.filter(  # Фильтруем смз, только с оценками
            reviews__isnull=False,
        ).annotate(
            total_rating=Subquery(
                Review.objects.filter(  # Собираем общий рейтинг
                    target_id=OuterRef('id'),
                    target_ct=user_ct,
                ).annotate(
                    rating=Window(  # Приходится использовать оконные функции из-за сложной структуры оценок и задачи
                        expression=Avg('value'), partition_by=[F('target_id')]
                    )
                ).values('rating')[:1]
            )
        ).distinct().annotate(
            place=Window(
                # Проставляем место (ранг) по убыванию рейтинга
                expression=DenseRank(), order_by=F('total_rating').desc()
            )
        ).order_by('-total_rating')

        # Обновляем место в общем рейтинге для всех пользователей
        sql = f'''
            WITH 

            updated_rating AS (
                {updated_ratings.query}
            ),

            joined_ratings AS (
                SELECT 
                    p.id, 
                    ur.place,
                    ur.total_rating
                FROM app_users__profiles p 
                LEFT JOIN updated_rating ur ON p.id=ur.id
                WHERE 
                    p.account_type={AccountType.SELF_EMPLOYED.value}
            )

            UPDATE app_users__profiles p 
            SET 
                rating_place=jr.place,
                rating_value=jr.total_rating
            FROM joined_ratings jr
            WHERE 
                p.id=jr.id
        '''

        with connection.cursor() as c:
            c.execute(sql)  # Update запросы выполняются через cursor

    def make_review_to_self_employed_by_admin_or_manager(self, user_id, shift_id, text, value, point=None):
        # TODO добавить загрузку attachments

        owner_content_type = ContentType.objects.get_for_model(self.me)
        owner_ct_id = owner_content_type.id
        owner_ct_name = owner_content_type.model
        owner_id = self.me.id

        target_content_type = ContentType.objects.get_for_model(self.model)
        target_ct_id = target_content_type.id
        target_ct_name = target_content_type.model
        target_id = user_id

        # проверяем валидность id конечной цели
        applier = self.get_by_id(record_id=target_id)

        if applier.account_type != AccountType.SELF_EMPLOYED:
            raise PermissionDenied()

        # проверка связи между магазином, сменой и менеджером
        try:
            shift = Shift.objects.get(id=shift_id)
        except Shift.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {Shift._meta.verbose_name} с ID={shift_id} не найден'
            )

        appeal = ShiftAppeal.objects.filter(
            deleted=False,
            shift=shift,
            applier=applier,
            status__in=[ShiftAppealStatus.CONFIRMED.value, ShiftAppealStatus.COMPLETED.value]
        ).first()

        shop = shift.vacancy.shop

        if shop not in self.me.shops.all():
            raise PermissionDenied()

        if not appeal:
            raise PermissionDenied()

        region = Region.objects.filter(boundary__covers=point).first() if point else None

        if not Review.objects.filter(
                owner_ct_id=owner_ct_id,
                owner_id=owner_id,
                target_ct_id=target_ct_id,
                target_id=target_id,
                shift=shift,
                deleted=False
        ).exists():
            Review.objects.create(
                owner_ct_id=owner_ct_id,
                owner_id=owner_id,
                owner_ct_name=owner_ct_name,

                target_ct_id=target_ct_id,
                target_id=target_id,
                target_ct_name=target_ct_name,

                value=value,
                text=text,
                region=region,
                shift=shift
            )

            # пересчитываем место в общем рейтинге для всех пользователей
            self.recalculate_rating_place_for_users()


class AsyncProfileRepository(ProfileRepository):
    def __init__(self, me=None) -> None:
        super().__init__()
        self.me = me

    @database_sync_to_async
    def get_by_id(self, record_id):
        return super().get_by_id(record_id)

    @database_sync_to_async
    def update_location(self, event):
        super().__init__(self.me)
        return super().update_location(event)


class NotificationsRepository(MasterRepository):
    model = Notification

    def __init__(self, me=None) -> None:
        super().__init__()
        self.me = me

    def get_by_id(self, record_id):
        record = self.model.objects.filter(id=record_id)
        record = self.fast_related_loading(record).first()
        if not record:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден')
        return record

    def filter_by_kwargs(self, kwargs, paginator=None, order_by: list = None):
        try:
            if order_by:
                records = self.model.objects.order_by(*order_by).exclude(deleted=True).filter(**kwargs)
            else:
                records = self.model.objects.exclude(deleted=True).filter(**kwargs)
        except Exception:  # no 'deleted' field
            if order_by:
                records = self.model.objects.order_by(*order_by).filter(**kwargs)
            else:
                records = self.model.objects.filter(**kwargs)

        return self.fast_related_loading(  # Предзагрузка связанных сущностей
            queryset=records[paginator.offset:paginator.limit] if paginator else records,
        )

    @staticmethod
    def fast_related_loading(queryset, point=None):
        """ Подгрузка зависимостей с 3 уровнями вложенности по ForeignKey + GenericRelation
             Media
        """
        queryset = queryset.prefetch_related(
            # Подгрузка медиа для магазинов
            Prefetch(
                'media',
                queryset=MediaModel.objects.filter(
                    deleted=False,
                    type=MediaType.NOTIFICATION_ICON.value,
                    owner_ct_id=ContentType.objects.get_for_model(Notification).id,
                    format=MediaFormat.IMAGE.value
                ),
                to_attr='medias'
            )
        )

        return queryset

    def get_unread_notifications_count(self):
        return self.model.objects.filter(user=self.me, read_at__isnull=True).count()


class AsyncNotificationsRepository(NotificationsRepository):
    def __init__(self, me=None) -> None:
        super().__init__()
        self.me = me

    @database_sync_to_async
    def get_unread_notifications_count(self):
        return super().get_unread_notifications_count()


class FCMDeviceRepository(MasterRepository):
    model = FCMDevice


class NotificationsSettingsRepository(MasterRepository):
    model = NotificationsSettings


class CareerRepository(MasterRepository):
    model = UserCareer


class DocumentsRepository(MasterRepository):
    model = Document

    def update_media(self, instance, files_uuid, me):
        if files_uuid is not None and isinstance(files_uuid, list):  # Обрабатываем только массив
            try:
                # Отфильтровываем невалидные uuid
                files_uuid = list(filter(lambda x: is_valid_uuid(x), files_uuid))

                user_ct = ContentType.objects.get_for_model(me)
                document_ct = ContentType.objects.get_for_model(instance)
                # Получаем массив uuid всех прикрепленных к документу файлов

                # Получаем массив uuid файлов которые прикреплены к документу но не пришли в списке прикрепляемых
                # и перепривязываем их к обратно пользователю (или удаляем)
                instance.media \
                    .all() \
                    .exclude(uuid__in=files_uuid) \
                    .update(deleted=True)

                # Получаем из бд массив загруженных файлов, которые нужно прикрепить к документу
                # Получаем список файлов

                # Находим список всех прикрепленных файлов
                # Добавляем или обновляем языки пользователя
                MediaRepository().filter(
                    Q(uuid__in=files_uuid, owner_ct=document_ct, owner_id=instance.id) |
                    Q(uuid__in=files_uuid, owner_ct=user_ct, owner_id=me.id)
                ).update(
                    updated_at=now(),
                    owner_ct=document_ct,
                    owner_ct_name=document_ct.model,
                    owner_id=instance.id
                )
            except Exception as e:
                raise CustomException(errors=[
                    dict(Error(ErrorsCodes.UNSUPPORTED_FILE_FORMAT, **{'detail': str(e)}))
                ])


class RatingRepository(MasterRepository):
    model = UserProfile

    def __init__(self, me=None) -> None:
        super().__init__()
        self.me = me

    def get_kwargs_for_reviews(self, kwargs):
        m_kwargs = kwargs.copy()
        for k in m_kwargs.keys():
            try:
                new_key = k.replace('reviews__', '')
                m_kwargs[new_key] = m_kwargs.pop(k)
            except:
                pass

        return m_kwargs

    def get_users_rating(self, kwargs, paginator=None):
        user_ct = ContentType.objects.get_for_model(UserProfile)
        kwargs_for_reviews = self.get_kwargs_for_reviews(kwargs)
        records = self.model.objects.filter(  # Фильтруем смз по нужным параметрам (регион оценки, смена, дата)
            reviews__isnull=False,
            **kwargs
        ).annotate(
            total_rating=Subquery(
                Review.objects.filter(  # Собираем рейтинг по тем же парамерам
                    target_id=OuterRef('id'),
                    target_ct=user_ct,
                    **kwargs_for_reviews  # Измененные kwargs, так как тут модель не UserProfile, а Review
                ).annotate(
                    rating=Window(  # Приходится использовать оконные функции из-за сложной структуры оценок и задачи
                        expression=Avg('value'), partition_by=[F('target_id')]
                    )
                ).values('rating')[:1]
            )
        ).distinct().annotate(
            place=Window(
                # Проставляем место (ранг) по убыванию рейтинга
                expression=DenseRank(), order_by=F('total_rating').desc()
            )
        ).order_by('-total_rating')
        # TODO префетчить аватарки
        return records[paginator.offset:paginator.limit] if paginator else records

    def get_my_rating(self, kwargs):
        user_ct = ContentType.objects.get_for_model(UserProfile)
        kwargs_for_reviews = self.get_kwargs_for_reviews(kwargs)
        queryset = self.model.objects.filter(  # Фильтруем смз по нужным параметрам (регион оценки, смена, дата)
            reviews__isnull=False,
            **kwargs
        ).annotate(
            total_rating=Subquery(
                Review.objects.filter(  # Собираем рейтинг по тем же парамерам
                    target_id=OuterRef('id'),
                    target_ct=user_ct,
                    **kwargs_for_reviews  # Измененные kwargs, так как тут модель не UserProfile? а Review
                ).annotate(
                    rating=Window(  # Приходится использовать оконные функции из-за сложной структуры оценок и задачи
                        expression=Avg('value'), partition_by=[F('target_id')]
                    )
                ).values('rating')[:1]
            )
        ).distinct().annotate(
            place=Window(
                # Проставляем место (ранг) по убыванию рейтинга
                expression=DenseRank(), order_by=F('total_rating').desc()
            )
        )

        # Берем общий рейтинг для использования в WITH блоке
        sql, params = queryset.query.sql_with_params()  # Разбиваем его на параметризованный SQL и параметры
        final_params = params + (self.me.id,)  # Добавляем в параметры свой ид
        # Создаем итоговый SQL
        final_sql = f'''
            WITH ratings AS ({sql})
            
            SELECT * FROM ratings WHERE id=%s LIMIT 1
            '''

        records = self.model.objects.raw(final_sql, final_params)  # Выполняем RAW запрос с параметрами

        my_profile = None
        for record in records:
            my_profile = record
            break

        if not my_profile:  # Если нет рейтинга по своему профилю, то проставляем null
            my_profile = UserProfile.objects.filter(id=self.me.id).annotate(
                place=Value(None, output_field=FloatField()),
                total_rating=Value(None, output_field=FloatField())
            ).first()

        return my_profile


class CardsRepository(MasterRepository):
    model = Card

    def __init__(self, me=None) -> None:
        super().__init__()
        self.me = me
        self.base_query = self.model.objects.filter(user=self.me)

    def inited_get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id, user=self.me, deleted=False)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден'
            )

    def get_my_cards(self, paginator=None, order_by: list = None):
        records = self.base_query.filter(deleted=False)
        if order_by:
            records = records.order_by(*order_by)
        if paginator:
            return records[paginator.offset:paginator.limit]
        return records

    def add_card(self, real_pan, data):
        hashed_pan, salt = make_hash_and_salt(value=real_pan, salt_base=data.get('pan'))
        card, created = self.model.objects.get_or_create(
            hash=hashed_pan,
            deleted=False,
            defaults={
                'user': self.me,
                'pan': data.get('pan'),
                'valid_through': data.get('valid_through'),
                'type': data.get('type'),
                'payment_network': data.get('payment_network'),
                'issuer': data.get('issuer'),
                'salt': salt
            }
        )

        if not created and card.user != self.me:
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.CARD_ALREADY_USED_IN_OTHER_ACCOUNT))
            ])

        # TODO возможно будет только 1 карта
        if created:
            # Удаляем все остальные карты
            self.me.cards.exclude(pk=card.id).update(deleted=True, updated_at=now())

        return card


class MoneyRepository(MasterRepository):
    model = UserMoney

    def __init__(self, me=None) -> None:
        super().__init__()
        self.me = me

    def get_my_money(self):
        return UserMoney.objects.filter(user=self.me)
