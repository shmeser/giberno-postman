class SocketEventRM:
    def __init__(self, data):
        self.token = data.get('token', None)
        self.group_name = data.get('groupName', None)
        self.event_type = data.get('eventType', None)
        self.profile_id = data.get('profileId', None)
        self.lat = data.get('lat', None)
        self.lon = data.get('lon', None)
        self.uuid = data.get('uuid', None)
        self.id = data.get('id', None)
        self.receiver = data.get('receiver', None)

        self.chat_id = data.get('chatId', None)
        self.message = data.get('message', None)
