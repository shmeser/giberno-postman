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
        item.qr_code = QRHandler(item).create_qr_data()
        item.save()
