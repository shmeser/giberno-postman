class WebSocketError(Exception):
    """
    Custom exception class that is caught by the websocket receive()
    handler and translated into a send back to the client.
    """
    def __init__(self, code, details):
        super().__init__(code, details)
        self.code = code
        self.details = details
