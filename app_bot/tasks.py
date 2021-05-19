import uuid

from loguru import logger

from app_bot.enums import ChatterBotIntentCode
from app_chats.enums import ChatMessageType, ChatManagerState, ChatMessageActionType
from app_market.models import Vacancy, Shop
from app_sockets.controllers import SocketController
from app_sockets.enums import AvailableRoom, AvailableVersion
from app_sockets.mappers import RoutingMapper
from app_users.enums import AccountType, NotificationAction, NotificationType, NotificationIcon
from backend.controllers import PushController
from backend.utils import datetime_to_timestamp
from giberno.celery import app


@app.task
def delayed_checking_for_bot_reply(version, chat_id, user_id, message_text):
    __NOTIFICATION_TITLE = 'Необходима поддержка от менеджера'

    try:
        user_repository = RoutingMapper.room_repository(
            version=version, room_name=AvailableRoom.USERS.value)
        user = user_repository().get_by_id(user_id)
        # Проверяем необходимость отправки сообщения в чат от имени бота

        # Обрабатываем сообщения только от СМЗ
        if user is None or user.account_type != AccountType.SELF_EMPLOYED.value:
            return

        chat_repository = RoutingMapper.room_repository(
            version=version, room_name=AvailableRoom.CHATS.value)
        chat = chat_repository().get_by_id(chat_id)

        # НЕ обрабатываем сообщения в удаленных чатах и в состоянии НЕ в BOT_IS_USED
        if chat.deleted is True or chat.state != ChatManagerState.BOT_IS_USED.value:
            return

        bot_repository = RoutingMapper.room_repository(
            version=version, room_name=AvailableRoom.BOT.value)
        message_repository = RoutingMapper.room_repository(
            version=version, room_name=AvailableRoom.MESSAGES.value)

        # TODO Определить тип ответа - список документов, форма, обычное сообщение и т.д.

        text_reply, intent_code = bot_repository.get_response(message_text)
        buttons = None

        # Если запрошен менеджер в чат
        if intent_code == ChatterBotIntentCode.DISABLE.value:
            # TODO не сразу переводить, добавить несколько попыток с вариантами кнопок
            add_managers_to_chat(version, chat, __NOTIFICATION_TITLE)

        # Vacs Shops
        if intent_code == ChatterBotIntentCode.SHOP_ADDRESS.value:
            text_reply = get_shop_address(version, chat.target, chat.target_id)
        # Vacs
        if intent_code == ChatterBotIntentCode.VACANCY_REQUIREMENTS.value:
            text_reply = get_vacancy_requirements(version, chat.target, chat.target_id, message_text)
        if intent_code == ChatterBotIntentCode.APPEAL_CONFIRMATION.value:
            pass  # не меняем ответ бота
        if intent_code == ChatterBotIntentCode.SHIFT_TIME.value:
            text_reply = get_shift_time(version, chat.target, chat.target_id, chat.subject_user)
        if intent_code == ChatterBotIntentCode.WHAT_TO_TAKE_WITH.value:
            text_reply = get_necessary_docs_to_take(version, chat.target, chat.target_id)
        if intent_code == ChatterBotIntentCode.CANCEL_APPEAL.value:
            # Текст дает бот
            text, buttons = get_appeal_cancellation_response(version, chat.target, chat.target_id, chat.subject_user)
            if text:
                text_reply = text
        # Shops
        if intent_code == ChatterBotIntentCode.VACANCIES_VARIETY.value:
            text_reply, buttons = get_shop_vacancies_response(version, chat.target, chat.target_id)
        if intent_code == ChatterBotIntentCode.VACANCY_RATES.value:
            text_reply, buttons = get_shop_vacancy_rates_response(version, chat.target, chat.target_id)

        # Сохраняем ответ бота
        bot_message_serialized = message_repository(chat_id=chat_id).save_bot_message(
            {
                'message_type': ChatMessageType.SIMPLE.value,
                'text': text_reply,
                'buttons': buttons
            }
        )

        SocketController(
            version=AvailableVersion.V1_0.value,
            room_name=AvailableRoom.CHATS.value
        ).send_chat_message(chat_id=chat_id, prepared_message=bot_message_serialized)
    except Exception as e:
        logger.error(e)


__ASK_EXACT_VACANCY_CHAT = 'Обратитесь в чат по конкретной вакансии'
__ASK_EXACT_SHOP_CHAT = 'Обратитесь в чат c конкретным магазином'
__NO_CONFIRMED_APPEALS_FOR_VACANCY = 'У вас нет одобренных заявок на эту вакансию'


