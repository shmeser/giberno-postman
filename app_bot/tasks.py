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
    try:
        chat, bot_repository = get_chat_and_bot_repo(version, user_id, chat_id)
        if not chat:
            return

        # TODO Определить тип ответа - список документов, форма, обычное сообщение и т.д.

        text_reply, intent_code = bot_repository.get_response(message_text)

        text_reply, buttons = get_reply_and_buttons(text_reply, intent_code, version, chat)

        # Сохраняем ответ бота и отправляем
        save_bot_reply_and_send(version, chat_id, text_reply, buttons)
    except Exception as e:
        logger.error(e)


@app.task
def delayed_select_bot_intent(version, chat_id, user_id, intent_code):
    __SWITCH_CHAT_TO_MANAGER_MESSAGE = 'Перевожу разговор на менеджера'
    try:
        chat, bot_repository = get_chat_and_bot_repo(version, user_id, chat_id)
        if not chat:
            return

        text_reply = bot_repository.get_response_by_intent_code(intent_code)
        text_reply, buttons = get_reply_and_buttons(text_reply, intent_code, version, chat)

        # Если запрошен менеджер в чат
        if intent_code == ChatterBotIntentCode.DISABLE.value:
            add_managers_to_chat(version, chat)

            text_reply = __SWITCH_CHAT_TO_MANAGER_MESSAGE
            buttons = None  # Не отправляем кнопки

        # Сохраняем ответ бота и отправляем
        save_bot_reply_and_send(version, chat_id, text_reply, buttons)

    except Exception as e:
        logger.error(e)


def get_chat_and_bot_repo(version, user_id, chat_id):
    user_repository = RoutingMapper.room_repository(
        version=version, room_name=AvailableRoom.USERS.value)
    user = user_repository().get_by_id(user_id)
    # Проверяем необходимость отправки сообщения в чат от имени бота

    # Обрабатываем сообщения только от СМЗ
    if user is None or user.account_type != AccountType.SELF_EMPLOYED.value:
        return None, None

    chat_repository = RoutingMapper.room_repository(
        version=version, room_name=AvailableRoom.CHATS.value)
    chat = chat_repository().get_by_id(chat_id)

    # НЕ обрабатываем сообщения в удаленных чатах и в состоянии НЕ в BOT_IS_USED
    if chat.deleted is True or chat.state != ChatManagerState.BOT_IS_USED.value:
        return None, None

    bot_repository = RoutingMapper.room_repository(
        version=version, room_name=AvailableRoom.BOT.value)

    return chat, bot_repository


def get_reply_and_buttons(text_reply, intent_code, version, chat):
    buttons = None
    # Если запрошен менеджер в чат
    if intent_code == ChatterBotIntentCode.DISABLE.value:
        buttons = BotIntentsHandler.get_disable_bot_buttons()
    # Vacs Shops
    if intent_code == ChatterBotIntentCode.SHOP_ADDRESS.value:
        text_reply = BotIntentsHandler.get_shop_address(version, chat.target, chat.target_id)
    # Vacs
    if intent_code == ChatterBotIntentCode.VACANCY_REQUIREMENTS.value:
        text_reply = BotIntentsHandler.get_vacancy_requirements(version, chat.target, chat.target_id)
    if intent_code == ChatterBotIntentCode.APPEAL_CONFIRMATION.value:
        pass  # не меняем ответ бота
    if intent_code == ChatterBotIntentCode.SHIFT_TIME.value:
        text_reply = BotIntentsHandler.get_shift_time(version, chat.target, chat.target_id, chat.subject_user)
    if intent_code == ChatterBotIntentCode.WHAT_TO_TAKE_WITH.value:
        text_reply = BotIntentsHandler.get_necessary_docs_to_take(version, chat.target, chat.target_id)
    if intent_code == ChatterBotIntentCode.CANCEL_APPEAL.value:
        # Текст дает бот
        text, buttons = BotIntentsHandler.get_appeal_cancellation_response(
            version, chat.target, chat.target_id, chat.subject_user)
        if text:
            text_reply = text
    # Shops
    if intent_code == ChatterBotIntentCode.VACANCIES_VARIETY.value:
        text_reply, buttons = BotIntentsHandler.get_shop_vacancies_response(version, chat.target, chat.target_id)
    if intent_code == ChatterBotIntentCode.VACANCY_RATES.value:
        text_reply, buttons = BotIntentsHandler.get_shop_vacancy_rates_response(version, chat.target, chat.target_id)

    return text_reply, buttons


def save_bot_reply_and_send(version, chat_id, text_reply, buttons):
    message_repository = RoutingMapper.room_repository(
        version=version, room_name=AvailableRoom.MESSAGES.value)

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


