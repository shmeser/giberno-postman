import base64
import os

import segno


class QRHandler:
    def __init__(self, user_shift_model_instance):
        user = user_shift_model_instance.user
        shift = user_shift_model_instance.shift
        self.info_to_encode = f"""{user} : {user.id}, {shift} : {shift.id}"""
        self.qr_image_name = 'qr.png'
        self.qr = segno.make(self.info_to_encode)
        self.qr.save(self.qr_image_name)

    # def to_qr(self):
    #     qr = segno.make(self.info_to_encode)
    #     qr.save(self.qr_image_name)

    def to_bas64(self):
        return base64.b64encode(open(self.qr_image_name, "rb").read())

    def remove(self):
        os.remove(self.qr_image_name)
