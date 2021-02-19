import base64


class Base64EncodedStringGenerator:
    def __init__(self, user_shift_model_instance):
        self.user = user_shift_model_instance.user
        self.shift = user_shift_model_instance.shift

    def encode(self):
        string = f"""{self.user} : {self.user.id}, {self.shift} : {self.shift.id}"""
        string_to_bytes = string.encode()
        return base64.b64encode(string_to_bytes, altchars=None)
