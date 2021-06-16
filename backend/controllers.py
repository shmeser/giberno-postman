from asgiref.sync import sync_to_async
from celery import group
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Case, When, CharField, F
from django.utils.timezone import now
from djangorestframework_camel_case.util import camelize
from fcm_django.models import FCMDevice
from loguru import logger

from app_users.enums import NotificationType, NotificationChannelFromAndroid8
from app_users.models import UserProfile, Notification
from backend.enums import Platform
from backend.tasks import async_send_push
from backend.utils import chunks, ArrayRemove, datetime_to_timestamp
from giberno.settings import FCM_MAX_DEVICES_PER_REQUEST


class PushController:

    def __init__(self, me=None) -> None:
        super().__init__()
        self.me = me

    def send_notification(
            self,
            users_to_send: [UserProfile],
            title,
            message,
            common_uuid,
            action,
            subject_id,
            notification_type,
            icon_type,
            **kwargs
    ):

        if not NotificationType.has_value(notification_type):
            # Если неизвестный тип уведомлений
            return

        users_to_send_queryset_sound, users_to_send_queryset_soundless = self.get_grouped_users_with_enabled_push(
            users_to_send=users_to_send,
            notification_type=notification_type
        )

        if users_to_send_queryset_sound:
            # Пуши со звуком
            self.process_notification_by_platform(
                users_to_send_queryset=users_to_send_queryset_sound,
                title=title,
                message=message,
                common_uuid=common_uuid,
                action=action,
                subject_id=subject_id,
                notification_type=notification_type,
                icon_type=icon_type,
                is_sound_enabled=True,
                **kwargs
            )

        if users_to_send_queryset_soundless:
            # Пуши без звука
            self.process_notification_by_platform(
                users_to_send_queryset=users_to_send_queryset_soundless,
                title=title,
                message=message,
                common_uuid=common_uuid,
                action=action,
                subject_id=subject_id,
                notification_type=notification_type,
                icon_type=icon_type,
                is_sound_enabled=False,  # Отключаем звук
                **kwargs
            )

    def send_message(
            self,
            users_to_send: [UserProfile],
            title,
            message,
            uuid,
            action,
            subject_id,
            notification_type,
            icon_type,
            **kwargs
    ):
        """ Отправка пуша как сообщения, без создания записи в бд """

        if not NotificationType.has_value(notification_type):
            # Если неизвестный тип уведомлений
            return

        users_to_send_queryset_sound, users_to_send_queryset_soundless = self.get_grouped_users_with_enabled_push(
            users_to_send=users_to_send,
            notification_type=notification_type
        )

        if users_to_send_queryset_sound:
            # Пуши со звуком
            self.process_message(
                users_to_send_queryset=users_to_send_queryset_sound,
                title=title,
                message=message,
                uuid=uuid,
                action=action,
                subject_id=subject_id,
                notification_type=notification_type,
                icon_type=icon_type,
                is_sound_enabled=True,
                **kwargs
            )

        if users_to_send_queryset_soundless:
            # Пуши без звука
            self.process_message(
                users_to_send_queryset=users_to_send_queryset_soundless,
                title=title,
                message=message,
                uuid=uuid,
                action=action,
                subject_id=subject_id,
                notification_type=notification_type,
                icon_type=icon_type,
                is_sound_enabled=False,  # Отключаем звук
                **kwargs
            )

    @staticmethod
    def get_grouped_users_with_enabled_push(users_to_send, notification_type):
        # Отфильтровываем по настройкам уведомлений у пользователей
        users_to_send_queryset_sound = UserProfile.objects.filter(pk__in=[u.id for u in users_to_send]).filter(
            notificationssettings__enabled_types__contains=[notification_type],
            notificationssettings__sound_enabled=True,  # Звук уведомлений включен в настройках
        )
        users_to_send_queryset_soundless = UserProfile.objects.filter(pk__in=[u.id for u in users_to_send]).filter(
            notificationssettings__enabled_types__contains=[notification_type],
            notificationssettings__sound_enabled=False,  # Звук уведомлений выключен в настройках
        )

        return users_to_send_queryset_sound, users_to_send_queryset_soundless

    @staticmethod
    def process_sound_parameters(is_sound_enabled, notification_type, kwargs):
        """ Обработка звуковых параметров """

        # ## Определение звуковых параметров пуша
        # is_sound_enabled берется из настроек пользователя
        if is_sound_enabled is True:
            sound = 'default'
            android_channel_id = NotificationChannelFromAndroid8[NotificationType(notification_type).name].value
        else:
            sound = None
            android_channel_id = NotificationChannelFromAndroid8[
                f'{NotificationType(notification_type).name}_SOUNDLESS'
            ].value

        # ## Переопределение параметров sound, android_channel_id из kwargs (могут быть посланы из тестового метода)
        if 'sound' in kwargs and 'android_channel_id' in kwargs:
            android_channel_id = kwargs.pop('android_channel_id')
            sound = kwargs.pop('sound')
            if sound is None:
                is_sound_enabled = False
        elif 'sound' in kwargs:
            sound = kwargs.pop('sound')
            if sound is None:
                is_sound_enabled = False
        elif 'android_channel_id' in kwargs:
            android_channel_id = kwargs.pop('android_channel_id')

        kwargs.update({
            'android_channel_id': android_channel_id
        })

        return sound, is_sound_enabled

    def process_notification_by_platform(
            self,
            users_to_send_queryset,
            title,
            message,
            common_uuid,
            action,
            subject_id,
            notification_type,
            icon_type,
            is_sound_enabled: bool,
            **kwargs
    ):
        """ Отправка пуша как оповещения, создание записи в бд """

        # Разделяем пуштокены iOS и Android, записываем в модель уведомления
        users_with_divided_tokens = FCMDevice.objects.filter(
            active=True,  # Только живые токены
            user__in=users_to_send_queryset  # Берем токены только отфиьтрованных пользователей
        ).values('user_id').annotate(
            devices=ArrayAgg('id'),  # Собираем ID токенов в
            ios=ArrayRemove(
                ArrayAgg(  # Группируем ios токены
                    Case(
                        When(
                            type=Platform.IOS.value,
                            then=F('registration_id')
                        ),
                        default=None,
                        output_field=CharField()
                    )
                ),
                None  # Удаляем null'ы из массива
            ),
            android=ArrayRemove(
                ArrayAgg(  # Группируем Android токены
                    Case(
                        When(
                            type=Platform.ANDROID.value,
                            then=F('registration_id')
                        ),
                        default=None,
                        output_field=CharField()
                    )
                ),
                None  # Удаляем null'ы из массива
            )
        )

        # Обрабатываем параметры звука
        sound, is_sound_enabled = self.process_sound_parameters(is_sound_enabled, notification_type, kwargs)

        devices_ids = []  # Список ID моделей пуш-токенов
        notifications_links = []  # Список объектов-связок для bulk_create

        for u in users_with_divided_tokens:
            devices_ids += u['devices']  # Добавляем список устройств пользователя в общий массив

            notifications_links.append(
                Notification(
                    uuid=common_uuid,
                    user_id=u['user_id'],
                    subject_id=subject_id,
                    title=title,
                    message=message,
                    type=notification_type,
                    action=action,
                    push_tokens_android=u['android'],
                    push_tokens_ios=u['ios'],
                    icon_type=icon_type,
                    sound_enabled=is_sound_enabled,
                )
            )

        Notification.objects.bulk_create(notifications_links)  # Массовое создание уведомлений

        # Все данные должны быть строками
        push_data = camelize({
            'uuid': str(common_uuid),
            'type': str(notification_type),
            'action': str(action),
            'icon_type': str(icon_type) if icon_type else '',
            'subject_id': str(subject_id) if subject_id else '',
            'title': str(title),
            'message': str(message),
            'created_at': str(datetime_to_timestamp(now()))
        })

        self.send_push(title, message, push_data, sound, devices_ids, **kwargs)

    def process_message(
            self,
            users_to_send_queryset,
            title,
            message,
            uuid,
            action,
            subject_id,
            notification_type,
            icon_type,
            is_sound_enabled: bool,
            **kwargs
    ):
        """ Отправка пуша как сообщения, без создания записи в бд """

        # Получаем только ид устройств с токенами
        devices_ids = FCMDevice.objects.filter(
            active=True,  # Только живые токены
            user__in=users_to_send_queryset  # Берем токены только отфиьтрованных пользователей
        ).values_list('id', flat=True)

        # Обрабатываем параметры звука
        sound, is_sound_enabled = self.process_sound_parameters(is_sound_enabled, notification_type, kwargs)

        # Все данные должны быть строками
        push_data = camelize({
            'type': str(notification_type),
            'action': str(action),
            'icon_type': str(icon_type) if icon_type else '',
            'subject_id': str(subject_id) if subject_id else '',
            'uuid': str(uuid),
            'title': str(title),
            'message': str(message),
            'created_at': str(datetime_to_timestamp(now()))
        })

        self.send_push(title, message, push_data, sound, devices_ids, **kwargs)

    @staticmethod
    def send_push(title, message, push_data, sound, devices_ids=[], **kwargs):

        # Разбиваем весь список на группы по FCM_MAX_DEVICES_PER_REQUEST штук
        devices_ids_chunked = chunks(devices_ids, FCM_MAX_DEVICES_PER_REQUEST)
        logger.info(
            f'>>>>\n'
            f'  SOUND {"ON" if sound else "OFF"}\n'
            f'  DEVICES COUNT {len(devices_ids)}\n'
            f'  CHUNKS COUNT {len(devices_ids_chunked)}\n'
            f'<<<<'
        )

        jobs = group(  # Создаем группы асинхронных задач
            [
                async_send_push.s(title, message, push_data, sound, ids_chunk, **kwargs) for ids_chunk in
                devices_ids_chunked
            ]
        )

        jobs.apply_async()


class AsyncPushController(PushController):
    @sync_to_async
    def send_message(
            self,
            users_to_send: [UserProfile],
            title,
            message,
            uuid,
            action,
            subject_id,
            notification_type,
            icon_type,
            **kwargs
    ):
        logger.info(
            f'ASYNC SEND MESSAGE [{title},{message},{action},{subject_id},{notification_type}]'
        )

        super().send_message(
            users_to_send,
            title,
            message,
            uuid,
            action,
            subject_id,
            notification_type,
            icon_type,
            **kwargs
        )
