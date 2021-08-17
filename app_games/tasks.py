import uuid

from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now
from celery import group
from app_games.enums import TaskType, TaskPeriod, TaskKind
from app_games.versions.v1_0.repositories import TasksRepository, PrizesRepository
from app_market.enums import TransactionType, TransactionStatus, Currency
from app_market.versions.v1_0.repositories import OrdersRepository, TransactionsRepository
from app_sockets.controllers import SocketController
from app_users.enums import NotificationAction, NotificationType, NotificationIcon
from app_users.versions.v1_0.repositories import UsersRepository
from backend.controllers import PushController
from giberno.celery import app
from giberno.settings import BONUS_PROGRESS_STEP_VALUE


@app.task
def check_users_daily_tasks_on_completed_shifts():
    jobs = group(
        [check_everyday_tasks_for_user.s(user_id, TaskKind.COMPLETE_SHIFT_WITH_MIN_RATING.value) for user_id in
         UsersRepository.get_all_self_employed_ids()])
    jobs.apply_async()


@app.task
def check_everyday_tasks_for_user(user_id, kind):
    """

    """
    task = TasksRepository().filter_by_kwargs(
        {
            'type': TaskType.COMMON.value,
            'period': TaskPeriod.DAILY.value,
            'kind': kind,
        }
    ).first()
    if not task:
        return

    # Ищем последнюю завершенную такую же задачу
    last_same_task_completed = TasksRepository.get_user_last_task_completed(
        task_id=task.id, user_id=user_id
    )

    check_after_date = None
    if last_same_task_completed:
        if last_same_task_completed.created_at.date() == now().date():
            # Если есть, но выполнена сегодня
            return
        check_after_date = last_same_task_completed.created_at

    # Проверяем возможность выполнения задания (ищем выполненные условия)
    conditions_fulfilled = TasksRepository.check_fulfilled_conditions(
        user_id=user_id, task=task, check_after_date=check_after_date
    )
    if not conditions_fulfilled:
        return

    # Выполнить задание
    completed_task = TasksRepository.complete_task(
        task_id=task.id, user_id=user_id
    )
    # Начислить бонусы
    user_ct = ContentType.objects.get_for_model(completed_task.user)
    OrdersRepository.create_transaction(
        amount=task.bonus_value,
        t_type=TransactionType.DEPOSIT.value,
        to_ct=user_ct,
        to_ct_name=user_ct.model,
        to_id=user_id,
        comment=f'Начисление бонусов за выполненное задание "{task.name}" - "{task.description}"',
        **{
            'status': TransactionStatus.COMPLETED.value
        }
    )

    new_bonus_acquired_value = completed_task.user.bonuses_acquired + task.bonus_value
    old_level = completed_task.user.bonuses_acquired // BONUS_PROGRESS_STEP_VALUE
    new_level = new_bonus_acquired_value // BONUS_PROGRESS_STEP_VALUE

    if new_level != old_level:
        PrizesRepository.issue_prize_cards_for_user(
            user_id=user_id, bonuses_acquired=new_bonus_acquired_value
        )

    completed_task.user.bonuses_acquired += task.bonus_value
    completed_task.user.save()

    TransactionsRepository(completed_task.user).recalculate_money(currency=Currency.BONUS.value)

    title = 'Начислены бонусы'
    message = f'Начисление {task.bonus_value} очков славы за выполненное задание'
    action = NotificationAction.USER.value
    subject_id = user_id
    notification_type = NotificationType.SYSTEM.value
    icon_type = NotificationIcon.DEFAULT.value

    # uuid для массовой рассылки оповещений,
    # у пользователей в бд будут созданы оповещения с одинаковым uuid
    # uuid необходим на клиенте для фильтрации одинаковых данных, полученных по 2 каналам - сокеты и пуши
    common_uuid = uuid.uuid4()

    PushController().send_notification(
        users_to_send=[completed_task.user],
        title=title,
        message=message,
        common_uuid=common_uuid,
        action=action,
        subject_id=subject_id,
        notification_type=notification_type,
        icon_type=icon_type,
    )

    # Отправка уведомления по сокетам
    SocketController(completed_task.user, version='1.0').send_notification_to_my_connection({
        'title': title,
        'message': message,
        'uuid': str(common_uuid),
        'action': action,
        'subjectId': subject_id,
        'notificationType': notification_type,
        'iconType': icon_type,
    })
