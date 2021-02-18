from app_market.enums import ShiftWorkTime
from dateutil.utils import time


class ShiftMapper:
    @staticmethod
    def work_time_to_time_range(work_time):
        if work_time == ShiftWorkTime.MORNING:
            return time(5, 0, 0), time(12, 0, 0)

        if work_time == ShiftWorkTime.DAY:
            return time(12, 0, 0), time(18, 0, 0)

        if work_time == ShiftWorkTime.EVENING:
            return time(18, 0, 0), time(23, 59, 59, 999999), time(0, 0, 0)  # Окончание суток 23.59.59 и сама полночь

        return None, None
