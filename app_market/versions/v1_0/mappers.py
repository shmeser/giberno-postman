from dateutil.utils import time

from app_market.enums import ShiftWorkTime
from backend.entity import Error
from backend.errors.enums import ErrorsCodes
from backend.errors.http_exception import CustomException
from backend.utils import chained_get, CP


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


class ReviewsValidator:
    @staticmethod
    def text_and_value(body):
        text = chained_get(body, 'text')
        value = chained_get(body, 'value')

        if not text or not value:
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.VALIDATION_ERROR))
            ])

        try:
            return text, float(value)
        except Exception as e:
            CP(bg='red').bold(e)
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.VALIDATION_ERROR))
            ])
