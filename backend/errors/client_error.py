class SocketError(Exception):
    """
    Custom exception class that is caught by the websocket receive()
    handler and translated into a send back to the client.
    """

    def __init__(self, code, message):
        super().__init__(code, message)
        self.code = code
        self.message = message
