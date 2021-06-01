from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from app_market.enums import ShiftAppealStatus, JobStatus
from app_market.models import ShiftAppeal


@shared_task
def cancel_overdue_appeals():
    queryset = ShiftAppeal.objects.filter(status=ShiftAppealStatus.INITIAL.value, time_start__lte=timezone.now())
    queryset.update(status=ShiftAppealStatus.CANCELED.value)


@shared_task
def notify_user_about_job_status():
    confirmed_appeals = ShiftAppeal.objects.filter(status=ShiftAppealStatus.CONFIRMED)

    soon = timezone.now() + timedelta(minutes=30)

    with transaction.atomic():
        for appeal in confirmed_appeals.filter(job_status__isnull=True):
            if timezone.now() < appeal.time_start < soon:
                appeal.job_status = JobStatus.JOB_SOON.value
                appeal.save()
                # уведомление - работа скоро

    # TODO прикрутить логику по остальным статусам
