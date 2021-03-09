from celery import group
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Case, When, CharField, F
from django.utils.timezone import now
from djangorestframework_camel_case.util import camelize
from fcm_django.models import FCMDevice

from app_users.enums import NotificationType
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
            icon_type
    ):
        # Проверяем настройки оповещений для конкретного пользователя
        users_to_send_queryset = UserProfile.objects.filter(pk__in=[u.id for u in users_to_send])

        # Отфильтровываем по настройкам уведомлений у пользователей
        if notification_type == NotificationType.SYSTEM.value:
            users_to_send_queryset = users_to_send_queryset.filter(
                notificationssettings__enabled_types__contains=[notification_type]
            )

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
                    icon_type=icon_type
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

        self.send_push(title, message, push_data, devices_ids)

    @staticmethod
    def send_push(title, message, push_data, devices_ids=[]):

        print('>>>> DEVICES COUNT', len(devices_ids))

        # Разбиваем весь список на группы по FCM_MAX_DEVICES_PER_REQUEST штук
        devices_ids_chunked = chunks(devices_ids, FCM_MAX_DEVICES_PER_REQUEST)
        print('>>>> DEVICES CHUNKS COUNT', len(devices_ids_chunked))

        jobs = group(  # Создаем группы асинхронных задач
            [async_send_push.s(title, message, push_data, ids_chunk) for ids_chunk in devices_ids_chunked]
        )

        jobs.apply_async()
