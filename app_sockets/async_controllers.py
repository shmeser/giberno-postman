import asyncio

from loguru import logger

from app_bot.tasks import delayed_checking_for_bot_reply, delayed_select_bot_intent
from app_chats.enums import ChatMessageType, ChatMessageIconType, ChatManagerState
from app_sockets.enums import SocketEventType, AvailableRoom
from app_sockets.mappers import RoutingMapper
from app_users.enums import NotificationAction, NotificationType, AccountType
from backend.controllers import AsyncPushController
from backend.errors.enums import SocketErrors
from backend.errors.exceptions import EntityDoesNotExistException, ForbiddenException
from backend.errors.ws_exceptions import WebSocketError
from backend.utils import chained_get, datetime_to_timestamp


class AsyncSocketController:
    def __init__(self, consumer=None) -> None:
        super().__init__()
        self.consumer = consumer
        self.own_repository_class = RoutingMapper.room_async_repository(consumer.version)
        self.repository_class = RoutingMapper.room_async_repository(consumer.version, consumer.room_name)

    async def store_single_connection(self):
        try:
            me = self.consumer.user  # Прользователь текущего соединения

            await self.own_repository_class(me).add_socket(
                self.consumer.channel_name  # ид соединения
            )
        except Exception as e:
            logger.error(e)
            raise WebSocketError(code=SocketErrors.BAD_REQUEST.value, details=e)

    async def store_group_connection(self, **kwargs):
        try:
            me = self.consumer.user  # Прользователь текущего соединения

            await self.own_repository_class(me).add_socket(
                self.consumer.channel_name,  # ид соединения,
                chained_get(kwargs, 'room_name', default=self.consumer.room_name),  # имя комнаты
                chained_get(kwargs, 'room_id', default=self.consumer.room_id)  # ид комнаты
            )

        except Exception as e:
            logger.error(e)
            raise WebSocketError(code=SocketErrors.BAD_REQUEST.value, details=e)

    async def remove_connection(self):
        me = self.consumer.user  # Пользователь текущего соединения
        await self.own_repository_class(me).remove_socket(self.consumer.channel_name)

    async def send_error(self, code, details):
        await self.consumer.channel_layer.send(self.consumer.channel_name, {
            'type': 'error_handler',
            'code': code,
            'details': details,
        })

    async def leave_topic(self, content):
        group_name = content.get('topic')

        # Удаляем соединение из группы
        await self.consumer.channel_layer.group_discard(group_name, self.consumer.channel_name)
        await self.topic_leaved(group_name)

    async def join_topic(self, content):
        room_name = None
        room_id = None
        group_name = content.get('topic')
        if group_name:
            room_name, room_id = RoutingMapper.get_room_and_id(self.consumer.version, group_name)

        if await self.check_permission_for_group_connection(**{
            'room_name': room_name,
            'room_id': room_id,
        }):
            # Добавляем соединение в группу
            await self.consumer.channel_layer.group_add(group_name, self.consumer.channel_name)
            await self.topic_joined(group_name)
        else:
            await self.send_error(
                code=SocketErrors.FORBIDDEN.value, details=SocketErrors.FORBIDDEN.name
            )

    async def topic_joined(self, topic):
        await self.consumer.channel_layer.send(self.consumer.channel_name, {
            'type': 'server_message_handler',
            'event_type': SocketEventType.TOPIC_JOINED.value,
            'prepared_data': {
                'topic': topic
            },
        })

    async def topic_leaved(self, topic):
        await self.consumer.channel_layer.send(self.consumer.channel_name, {
            'type': 'server_message_handler',
            'event_type': SocketEventType.TOPIC_LEAVED.value,
            'prepared_data': {
                'topic': topic
            },
        })

    async def check_permission_for_group_connection(self, **kwargs):
        try:
            # Проверка возможности присоединиться к определенному каналу в чате
            version = self.consumer.version
            room_name = chained_get(kwargs, 'room_name', default=self.consumer.room_name)
            room_id = chained_get(kwargs, 'room_id', default=self.consumer.room_id)
            me = self.consumer.user  # Пользователь текущего соединения

            if not RoutingMapper.check_room_version(room_name, version):
                logger.info(f'Такой точки соединения не существует для версии {version}')

                if self.consumer.is_group_consumer:
                    # Закрываем соединение, если это GroupConsumer
                    await self.consumer.close(code=SocketErrors.NOT_FOUND.value)

                return False

            self.repository_class = RoutingMapper.room_async_repository(version, room_name)

            await self.repository_class(me).check_if_exists(room_id)
            return True

        except EntityDoesNotExistException:
            logger.info(f'Объект не найден')
            if self.consumer.is_group_consumer:
                # Закрываем соединение, если это GroupConsumer
                await self.consumer.close(code=SocketErrors.NOT_FOUND.value)
                return False
            raise WebSocketError(code=SocketErrors.NOT_FOUND.value, details=SocketErrors.NOT_FOUND.name)
        except ForbiddenException:
            logger.info(f'Действие запрещено')
            if self.consumer.is_group_consumer:
                # Закрываем соединение, если это GroupConsumer
                await self.consumer.close(code=SocketErrors.FORBIDDEN.value)
                return False
            raise WebSocketError(code=SocketErrors.FORBIDDEN.value, details=SocketErrors.FORBIDDEN.name)
        except Exception as e:
            logger.error(e)
            if self.consumer.is_group_consumer:
                # Закрываем соединение, если это GroupConsumer
                await self.consumer.close(code=SocketErrors.BAD_REQUEST.value)
            raise WebSocketError(code=SocketErrors.CUSTOM_DETAILED_ERROR.value, details=str(e))

    async def update_location(self, event):
        self.repository_class = RoutingMapper.room_async_repository(self.consumer.version, AvailableRoom.USERS.value)
        user = await self.repository_class(me=self.consumer.user).update_location(event)
        return user

    async def send_chat_state_to_managers(self, chat_id, state, active_managers_ids=[]):
        chat_repository = RoutingMapper.room_async_repository(
            version=self.consumer.version, room_name=AvailableRoom.CHATS.value
        )

        managers, relevant_managers_sockets, blocked_at = await chat_repository().get_managers_and_sockets(
            chat_id=chat_id
        )

        for socket in relevant_managers_sockets:
            await self.consumer.channel_layer.send(socket, {
                'type': 'chat_state_updated',
                'prepared_data': {
                    'id': chat_id,
                    'state': state,
                    'activeManagersIds': active_managers_ids,
                    'blockedAt': datetime_to_timestamp(blocked_at) if blocked_at is not None else None
                },
            })

    async def send_chat_message(self, room_id, group_name, prepared_message):
        personalized_chat_variants_with_sockets, chat_users, push_title, inactive_mng_ids = await self.repository_class(
            me=self.consumer.user
        ).get_chat_for_all_participants(  # 10
            chat_id=room_id
        )

        # Отправялем сообщение обратно в групповой канал по сокетам
        await self.consumer.channel_layer.group_send(group_name, {
            'type': 'chat_message',
            'chat_id': room_id,
            'prepared_data': prepared_message,
        })

        # Отправляем обновленные данные о чате всем участникам чата по одиночным сокетам
        for data in personalized_chat_variants_with_sockets:
            for connection_name in data['sockets']:
                await self.send_last_msg_updated_to_one_connection(
                    socket_id=connection_name,
                    room_id=room_id,
                    unread_cnt=chained_get(data, 'chat', 'unreadCount'),
                    first_unread=chained_get(data, 'chat', 'firstUnreadMessage'),
                    last_msg=prepared_message,
                    chats_unread_messages_count=chained_get(data, 'chats_unread_messages'),
                    blocked_at=chained_get(data, 'chat', 'blockedAt'),
                    state=chained_get(data, 'chat', 'state'),
                )

        # Отправляем сообщение по пушам всем участникам чата, кроме самого себя
        # Заголовки сообщения формируется исходя из роли отправителя

        inactive_mng_ids.append(self.consumer.user.id)  # Не отправляем пуш неактивным менеджерам и самому себе

        users_to_send = chat_users.exclude(
            pk__in=inactive_mng_ids
        )
        await AsyncPushController().send_message(
            users_to_send=users_to_send,
            title=push_title,
            message=chained_get(prepared_message, 'text', default=''),
            uuid=chained_get(prepared_message, 'uuid', default=''),
            action=NotificationAction.CHAT.value,
            subject_id=room_id,
            notification_type=NotificationType.CHAT.value,
            icon_type=''
        )

    async def send_chat_message_async(self, room_id, group_name, prepared_message):
        try:
            loop = asyncio.get_event_loop()
            task = loop.create_task(self.send_chat_message(room_id, group_name, prepared_message))
            # Необходимо для отлова исключений, но блокирует выполнение
            # await asyncio.gather(task, return_exceptions=False)
        except Exception as e:
            logger.error(e)
            raise WebSocketError(code=SocketErrors.BAD_REQUEST.value, details=str(e))

    async def client_message_to_chat(self, content):
        room_id = self.consumer.room_id
        group_name = self.consumer.group_name
        if not room_id:
            room_id = chained_get(content, 'chatId')
            group_name = f'{AvailableRoom.CHATS.value}{room_id}'

        self.repository_class = RoutingMapper.room_async_repository(self.consumer.version, AvailableRoom.CHATS.value)

        try:
            await self.repository_class(self.consumer.user).check_permission_for_action(room_id)

            message_repository = RoutingMapper.room_async_repository(
                self.consumer.version, AvailableRoom.MESSAGES.value
            )

            # Обрабатываем полученное от клиента сообщение
            processed_serialized_message = await message_repository(
                me=self.consumer.user,
                chat_id=room_id,
            ).save_client_message(
                content=content
            )

            # Отправляем сообщение в чат с персонализацией для всех участников
            await self.send_chat_message_async(
                room_id=room_id,
                group_name=group_name,
                prepared_message=processed_serialized_message
            )

            # Ответ бота через Celery с задержкой
            delayed_checking_for_bot_reply.s(
                version=self.consumer.version,
                chat_id=room_id,
                user_id=self.consumer.user.id,
                message_text=chained_get(processed_serialized_message, 'text')
            ).apply_async(countdown=2)  # Отвечаем через 2 сек

        except ForbiddenException:
            logger.info(f'Действие запрещено')
            await self.send_error(
                code=SocketErrors.FORBIDDEN.value, details=SocketErrors.FORBIDDEN.name
            )
            if self.consumer.is_group_consumer:
                # Закрываем соединение, если это GroupConsumer
                await self.consumer.close(code=SocketErrors.FORBIDDEN.value)
        except EntityDoesNotExistException:
            logger.info(f'Не найдено')
            await self.send_error(
                code=SocketErrors.NOT_FOUND.value, details=SocketErrors.NOT_FOUND.name
            )
            if self.consumer.is_group_consumer:
                # Закрываем соединение, если это GroupConsumer
                await self.consumer.close(code=SocketErrors.NOT_FOUND.value)

        except Exception as e:
            logger.error(e)
            if self.consumer.is_group_consumer:
                # Закрываем соединение, если это GroupConsumer
                await self.consumer.close(code=SocketErrors.BAD_REQUEST.value)
            raise WebSocketError(code=SocketErrors.CUSTOM_DETAILED_ERROR.value, details=str(e))

    async def client_read_message_in_chat(self, content):
        try:
            room_id = self.consumer.room_id
            if not room_id:
                room_id = chained_get(content, 'chatId')

            self.repository_class = RoutingMapper.room_async_repository(
                self.consumer.version, AvailableRoom.CHATS.value
            )
            await self.repository_class(self.consumer.user).check_permission_for_action(room_id)

            message_repository = RoutingMapper.room_async_repository(
                self.consumer.version, AvailableRoom.MESSAGES.value
            )

            # Обрабатываем полученные от клиента данные
            message, owner, owner_sockets, should_response_owner = await message_repository(
                me=self.consumer.user,
                chat_id=room_id,
            ).client_read_message(
                content=content
            )

            if message:
                msg, owner_unread_cnt, owner_first_unread, owner_chats_unread_count, my_unread_cnt, my_first_unread, my_chats_unread_cnt, blocked_at, state = await message_repository(
                    me=self.consumer.user,
                    chat_id=room_id,
                ).get_unread_data(message=message, msg_owner=owner, should_response_owner=should_response_owner)

                # Отправялем ответ на свой запрос с числом непрочитанных сообщений в чате
                await self.send_message_was_read(
                    unread_cnt=my_unread_cnt,
                    room_id=room_id,
                    first_unread=my_first_unread,
                    uuid=chained_get(content, 'uuid'),
                    chats_unread_messages_count=my_chats_unread_cnt,
                    blocked_at=blocked_at,
                    state=state
                )

                # Отправляем автору сообщения событие о прочтении, если сообщение последнее в чате
                await self.respond_to_msg_owner_when_read(
                    owner=owner,
                    sockets=owner_sockets,
                    should_response=should_response_owner,
                    room_id=room_id,
                    unread_cnt=owner_unread_cnt,
                    last_msg=msg,
                    first_unread=owner_first_unread,
                    chats_unread_count=owner_chats_unread_count,
                    blocked_at=blocked_at,
                    state=state
                )

        except ForbiddenException:
            logger.info(f'Действие запрещено')
            if self.consumer.is_group_consumer:
                # Закрываем соединение, если это GroupConsumer
                await self.consumer.close(code=SocketErrors.FORBIDDEN.value)
            await self.send_error(
                code=SocketErrors.FORBIDDEN.value, details=SocketErrors.FORBIDDEN.name
            )
        except EntityDoesNotExistException:
            logger.info(f'Не найдено')
            if self.consumer.is_group_consumer:
                # Закрываем соединение, если это GroupConsumer
                await self.consumer.close(code=SocketErrors.NOT_FOUND.value)
            await self.send_error(
                code=SocketErrors.NOT_FOUND.value, details=SocketErrors.NOT_FOUND.name
            )
        except Exception as e:
            logger.error(e)
            if self.consumer.is_group_consumer:
                # Закрываем соединение, если это GroupConsumer
                await self.consumer.close(code=SocketErrors.BAD_REQUEST.value)
            raise WebSocketError(code=SocketErrors.CUSTOM_DETAILED_ERROR.value, details=str(e))

    async def send_last_msg_updated_to_one_connection(
            self, socket_id, room_id, unread_cnt, first_unread, last_msg, chats_unread_messages_count, blocked_at, state
    ):
        await self.consumer.channel_layer.send(socket_id, {
            'type': 'chat_last_msg_updated',
            'prepared_data': {
                'id': room_id,
                'unreadCount': unread_cnt,
                'state': state,
                'firstUnreadMessage': first_unread,
                'lastMessage': last_msg,
                'blockedAt': blocked_at
            },
            'indicators': {
                'chatsUnreadMessages': chats_unread_messages_count
            }
        })

    async def send_message_was_read(
            self, unread_cnt, room_id, first_unread, uuid, chats_unread_messages_count, blocked_at, state
    ):
        if unread_cnt is not None:
            await self.consumer.channel_layer.send(self.consumer.channel_name, {
                'type': 'chat_message_was_read',
                'chat': {
                    'id': room_id,
                    'unreadCount': unread_cnt,
                    'state': state,
                    'firstUnreadMessage': first_unread,
                    'blockedAt': datetime_to_timestamp(blocked_at) if blocked_at is not None else None

                },
                'message': {
                    'uuid': uuid,
                },
                'indicators': {
                    'chatsUnreadMessages': chats_unread_messages_count
                }
            })

    async def respond_to_msg_owner_when_read(
            self, owner, sockets, should_response, room_id, unread_cnt, last_msg, first_unread, chats_unread_count,
            blocked_at, state
    ):
        if owner and owner.id != self.consumer.user.id and should_response:
            # Если автор прочитаного сообщения не тот, кто его читает, и сообщение ранее не читали
            for socket_id in sockets:
                # Отправялем сообщение автору сообщения о том, что оно прочитано
                await self.consumer.channel_layer.send(socket_id, {
                    'type': 'chat_message_updated',
                    'chat_id': room_id,
                    'prepared_data': last_msg,
                })

                # Если прочитанное сообщение последнее в чате, то отправляем автору SERVER_CHAT_LAST_MSG_UPDATED
                if unread_cnt is not None:
                    await self.send_last_msg_updated_to_one_connection(
                        socket_id=socket_id,
                        room_id=room_id,
                        unread_cnt=unread_cnt,
                        first_unread=first_unread,
                        last_msg=last_msg,
                        chats_unread_messages_count=chats_unread_count,
                        blocked_at=datetime_to_timestamp(blocked_at) if blocked_at is not None else None,
                        state=state
                    )

    async def send_counters(self):
        notifications_repository = RoutingMapper.room_async_repository(
            self.consumer.version, AvailableRoom.NOTIFICATIONS.value
        )
        chats_repository = RoutingMapper.room_async_repository(
            self.consumer.version, AvailableRoom.CHATS.value
        )
        appeals_repository = RoutingMapper.room_async_repository(
            self.consumer.version, AvailableRoom.APPEALS.value
        )

        indicators_dict = {
            'newNotifications': await notifications_repository(me=self.consumer.user).get_unread_notifications_count(),
            'chatsUnreadMessages': await chats_repository(me=self.consumer.user).get_all_chats_unread_count()
        }
        if self.consumer.user.account_type == AccountType.SELF_EMPLOYED.value:
            indicators_dict['newConfirmedAppeals'] = await appeals_repository(
                me=self.consumer.user).get_new_confirmed_count()

        if self.consumer.user.account_type == AccountType.MANAGER.value:
            indicators_dict['newAppeals'] = await appeals_repository(
                me=self.consumer.user).get_new_appeals_count()

        await self.consumer.channel_layer.send(self.consumer.channel_name, {
            'type': 'counters_for_indicators',
            'prepared_data': indicators_dict,
        })

    async def manager_join_chat(self, content):
        room_id = content.get('chatId')
        group_name = f'{AvailableRoom.CHATS.value}{room_id}'
        _MANAGER_CONNECTED_TEXT = 'Менеджер присоединился к беседе'

        # Если смз
        if self.consumer.user and self.consumer.user.account_type == AccountType.SELF_EMPLOYED.value:
            await self.send_error(
                code=SocketErrors.FORBIDDEN.value, details=SocketErrors.FORBIDDEN.name
            )
            return

        try:
            self.repository_class = RoutingMapper.room_async_repository(
                self.consumer.version, AvailableRoom.CHATS.value
            )
            await self.repository_class(self.consumer.user).check_permission_for_action(room_id)

            # Обновляем состояние чата - текущий менеджер активный и отправляем инфо сообщение
            # Если уже активен другой, то ставим его, но не отправляем инфо сообщение
            chat_repository = RoutingMapper.room_async_repository(self.consumer.version, AvailableRoom.CHATS.value)

            should_send_info, active_managers_ids = await chat_repository(
                me=self.consumer.user
            ).set_me_as_active_manager(chat_id=room_id)

            if should_send_info:
                # Отправляем событие о смене состояния чата всем релевантным менеджерам
                await self.send_chat_state_to_managers(
                    chat_id=room_id,
                    state=ChatManagerState.MANAGER_CONNECTED.value,
                    active_managers_ids=active_managers_ids
                )

                message_repository = RoutingMapper.room_async_repository(
                    self.consumer.version, AvailableRoom.MESSAGES.value
                )
                bot_message_serialized = await message_repository(chat_id=room_id).save_bot_message(
                    {
                        'message_type': ChatMessageType.INFO.value,
                        'text': _MANAGER_CONNECTED_TEXT,
                        'icon_type': ChatMessageIconType.SUPPORT.value
                    }
                )

                # Отправляем сообщение в чат с персонализацией данных для всех участников
                await self.send_chat_message(
                    room_id=room_id,
                    group_name=group_name,
                    prepared_message=bot_message_serialized
                )
            else:
                await self.send_chat_state_to_managers(
                    chat_id=room_id,
                    state=ChatManagerState.MANAGER_CONNECTED.value,
                    active_managers_ids=active_managers_ids
                )

        except ForbiddenException:
            logger.info(f'Действие запрещено')
            if self.consumer.is_group_consumer:
                # Закрываем соединение, если это GroupConsumer
                await self.consumer.close(code=SocketErrors.FORBIDDEN.value)
            await self.send_error(
                code=SocketErrors.FORBIDDEN.value, details=SocketErrors.FORBIDDEN.name
            )
        except EntityDoesNotExistException:
            logger.info(f'Не найдено')
            if self.consumer.is_group_consumer:
                # Закрываем соединение, если это GroupConsumer
                await self.consumer.close(code=SocketErrors.NOT_FOUND.value)
            await self.send_error(
                code=SocketErrors.NOT_FOUND.value, details=SocketErrors.NOT_FOUND.name
            )
        except Exception as e:
            logger.error(e)
            if self.consumer.is_group_consumer:
                # Закрываем соединение, если это GroupConsumer
                await self.consumer.close(code=SocketErrors.BAD_REQUEST.value)
            raise WebSocketError(code=SocketErrors.CUSTOM_DETAILED_ERROR.value, details=str(e))

    async def manager_leave_chat(self, content):
        room_id = content.get('chatId')
        group_name = f'{AvailableRoom.CHATS.value}{room_id}'

        _MANAGER_DISCONNECTED_TEXT = 'Менеджер завершил консультацию'

        # Если смз
        if self.consumer.user and self.consumer.user.account_type == AccountType.SELF_EMPLOYED.value:
            await self.send_error(
                code=SocketErrors.FORBIDDEN.value, details=SocketErrors.FORBIDDEN.name
            )
            return

        try:
            self.repository_class = RoutingMapper.room_async_repository(
                self.consumer.version, AvailableRoom.CHATS.value
            )
            await self.repository_class(self.consumer.user).check_permission_for_action(room_id)

            # Обновляем состояние чата - убираем менеджера и отправляем инфо сообщение
            chat_repository = RoutingMapper.room_async_repository(self.consumer.version, AvailableRoom.CHATS.value)
            should_send_info, active_managers_ids, state = await chat_repository(
                me=self.consumer.user).remove_active_manager(
                chat_id=room_id
            )

            if should_send_info:
                # Отправить сообщение о том, что консультация завершена
                message_repository = RoutingMapper.room_async_repository(
                    self.consumer.version, AvailableRoom.MESSAGES.value
                )
                bot_message_serialized = await message_repository(chat_id=room_id).save_bot_message(
                    {
                        'message_type': ChatMessageType.INFO.value,
                        'text': _MANAGER_DISCONNECTED_TEXT,
                        'icon_type': ChatMessageIconType.SUPPORT.value
                    }
                )

                # Отправляем сообщение в чат с персонализацией данных для всех участников
                await self.send_chat_message(
                    room_id=room_id,
                    group_name=group_name,
                    prepared_message=bot_message_serialized
                )

                # Отправляем событие о смене состояния чата всем релевантным менеджерам
                await self.send_chat_state_to_managers(
                    chat_id=room_id,
                    state=state
                )
            else:
                # Отправляем событие о смене активных менеджеров всем релевантным менеджерам
                await self.send_chat_state_to_managers(
                    chat_id=room_id,
                    state=state,
                    active_managers_ids=active_managers_ids
                )

        except ForbiddenException:
            logger.info(f'Действие запрещено')
            if self.consumer.is_group_consumer:
                # Закрываем соединение, если это GroupConsumer
                await self.consumer.close(code=SocketErrors.FORBIDDEN.value)
            await self.send_error(
                code=SocketErrors.FORBIDDEN.value, details=SocketErrors.FORBIDDEN.name
            )

        except EntityDoesNotExistException:
            logger.info(f'Не найдено')
            if self.consumer.is_group_consumer:
                # Закрываем соединение, если это GroupConsumer
                await self.consumer.close(code=SocketErrors.NOT_FOUND.value)
            await self.send_error(
                code=SocketErrors.NOT_FOUND.value, details=SocketErrors.NOT_FOUND.name
            )
        except Exception as e:
            logger.error(e)
            if self.consumer.is_group_consumer:
                # Закрываем соединение, если это GroupConsumer
                await self.consumer.close(code=SocketErrors.BAD_REQUEST.value)
            raise WebSocketError(code=SocketErrors.CUSTOM_DETAILED_ERROR.value, details=str(e))

    async def select_bot_intent(self, content):
        room_id = content.get('chatId')

        try:
            self.repository_class = RoutingMapper.room_async_repository(
                self.consumer.version, AvailableRoom.CHATS.value
            )
            await self.repository_class(self.consumer.user).check_permission_for_action(room_id)

            await self.consumer.channel_layer.send(self.consumer.channel_name, {
                'type': 'chat_bot_intent_accepted',
                'chat': {
                    'id': room_id
                },
                'intent': content.get('intent')
            })

            # Ответ бота через Celery с задержкой
            delayed_select_bot_intent.s(
                version=self.consumer.version,
                chat_id=room_id,
                user_id=self.consumer.user.id,
                intent_code=content.get('intent')
            ).apply_async(countdown=2)  # Отвечаем через 2 сек

        except ForbiddenException:
            logger.info(f'Действие запрещено')
            if self.consumer.is_group_consumer:
                # Закрываем соединение, если это GroupConsumer
                await self.consumer.close(code=SocketErrors.FORBIDDEN.value)
            await self.send_error(
                code=SocketErrors.FORBIDDEN.value, details=SocketErrors.FORBIDDEN.name
            )

        except EntityDoesNotExistException:
            logger.info(f'Не найдено')
            if self.consumer.is_group_consumer:
                # Закрываем соединение, если это GroupConsumer
                await self.consumer.close(code=SocketErrors.NOT_FOUND.value)
            await self.send_error(
                code=SocketErrors.NOT_FOUND.value, details=SocketErrors.NOT_FOUND.name
            )

        except Exception as e:
            logger.error(e)
            if self.consumer.is_group_consumer:
                # Закрываем соединение, если это GroupConsumer
                await self.consumer.close(code=SocketErrors.BAD_REQUEST.value)
            raise WebSocketError(code=SocketErrors.CUSTOM_DETAILED_ERROR.value, details=str(e))