def add_managers_to_chat(version, chat):
    __NOTIFICATION_TITLE = 'Необходима поддержка от менеджера'
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
            title=__NOTIFICATION_TITLE,
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
            'title': __NOTIFICATION_TITLE,
            'message': message,
            'uuid': str(common_uuid),
            'action': action,
            'subjectId': chat.id,
            'notificationType': notification_type,
            'iconType': icon_type,
        })


class BotIntentsHandler:
    __ASK_EXACT_VACANCY_CHAT = 'Обратитесь в чат по конкретной вакансии'
    __ASK_EXACT_SHOP_CHAT = 'Обратитесь в чат c конкретным магазином'
    __NO_CONFIRMED_APPEALS_FOR_VACANCY = 'У вас нет одобренных заявок на эту вакансию'

    @staticmethod
    def get_disable_bot_buttons():
        buttons = [
            {
                'action': ChatMessageActionType.SHOP_VACANCIES.value,
                'text': 'Вакансии'
            },
            {
                'action': ChatMessageActionType.APPEALS.value,
                'text': 'Отклики'
            },
            {
                'action': ChatMessageActionType.BOT_INTENT.value,
                'text': 'Соединить с менеджером',
                'intent': ChatterBotIntentCode.DISABLE.value
            }
        ]

        return buttons

    @staticmethod
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

    @classmethod
    def get_vacancy_requirements(cls, version, target, vacancy_id):
        if isinstance(target, Shop):
            return cls.__ASK_EXACT_VACANCY_CHAT
        # TODO добавить файлы документов и разбивку по точным запросам (бонусы, опыт и т.д)
        vacancy_repository = RoutingMapper.room_repository(version=version, room_name=AvailableRoom.VACANCIES.value)
        return vacancy_repository().get_requirements(vacancy_id)

    @classmethod
    def get_shift_time(cls, version, target, vacancy_id, subject_user):
        if isinstance(target, Shop):
            return cls.__ASK_EXACT_VACANCY_CHAT
        vacancy_repository = RoutingMapper.room_repository(version=version, room_name=AvailableRoom.VACANCIES.value)
        text = vacancy_repository().get_shift_remaining_time_to_start(subject_user, vacancy_id)
        if not text:
            text = cls.__NO_CONFIRMED_APPEALS_FOR_VACANCY
        return text

    @staticmethod
    def get_necessary_docs_to_take(version, target, target_id):
        required_docs = 'Паспорт'
        if isinstance(target, Vacancy):
            vacancy_repository = RoutingMapper.room_repository(version=version, room_name=AvailableRoom.VACANCIES.value)
            vacancy_required_docs = vacancy_repository().get_necessary_docs(target_id)
            if vacancy_required_docs:
                return vacancy_required_docs

        return required_docs

    @classmethod
    def get_appeal_cancellation_response(cls, version, target, vacancy_id, subject_user):
        if not isinstance(target, Vacancy):
            return cls.__ASK_EXACT_VACANCY_CHAT, None
        vacancy_repository = RoutingMapper.room_repository(version=version, room_name=AvailableRoom.VACANCIES.value)
        has_active_shifts = vacancy_repository().check_if_has_confirmed_appeals(subject_user, vacancy_id)
        text = None
        if not has_active_shifts:
            text = cls.__NO_CONFIRMED_APPEALS_FOR_VACANCY
        buttons = [
            {
                'action': ChatMessageActionType.APPEALS.value,
                'text': 'Отказаться'
            }
        ]
        return text, buttons

    @classmethod
    def get_shop_vacancies_response(cls, version, target, shop_id):
        if not isinstance(target, Shop):
            return cls.__ASK_EXACT_SHOP_CHAT, None
        # shop_repository = RoutingMapper.room_repository(version=version, room_name=AvailableRoom.SHOPS.value)
        # Shop
        # shop = shop_repository().get_by_id(shop_id)
        return '', [{
            'action': ChatMessageActionType.SHOP_VACANCIES.value,
            'text': 'Показать вакансии'
        }]

    @classmethod
    def get_shop_vacancy_rates_response(cls, version, target, shop_id):
        if not isinstance(target, Shop):
            return cls.__ASK_EXACT_SHOP_CHAT, None
        shop_repository = RoutingMapper.room_repository(version=version, room_name=AvailableRoom.SHOPS.value)
        # Shop
        shop = shop_repository().get_by_id(shop_id)
        return 'Таковы условия этого магазина! Хотите поискать в других магазинах?', [{
            'action': ChatMessageActionType.DISTRIBUTOR_SHOPS.value,
            'text': 'Показать другие магазины'
        }]
