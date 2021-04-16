from djangorestframework_camel_case.util import camelize
from rest_framework import status
from rest_framework.response import Response

from app_bot.tasks import delayed_checking_for_bot_reply
from app_chats.versions.v1_0.repositories import ChatsRepository, MessagesRepository
from app_chats.versions.v1_0.serializers import ChatsSerializer, MessagesSerializer, ChatSerializer, \
    FirstUnreadMessageSerializer
from app_sockets.controllers import SocketController
from app_sockets.enums import AvailableVersion, AvailableRoom
from backend.errors.enums import RESTErrors
from backend.errors.http_exceptions import HttpException
from backend.mappers import RequestMapper
from backend.mixins import CRUDAPIView
from backend.utils import get_request_headers, get_request_body, chained_get


class Chats(CRUDAPIView):
    serializer_class = ChatsSerializer
    repository_class = ChatsRepository
    allowed_http_methods = ['get']

    filter_params = {
        'shop': 'shop_id',
        'vacancy': 'vacancy_id',
        'user': 'user_id',
        'created_at': 'created_at'
    }

    bool_filter_params = {
    }

    date_filter_params = {
        'created_at': 'last_message_created_at',
    }

    array_filter_params = {
    }

    default_order_params = [
        '-id'
    ]

    default_filters = {}

    order_params = {
        'created_at': 'last_message_created_at',  # перекидываем на дату последнего сообщения
    }

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        if record_id:
            self.serializer_class = ChatSerializer
            dataset = self.repository_class(request.user).get_by_id(record_id)
        else:
            self.many = True
            dataset = self.repository_class(request.user).get_chats_or_create(
                kwargs=filters, order_by=order_params, paginator=pagination
            )

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class Messages(CRUDAPIView):
    serializer_class = MessagesSerializer
    repository_class = MessagesRepository
    allowed_http_methods = ['get', 'post']

    filter_params = {
        'search': 'text__istartswith',
    }

    bool_filter_params = {
    }

    array_filter_params = {
    }

    date_filter_params = {
        'created_at': 'created_at',
    }

    default_order_params = [
        '-created_at'
    ]

    default_filters = {}

    order_params = {
        'created_at': 'created_at',
    }

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        self.many = True
        dataset = self.repository_class(request.user, chat_id=record_id).filter_by_kwargs(
            kwargs=filters, order_by=order_params, paginator=pagination
        )

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)

    def post(self, request, **kwargs):
        chat_id = kwargs.get(self.urlpattern_record_id_name)
        body = get_request_body(request)

        self.many = False

        if not ChatsRepository(request.user).check_permission_for_action(chat_id):
            # Если нет доступа к чату
            raise HttpException(status_code=RESTErrors.FORBIDDEN.value, detail=RESTErrors.FORBIDDEN.name)

        dataset = self.repository_class(me=request.user, chat_id=chat_id).save_client_message(
            content=body
        )

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        processed_serialized_message = camelize(serialized.data)

        SocketController(
            me=request.user,
            version=AvailableVersion.V1_0.value,
            room_name=AvailableRoom.CHATS.value,
        ).send_chat_message(
            prepared_message=processed_serialized_message,
            chat_id=chat_id
        )

        # Ответ бота через Celery с задержкой
        delayed_checking_for_bot_reply.s(
            version=AvailableVersion.V1_0.value,
            chat_id=chat_id,
            user_id=request.user.id,
            message_text=chained_get(processed_serialized_message, 'text')
        ).apply_async(countdown=2)  # Отвечаем через 2 сек

        return Response(processed_serialized_message, status=status.HTTP_200_OK)


class ReadMessages(CRUDAPIView):
    serializer_class = MessagesSerializer
    repository_class = MessagesRepository
    allowed_http_methods = ['post']

    def post(self, request, **kwargs):
        chat_id = kwargs.get(self.urlpattern_record_id_name)
        body = get_request_body(request)

        self.many = False

        if not ChatsRepository(request.user).check_permission_for_action(chat_id):
            # Если нет доступа к чату
            raise HttpException(status_code=RESTErrors.FORBIDDEN.value, detail=RESTErrors.FORBIDDEN.name)

        last_msg = self.repository_class(chat_id=chat_id).get_last_message()
        (
            message,
            msg_owner,
            msg_owner_sockets,
            should_response_owner
        ) = self.repository_class(request.user, chat_id=chat_id).read_message(  # 8
            content=body,
            prefetch=True
        )

        if not message:
            raise HttpException(status_code=RESTErrors.NOT_FOUND.value, detail=RESTErrors.NOT_FOUND.name)

        # Количество непрочитанных сообщений в чате для себя
        my_unread_count, my_first_unread_message = ChatsRepository(
            me=request.user
        ).get_chat_unread_count_and_first_unread(chat_id)  # 2

        serialized_message = camelize(MessagesSerializer(message, many=False).data)
        serialized_first_unread_message = camelize(
            FirstUnreadMessageSerializer(my_first_unread_message, many=False).data)

        owner_unread_count = None
        if last_msg.id == message.id and should_response_owner:
            # Если последнее сообщение в чате и не было прочитано ранее, то запрашиваем число непрочитанных для чата
            # Т.к. отправляем данные о прочитанном сообщении в событии SERVER_CHAT_LAST_MSG_UPDATED, то нужны данные
            # по unread_count
            owner_unread_count, *_ = ChatsRepository(me=msg_owner).get_chat_unread_count_and_first_unread(chat_id)  # 2

        if my_unread_count is not None:
            SocketController(me=request.user, version=AvailableVersion.V1_0.value).send_message_to_my_connections({
                'type': 'chat_message_was_read',
                'chat': {
                    'id': chat_id,
                    'unreadCount': my_unread_count,
                    'firstUnreadMessage': serialized_first_unread_message,
                },
                'message': {
                    'uuid': chained_get(body, 'uuid'),
                }
            })

        if msg_owner and msg_owner.id != request.user.id and should_response_owner:
            # Если автор прочитаного сообщения не тот, кто его читает, и сообщение ранее не читали
            for socket_id in msg_owner_sockets:
                # Отправялем сообщение автору сообщения о том, что оно прочитано
                SocketController(version=AvailableVersion.V1_0.value).send_message_to_one_connection(socket_id, {
                    'type': 'chat_message_updated',
                    'chat_id': chat_id,
                    'prepared_data': serialized_message,
                })

                # Если прочитанное сообщение последнее в чате, то отправляем автору SERVER_CHAT_LAST_MSG_UPDATED
                if owner_unread_count is not None:
                    SocketController(version=AvailableVersion.V1_0.value).send_message_to_one_connection(socket_id, {
                        'type': 'chat_last_msg_updated',
                        'prepared_data': {
                            'id': chat_id,
                            'unreadCount': owner_unread_count,
                            'lastMessage': serialized_message
                        },
                    })

        return Response(serialized_message, status=status.HTTP_200_OK)
