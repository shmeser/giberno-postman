from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from app_market.models import UserShift
from app_market.utils import QRHandler


@shared_task
def set_qr_code_to_user_shifts():
    real_time_start = timezone.now() + timedelta(minutes=30)
    queryset = UserShift.objects.filter(real_time_start=real_time_start)
    for item in queryset:
        qr_code = QRHandler(user_shift_model_instance=item)
        item.qr_code = qr_code.to_bas64()
        item.save()
        qr_code.remove()