def add_managers_to_chat(version, chat, notification_title):
    # Добавляем всех релевантных менеджеров в чат
    # переводим чат в состояние NEED_MANAGER
    chat.state = ChatManagerState.NEED_MANAGER.value
    chat.save()

    chat_repository = RoutingMapper.room_repository(
        version=version, room_name=AvailableRoom.CHATS.value)

    managers, managers_sockets, blocked_at = chat_repository().get_managers_and_sockets(chat.id)
    if managers:
        chat.users.add(*managers)  # добавляем в m2m несколько менеджеров с десериализацией через *

        # Отправляем всем релевантным менеджерам по сокетам смену состояния чата
        for socket_id in managers_sockets:
            # Отправялем сообщение автору сообщения о том, что оно прочитано
            SocketController(version=AvailableVersion.V1_0.value).send_message_to_one_connection(socket_id, {
                'type': 'chat_state_updated',
                'prepared_data': {
                    'id': chat.id,
                    'state': ChatManagerState.NEED_MANAGER.value,
                    'activeManagersIds': [],
                    'blockedAt': datetime_to_timestamp(blocked_at) if blocked_at is not None else None
                },
            })

        # Отправляем всем релевантным менеджерам пуш о том что нужна помощь человека
        # uuid для массовой рассылки оповещений,
        # у пользователей в бд будут созданы оповещения с одинаковым uuid
        # uuid необходим на клиенте для фильтрации одинаковых данных, полученных по 2 каналам - сокеты и пуши
        common_uuid = uuid.uuid4()
        message = f'Пользователь {chat.subject_user.first_name} {chat.subject_user.last_name}'
        if chat.target and isinstance(chat.target, Vacancy):
            message += f', вакансия {chat.target.title}'

        if chat.target and isinstance(chat.target, Shop):
            message += f', магазин {chat.target.title} {chat.target.address if chat.target.address else ""}'

        notification_type = NotificationType.SYSTEM.value
        action = NotificationAction.CHAT.value
        icon_type = NotificationIcon.DEFAULT.value
        PushController().send_notification(
            users_to_send=managers,
            title=notification_title,
            message=message,
            common_uuid=common_uuid,
            action=action,
            subject_id=chat.id,
            notification_type=notification_type,
            icon_type=icon_type,
        )

        # После отправки пушей (записи в бд создаются перед пушами) дублируем по сокетам уведомления
        # TODO тут пока не учитываются настройки оповещений (notification_type)
        SocketController().send_notification_to_many_connections(managers_sockets, {
            'title': notification_title,
            'message': message,
            'uuid': str(common_uuid),
            'action': action,
            'subjectId': chat.id,
            'notificationType': notification_type,
            'iconType': icon_type,
        })


def get_shop_address(version, target, target_id):
    if isinstance(target, Vacancy):
        vacancy_repository = RoutingMapper.room_repository(version=version, room_name=AvailableRoom.VACANCIES.value)
        shop_repository = RoutingMapper.room_repository(version=version, room_name=AvailableRoom.SHOPS.value)
        vacancy = vacancy_repository().get_by_id(target_id)
        shop = shop_repository().get_by_id(vacancy.shop_id)
        return shop.address
    if isinstance(target, Shop):
        shop_repository = RoutingMapper.room_repository(version=version, room_name=AvailableRoom.SHOPS.value)
        shop = shop_repository().get_by_id(target_id)
        return shop.address
    return ''


def get_vacancy_requirements(version, target, vacancy_id, message_text):
    if isinstance(target, Shop):
        return __ASK_EXACT_VACANCY_CHAT
    # TODO добавить файлы документов и разбивку по точным запросам (бонусы, опыт и т.д)
    vacancy_repository = RoutingMapper.room_repository(version=version, room_name=AvailableRoom.VACANCIES.value)
    return vacancy_repository().get_requirements(vacancy_id, message_text)


def get_shift_time(version, target, vacancy_id, subject_user):
    if isinstance(target, Shop):
        return __ASK_EXACT_VACANCY_CHAT
    vacancy_repository = RoutingMapper.room_repository(version=version, room_name=AvailableRoom.VACANCIES.value)
    text = vacancy_repository().get_shift_remaining_time_to_start(subject_user, vacancy_id)
    if not text:
        text = __NO_CONFIRMED_APPEALS_FOR_VACANCY
    return text


def get_necessary_docs_to_take(version, target, target_id):
    if isinstance(target, Vacancy):
        vacancy_repository = RoutingMapper.room_repository(version=version, room_name=AvailableRoom.VACANCIES.value)
        return vacancy_repository().get_necessary_docs(target_id)
    return 'Паспорт'


def get_appeal_cancellation_response(version, target, vacancy_id, subject_user):
    if not isinstance(target, Vacancy):
        return __ASK_EXACT_VACANCY_CHAT, None
    vacancy_repository = RoutingMapper.room_repository(version=version, room_name=AvailableRoom.VACANCIES.value)
    has_active_shifts = vacancy_repository().check_if_has_confirmed_appeals(subject_user, vacancy_id)
    text = None
    if not has_active_shifts:
        text = __NO_CONFIRMED_APPEALS_FOR_VACANCY
    buttons = [
        {
            'action': ChatMessageActionType.APPEAL.value,
            'text': 'Отказаться'
        }
    ]
    return text, buttons


def get_shop_vacancies_response(version, target, shop_id):
    if not isinstance(target, Shop):
        return __ASK_EXACT_SHOP_CHAT, None
    # shop_repository = RoutingMapper.room_repository(version=version, room_name=AvailableRoom.SHOPS.value)
    # Shop
    # shop = shop_repository().get_by_id(shop_id)
    return '', [{
        'action': ChatMessageActionType.SHOP.value,
        'text': 'Показать вакансии'
    }]


def get_shop_vacancy_rates_response(version, target, shop_id):
    if not isinstance(target, Shop):
        return __ASK_EXACT_SHOP_CHAT, None
    shop_repository = RoutingMapper.room_repository(version=version, room_name=AvailableRoom.SHOPS.value)
    # Shop
    shop = shop_repository().get_by_id(shop_id)
    return 'Таковы условия этого магазина! Хотите поискать в других магазинах?', [{
        'action': ChatMessageActionType.DISTRIBUTOR.value,
        'text': 'Показать другие магазины'
    }]
