import uuid

from celery import shared_task

from app_market.utils import send_socket_event_on_appeal_statuses
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
    """ Проверка откликов """

    """ Отмена неподтвержденных откликов """
    canceled_appeals = ShiftAppealsRepository().bulk_cancel()
    for a in canceled_appeals:
        applier_sockets, managers_sockets, users_to_send = ShiftAppealsRepository.get_self_employed_and_managers_with_sockets(
            appeal=a
        )
        send_socket_event_on_appeal_statuses(
            appeal=a, applier_sockets=applier_sockets, managers_sockets=managers_sockets
        )

        icon_type = NotificationIcon.WORKER_CANCELED_VACANCY.value
        title = _CANCELED_APPEAL_TITLE
        message = f'К сожалению, ваш отклик на вакансию {a.shift.vacancy.title} был отменен автоматически, так как не был подтвержден до начала смены.'
        send_notification_on_appeal(
            appeal=a,
            users_to_send=[a.applier],
            sockets=applier_sockets,
            title=title,
            message=message,
            icon_type=icon_type
        )

    """ Отмена откликов со статусом "работа скоро" """
    canceled_job_soon_appeals = ShiftAppealsRepository().bulk_cancel_with_job_soon_status()
    for a in canceled_job_soon_appeals:
        applier_sockets, managers_sockets, users_to_send = ShiftAppealsRepository.get_self_employed_and_managers_with_sockets(
            appeal=a
        )
        send_socket_event_on_appeal_statuses(
            appeal=a, applier_sockets=applier_sockets, managers_sockets=managers_sockets
        )

        icon_type = NotificationIcon.WORKER_CANCELED_VACANCY.value
        title = _CANCELED_APPEAL_TITLE
        message = f'К сожалению, ваш отклик на вакансию {a.shift.vacancy.title} был отменен автоматически, так как не был отсканирован код.'
        send_notification_on_appeal(
            appeal=a,
            users_to_send=[a.applier],
            sockets=applier_sockets,
            title=title,
            message=message,
            icon_type=icon_type
        )

    """ Новый job-статус "работа скоро" для откликов """
    job_soon_appeals = ShiftAppealsRepository().bulk_set_job_soon_status()
    for a in job_soon_appeals:
        applier_sockets, managers_sockets, users_to_send = ShiftAppealsRepository.get_self_employed_and_managers_with_sockets(
            appeal=a
        )
        send_socket_event_on_appeal_statuses(
            appeal=a, applier_sockets=applier_sockets, managers_sockets=managers_sockets
        )

        icon_type = NotificationIcon.SHIFT_START_SOON.value
        title = _JOB_SOON_TITLE
        message = f'Скоро начало смены по вакансии {a.shift.vacancy.title}.'
        send_notification_on_appeal(
            appeal=a,
            users_to_send=[a.applier],
            sockets=applier_sockets,
            title=title,
            message=message,
            icon_type=icon_type
        )

    """ Новый job-статус "ожидает завершения" для откликов """
    waiting_completion = ShiftAppealsRepository().bulk_set_waiting_for_completion_status()
    for a in waiting_completion:
        applier_sockets, managers_sockets, users_to_send = ShiftAppealsRepository.get_self_employed_and_managers_with_sockets(
            appeal=a
        )
        send_socket_event_on_appeal_statuses(
            appeal=a, applier_sockets=applier_sockets, managers_sockets=managers_sockets
        )

        icon_type = NotificationIcon.DEFAULT.value
        title = _WAITING_COMPLETION_TITLE
        message = f'Смена по вакансии {a.shift.vacancy.title} ожидает завершения.'

        sockets = applier_sockets + managers_sockets
        send_notification_on_appeal(
            appeal=a,
            users_to_send=users_to_send,
            sockets=sockets,
            title=title,
            message=message,
            icon_type=icon_type
        )

    """ Новый job-статус "завершен" для откликов """
    completed_job_appeals = ShiftAppealsRepository().bulk_set_job_completed_status()
    for a in completed_job_appeals:
        applier_sockets, managers_sockets, users_to_send = ShiftAppealsRepository.get_self_employed_and_managers_with_sockets(
            appeal=a
        )
        send_socket_event_on_appeal_statuses(
            appeal=a, applier_sockets=applier_sockets, managers_sockets=managers_sockets
        )

        icon_type = NotificationIcon.DEFAULT.value
        title = _COMPLETED_APPEAL_TITLE
        message = f'Смена по вакансии {a.shift.vacancy.title} успешно завершена.'

        sockets = applier_sockets + managers_sockets
        send_notification_on_appeal(
            appeal=a,
            users_to_send=users_to_send,
            sockets=sockets,
            title=title,
            message=message,
            icon_type=icon_type
        )

    """ Новый статус "завершен" для откликов """
    # По истечении 15 минут после завершения работы, окончательно закрываем смену
    completed_appeals = ShiftAppealsRepository().bulk_set_completed_status()
    for a in completed_appeals:
        applier_sockets, managers_sockets, users_to_send = ShiftAppealsRepository.get_self_employed_and_managers_with_sockets(
            appeal=a
        )
        send_socket_event_on_appeal_statuses(
            appeal=a, applier_sockets=applier_sockets, managers_sockets=managers_sockets
        )

    """ Новый статус "отменен" и job-статус "уволен" для откликов """
    _FIRED_APPEAL_TITLE = 'Вы уволены'
    fired_appeals = ShiftAppealsRepository().fire_pending_appeals()
    for a in fired_appeals:
        applier_sockets, managers_sockets, users_to_send = ShiftAppealsRepository.get_self_employed_and_managers_with_sockets(
            appeal=a
        )
        send_socket_event_on_appeal_statuses(
            appeal=a, applier_sockets=applier_sockets, managers_sockets=managers_sockets
        )

        icon_type = NotificationIcon.WORKER_CANCELED_VACANCY.value
        title = _FIRED_APPEAL_TITLE
        message = f'К сожалению, вы были уволены. Ваша работа по вакансии {a.shift.vacancy.title} не будет оплачена.'
        send_notification_on_appeal(
            appeal=a,
            users_to_send=[a.applier],
            sockets=applier_sockets,
            title=title,
            message=message,
            icon_type=icon_type
        )


def send_notification_on_appeal(appeal, users_to_send, sockets, title, message, icon_type):
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
