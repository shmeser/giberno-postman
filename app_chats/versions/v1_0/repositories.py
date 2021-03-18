from app_chats.models import Chat, Message
from backend.mixins import MasterRepository


class ChatsRepository(MasterRepository):
    model = Chat


class MessagesRepository(MasterRepository):
    model = Message
