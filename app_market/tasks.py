import uuid

from celery import group
from celery import shared_task
from loguru import logger

from app_market.enums import AchievementType
from app_market.utils import send_socket_event_on_appeal_statuses
from app_market.versions.v1_0.repositories import ShiftAppealsRepository, AchievementsRepository, ShiftsRepository
from app_sockets.controllers import SocketController
from app_users.enums import NotificationAction, NotificationType, NotificationIcon
from backend.controllers import PushController
from giberno.celery import app

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
    grouped_tasks = []  # Группа задач
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

        # Обрабатываем достижения по выполненным сменам
        grouped_tasks.append(check_shift_achievement.s(a.completed_real_time, a.applier_id))

    # Создаем группу асинхронных задач и выполняем ее
    jobs = group(grouped_tasks)
    jobs.apply_async()
    # ==================== #

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


ITEMS_PER_CHUNK = 100


@app.task
def check_shift_achievement(appeal_real_date_end, applier_id):
    """
        # из откликов собираем уникальных пользователей
        # по каждому пользователю получаем или создаем прогресс по достижению
        # считаем поличество завершенных откликов для каждого пользователя, включая текущий,
            сгруппированных по торговой сети и начиная с даты создания прогресса
            (если не было прогресса, то started_at присвоить время фактического завершения отклика)
        # количество завершенных откликов по каждой торговой сети должно быть >= actions_min_count в Achievement
        # actions_count в прогрессе ставится как сумма сгруппированных по торговым сетям значений,
            которые >= actions_min_count, если сгруппированное значение меньше, то оно не учитывается
    """
    achievement = AchievementsRepository().filter_by_kwargs(
        {'type': AchievementType.SAME_DISTRIBUTOR_SHIFT.value}).first()
    if not achievement:
        return

    progress = AchievementsRepository.get_progress_for_user(
        achievement_id=achievement.id, user_id=applier_id, **{
            'started_at': appeal_real_date_end
        }
    )

    achieved_count = ShiftAppealsRepository.aggregate_stats_for_achievements(
        applier_id,
        achievement.actions_min_count,
        progress.started_at
    )

    if achieved_count and progress.achieved_count < achieved_count:  # знак < если вдруг achieved_count придет кривой
        # Если количество выполнений всех условий для ачивки изменилось, то отправляем пуш и записываем новые значения
        progress.achieved_count = achieved_count
        progress.save()

        # TODO отправить пуш о достижении

        logger.debug(f'========= НОВОЕ ДОСТИЖЕНИЕ {achievement.name} для USER {applier_id} ==========')

def auto_control_timed_shifts():
    #  Ищем все смены, у которых стоит мин рейтинг для работников, есть свободные места, и наступило время контроля
    #  Берем все неодобренные отклики,сортируем их по рейтингу заявителя, берем нужное количество
    #  Одобряем выбранные отклики
    shifts = ShiftsRepository.get_shifts_for_auto_control()

