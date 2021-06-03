from celery import shared_task

from app_market.versions.v1_0.repositories import ShiftAppealsRepository


@shared_task
def update_appeals():
    ShiftAppealsRepository().bulk_cancel()
    ShiftAppealsRepository().bulk_cancel_with_job_soon_status()
    ShiftAppealsRepository().bulk_set_job_soon_status()
    ShiftAppealsRepository().bulk_set_waiting_for_completion_status()
    ShiftAppealsRepository().bulk_set_completed_status()
