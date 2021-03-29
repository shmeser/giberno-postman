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
            action,
            subject_id,
            notification_type,
            icon_type,
            **kwargs

    ):
        # Проверяем настройки оповещений для конкретного пользователя
        # Отфильтровываем по настройкам уведомлений у пользователей
        if NotificationType.has_value(notification_type):
            users_to_send_queryset_sound = UserProfile.objects.filter(pk__in=[u.id for u in users_to_send]).filter(
                notificationssettings__enabled_types__contains=[notification_type],
                notificationssettings__sound_enabled=True,  # Звук уведомлений включен в настройках
            )
            users_to_send_queryset_soundless = UserProfile.objects.filter(pk__in=[u.id for u in users_to_send]).filter(
                notificationssettings__enabled_types__contains=[notification_type],
                notificationssettings__sound_enabled=False,  # Звук уведомлений выключен в настройках
            )
        else:
            # Если неизвестный тип уведомлений
            return

        if users_to_send_queryset_sound:
            # Пуши со звуком
            self.process_notification_by_platform(
                users_to_send_queryset=users_to_send_queryset_sound,
                title=title,
                message=message,
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
                action=action,
                subject_id=subject_id,
                notification_type=notification_type,
                icon_type=icon_type,
                is_sound_enabled=False,  # Отключаем звук
                **kwargs
            )

    def process_notification_by_platform(
            self,
            users_to_send_queryset,
            title,
            message,
            action,
            subject_id,
            notification_type,
            icon_type,
            is_sound_enabled: bool,
            **kwargs
    ):
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

        # ## Определение звуковых параметров пуша
        # is_sound_enabled берется из настроек пользователя
        if is_sound_enabled is True:
            sound = 'default'
            kwargs.update({
                'android_channel_id': NotificationChannelFromAndroid8[NotificationType(notification_type).name].value
            })
        else:
            sound = None
            kwargs.update({
                'android_channel_id': NotificationChannelFromAndroid8[
                    f'{NotificationType(notification_type).name}_SOUNDLESS'
                ].value
            })

        devices_ids = []  # Список ID моделей пуш-токенов
        notifications_links = []  # Список объектов-связок для bulk_create

        for u in users_with_divided_tokens:
            devices_ids += u['devices']  # Добавляем список устройств пользователя в общий массив

            notifications_links.append(
                Notification(
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
            'type': str(notification_type),
            'action': str(action),
            'icon_type': str(icon_type),
            'subject_id': str(subject_id) if subject_id else '',
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
