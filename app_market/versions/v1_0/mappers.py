from app_market.enums import ShiftWorkTime
from dateutil.utils import time


class ShiftMapper:
    def work_time_to_time_range(self, work_time):
        if work_time == ShiftWorkTime.MORNING:
            return time(5, 0), time(11, 59, 59)

        if work_time == ShiftWorkTime.DAY:
            return time(12, 0), time(17, 59, 59)

        if work_time == ShiftWorkTime.EVENING:
            return time(18, 0), time(23, 59, 59)

        return None, None
