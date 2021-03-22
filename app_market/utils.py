class QRHandler:
    def __init__(self, user_shift_model_instance):
        self.user = user_shift_model_instance.user
        self.shift = user_shift_model_instance.shift

    def create_qr_data(self):
        return {
            'user': self.user.id,
            'shift': self.shift.id
        }
