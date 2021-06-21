import uuid

from celery import shared_task

from app_market.versions.v1_0.repositories import ShiftAppealsRepository
from app_sockets.controllers import SocketController
from app_users.enums import NotificationAction, NotificationType, NotificationIcon
from backend.controllers import PushController

_CANCELED_APPEAL_TITLE = 'Отклик на смену отменен'
_JOB_SOON_TITLE = 'Смена скоро начнется'
_WAITING_COMPLETION_TITLE = 'Смена ожидает завершения'
_COMPLETED_APPEAL_TITLE = 'Смена успешно завершена'


@shared_task
def update_appeals():
    canceled_appeals = ShiftAppealsRepository().bulk_cancel()
    for a in canceled_appeals:
        icon_type = NotificationIcon.WORKER_CANCELED_VACANCY.value
        title = _CANCELED_APPEAL_TITLE
        message = f'К сожалению, ваш отклик на вакансию {a.shift.vacancy.title} был отменен автоматически, так как не был подтвержден до начала смены.'
        send_notification_and_socket_event_on_appeal(
            appeal=a,
            users_to_send=[a.applier],
            sockets=a.applier.sockets_array or [],
            title=title,
            message=message,
            icon_type=icon_type
        )

    canceled_job_soon_appeals = ShiftAppealsRepository().bulk_cancel_with_job_soon_status()
    for a in canceled_job_soon_appeals:
        icon_type = NotificationIcon.WORKER_CANCELED_VACANCY.value
        title = _CANCELED_APPEAL_TITLE
        message = f'К сожалению, ваш отклик на вакансию {a.shift.vacancy.title} был отменен автоматически, так как не был отсканирован код.'
        send_notification_and_socket_event_on_appeal(
            appeal=a,
            users_to_send=[a.applier],
            sockets=a.applier.sockets_array or [],
            title=title,
            message=message,
            icon_type=icon_type
        )

    job_soon_appeals = ShiftAppealsRepository().bulk_set_job_soon_status()
    for a in job_soon_appeals:
        icon_type = NotificationIcon.SHIFT_START_SOON.value
        title = _JOB_SOON_TITLE
        message = f'Скоро начало смены по вакансии {a.shift.vacancy.title}.'
        send_notification_and_socket_event_on_appeal(
            appeal=a,
            users_to_send=[a.applier],
            sockets=a.applier.sockets_array or [],
            title=title,
            message=message,
            icon_type=icon_type
        )

    # TODO добавить оповещение для менеджеров
    waiting_completion = ShiftAppealsRepository().bulk_set_waiting_for_completion_status()
    for a in waiting_completion:
        icon_type = NotificationIcon.DEFAULT.value
        title = _WAITING_COMPLETION_TITLE
        message = f'Смена по вакансии {a.shift.vacancy.title} ожидает завершения.'
        send_notification_and_socket_event_on_appeal_with_managers(
            appeal=a,
            title=title,
            message=message,
            icon_type=icon_type
        )

    # TODO добавить оповещение для менеджеров
    completed_appeals = ShiftAppealsRepository().bulk_set_job_completed_status()
    for a in completed_appeals:
        icon_type = NotificationIcon.DEFAULT.value
        title = _COMPLETED_APPEAL_TITLE
        message = f'Смена по вакансии {a.shift.vacancy.title} успешно завершена.'
        send_notification_and_socket_event_on_appeal_with_managers(
            appeal=a,
            title=title,
            message=message,
            icon_type=icon_type
        )

    ShiftAppealsRepository().bulk_set_completed_status()


def send_notification_and_socket_event_on_appeal_with_managers(appeal, title, message, icon_type):
    users_to_send = []

    applier_sockets = appeal.applier.sockets_array or []
    managers_sockets = []

    if appeal.shift.vacancy.shop.relevant_managers:
        for m in appeal.shift.vacancy.shop.relevant_managers:
            managers_sockets += m.sockets_array
            users_to_send.append(m)

    sockets = managers_sockets + applier_sockets  # Объединяем все сокеты
    users_to_send.append(appeal.applier)  # Добавляем заявителя

    send_notification_and_socket_event_on_appeal(
        appeal=appeal,
        users_to_send=users_to_send,
        sockets=sockets,
        title=title,
        message=message,
        icon_type=icon_type
    )


def send_notification_and_socket_event_on_appeal(appeal, users_to_send, sockets, title, message, icon_type):
    SocketController().send_message_to_many_connections(sockets, {
        'type': 'appeal_job_status_updated',
        'prepared_data': {
            'id': appeal.id,
            'jobStatus': appeal.job_status,
        }
    })

    action = NotificationAction.SHIFT.value
    subject_id = appeal.shift_id
    notification_type = NotificationType.SYSTEM.value

    # uuid для массовой рассылки оповещений,
    # у пользователей в бд будут созданы оповещения с одинаковым uuid
    # uuid необходим на клиенте для фильтрации одинаковых данных, полученных по 2 каналам - сокеты и пуши
    common_uuid = uuid.uuid4()

    PushController().send_notification(
        users_to_send=users_to_send,
        title=title,
        message=message,
        common_uuid=common_uuid,
        action=action,
        subject_id=subject_id,
        notification_type=notification_type,
        icon_type=icon_type
    )

    # Отправка уведомления по сокетам
    SocketController(version='1.0').send_notification_to_many_connections(sockets, {
        'title': title,
        'message': message,
        'uuid': str(common_uuid),
        'action': action,
        'subjectId': subject_id,
        'notificationType': notification_type,
        'iconType': icon_type,
    })
