from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from app_market.enums import ShiftAppealStatus, JobStatus
from app_market.models import ShiftAppeal
from app_market.utils import QRHandler


@shared_task
def cancel_overdue_appeals():
    queryset = ShiftAppeal.objects.filter(status=ShiftAppealStatus.INITIAL.value, time_start__lte=timezone.now())
    queryset.update(status=ShiftAppealStatus.CANCELED.value)


@shared_task
def notify_self_employed_users_about_soon_job():
    upcoming_appeals = ShiftAppeal.objects.filter(
        status=ShiftAppealStatus.CONFIRMED,
        job_status__isnull=True
    )

    soon = timezone.now() + timedelta(minutes=30)

    with transaction.atomic():
        for appeal in upcoming_appeals:
            if timezone.now() < appeal.time_start < soon:
                appeal.job_status = JobStatus.JOB_SOON.value
                qr_text = QRHandler(appeal=appeal).create_qr_data()
                appeal.save()
                # уведомление - работа скоро

    # TODO прикрутить логику по остальным статусам


@shared_task
def complete_appeals_by_end_time():
    appeals_to_complete = ShiftAppeal.objects.filter(
        status=ShiftAppealStatus.CONFIRMED,
        job_status__isnull=False
    ).exclude(job_status=JobStatus.COMPLETED.value)

    with transaction.atomic():
        for appeal in appeals_to_complete:
            if appeal.time_start > timezone.now():
                appeal.job_status = JobStatus.COMPLETED.value
                appeal.status = ShiftAppealStatus.COMPLETED.value
                appeal.time_completed = timezone.now()
                appeal.save()
                # Тут непонятно, нужно уведомление о том, что смена завершена или нет?!

# TODO нужна еще одна таска по установке статуса - скоро завершится и удалить метод который shift/check + еще метод для менеджера для завершения смены
