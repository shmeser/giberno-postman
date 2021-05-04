from datetime import datetime, timedelta


class QRHandler:
    def __init__(self, user_shift_model_instance):
        self.user = user_shift_model_instance.user
        self.shift = user_shift_model_instance.shift

    def create_qr_data(self):
        return {
            'user': self.user.id,
            'shift': self.shift.id
        }


def handle_date_for_appeals(shift_active_date, time_object, utc_offset):
    utc_offset = utc_offset / 3600
    year = shift_active_date.year
    month = str(shift_active_date.month)
    if len(month) == 1:
        month = '0' + month
    day = str(shift_active_date.day)
    if len(day) == 1:
        day = '0' + day

    date = datetime.fromisoformat(f'{year}-{month}-{day} {time_object}')
    date += timedelta(hours=utc_offset)
    return date
